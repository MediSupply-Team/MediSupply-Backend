param(
  [string]$Region = "us-east-1",
  [string]$EcrRepo = "medisupply-dev-bff-cliente",
  [string]$Cluster = "orders-cluster",
  [string]$Service = "medisupply-dev-bff-cliente-svc",
  [string]$ImageTag = "",
  [int]$WaitTimeout = 600,  # ⬅️ Timeout en segundos (10 min)
  [switch]$SkipWait         # ⬅️ Flag para saltar la espera
)

function Info($m){ Write-Host "[INFO]  $m" -ForegroundColor Yellow }
function Ok($m){ Write-Host "[OK]    $m" -ForegroundColor Green }
function Err($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }
function Warn($m){ Write-Host "[WARN]  $m" -ForegroundColor Magenta }

Info "Verificando prerequisitos..."
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { Err "AWS CLI no está instalado"; exit 1 }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Err "Docker no está instalado"; exit 1 }
try { aws sts get-caller-identity | Out-Null } catch { Err "Sin credenciales AWS"; exit 1 }
Ok "Prerrequisitos OK"

if (-not $ImageTag -or $ImageTag -eq "") {
  try {
    $sha = (git rev-parse --short HEAD).Trim()
    if ($LASTEXITCODE -eq 0 -and $sha) { $ImageTag = $sha } else { $ImageTag = "latest" }
  } catch { $ImageTag = "latest" }
}
Info "Tag de la imagen: $ImageTag"

$AccountId = (aws sts get-caller-identity --query Account --output text)
$Registry  = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$ImageUri  = "${Registry}/${EcrRepo}:${ImageTag}"
$ImageUriLatest = "${Registry}/${EcrRepo}:latest"

Info "Login ECR..."
$pw = aws ecr get-login-password --region $Region
docker login $Registry -u AWS -p $pw
if ($LASTEXITCODE -ne 0) { Err "Falló login ECR"; exit 1 } else { Ok "Login ECR OK" }

Info "Construyendo imagen (bff-cliente/Dockerfile)..."
Push-Location bff-cliente
docker build -t "${EcrRepo}:${ImageTag}" .
if ($LASTEXITCODE -ne 0) { Pop-Location; Err "Build falló"; exit 1 }
Pop-Location

Info "Taggeando & pusheando a ECR..."
docker tag "${EcrRepo}:${ImageTag}" "$ImageUri"
docker tag "${EcrRepo}:${ImageTag}" "$ImageUriLatest"
docker push "$ImageUri"       | Out-Null
docker push "$ImageUriLatest" | Out-Null
Ok "Imagen subida: $ImageUri y :latest"

Info "Forzando nuevo despliegue ECS..."
aws ecs update-service --cluster $Cluster --service $Service --force-new-deployment --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) { Err "update-service falló"; exit 1 } else { Ok "Despliegue iniciado" }

# ============================================================
# MONITOREO INTELIGENTE CON TIMEOUT
# ============================================================

if ($SkipWait) {
  Warn "Saltando espera de estabilidad (-SkipWait activado)"
  Info "Ver progreso manualmente:"
  Write-Host "  aws ecs describe-services --cluster $Cluster --services $Service --region $Region" -ForegroundColor Cyan
} else {
  Info "Esperando estabilidad del servicio (timeout: ${WaitTimeout}s)..."
  
  $elapsed = 0
  $interval = 10
  $stable = $false
  
  while ($elapsed -lt $WaitTimeout) {
    # Obtener estado actual
    $svcJson = aws ecs describe-services --cluster $Cluster --services $Service --region $Region --output json | ConvertFrom-Json
    $svc = $svcJson.services[0]
    
    $desired = $svc.desiredCount
    $running = $svc.runningCount
    $pending = $svc.pendingCount
    $status = $svc.status
    
    # Mostrar progreso
    $bar = "=" * [Math]::Min(50, [int](($elapsed / $WaitTimeout) * 50))
    Write-Host "`r[$bar$(' ' * (50 - $bar.Length))] ${elapsed}s | Running: $running/$desired | Pending: $pending" -NoNewline
    
    # Verificar estabilidad
    if ($running -eq $desired -and $pending -eq 0 -and $status -eq "ACTIVE") {
      # Dar 20s extra para que los health checks se estabilicen
      Start-Sleep -Seconds 20
      
      $svcJson2 = aws ecs describe-services --cluster $Cluster --services $Service --region $Region --output json | ConvertFrom-Json
      $svc2 = $svcJson2.services[0]
      
      if ($svc2.runningCount -eq $svc2.desiredCount -and $svc2.pendingCount -eq 0) {
        $stable = $true
        break
      }
    }
    
    # Verificar eventos de error
    $recentEvents = $svc.events | Select-Object -First 3
    foreach ($event in $recentEvents) {
      if ($event.message -match "unhealthy|failed|stopped") {
        Write-Host ""
        Warn "Evento reciente: $($event.message)"
      }
    }
    
    Start-Sleep -Seconds $interval
    $elapsed += $interval
  }
  
  Write-Host ""  # Nueva línea después del progreso
  
  if ($stable) {
    Ok "Servicio estable"
  } else {
    Warn "Timeout alcanzado (${WaitTimeout}s). El servicio aún se está desplegando."
    Info "Revisa el estado manualmente o aumenta el timeout."
  }
}

# ============================================================
# ESTADO FINAL Y DIAGNÓSTICO
# ============================================================

Info "Estado final del servicio:"
aws ecs describe-services --cluster $Cluster --services $Service --region $Region `
  --query "services[0].{status:status,desired:desiredCount,running:runningCount,pending:pendingCount,td:taskDefinition}" `
  --output table

Info "Últimos 3 eventos:"
aws ecs describe-services --cluster $Cluster --services $Service --region $Region `
  --query "services[0].events[:3].{time:createdAt,message:message}" `
  --output table

# Mostrar comandos útiles
Write-Host ""
Info "Comandos útiles:"
Write-Host "  # Ver logs en tiempo real:" -ForegroundColor Cyan
Write-Host "  aws logs tail /ecs/$Service --follow --region $Region" -ForegroundColor White
Write-Host ""
Write-Host "  # Ver health checks del target group:" -ForegroundColor Cyan
Write-Host "  aws elbv2 describe-target-health --target-group-arn <ARN>" -ForegroundColor White
Write-Host ""
Write-Host "  # Rollback si algo falla:" -ForegroundColor Cyan
Write-Host "  aws ecs update-service --cluster $Cluster --service $Service --task-definition <TASK_DEF_ANTERIOR> --force-new-deployment --region $Region" -ForegroundColor White

# Health check del ALB (si es accesible públicamente)
$albDns = "medisupply-dev-bff-cliente-alb-1141787956.us-east-1.elb.amazonaws.com"
Write-Host ""
Info "Probando health check del ALB..."
try {
  $response = Invoke-WebRequest -Uri "http://$albDns/health" -TimeoutSec 5 -UseBasicParsing
  if ($response.StatusCode -eq 200) {
    Ok "Health check OK: $($response.Content)"
  }
} catch {
  Warn "No se pudo alcanzar el health check (puede estar todavía desplegándose)"
}