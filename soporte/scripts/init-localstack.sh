#!/bin/bash
#
# Script para inicializar LocalStack con los recursos necesarios
# Crea bucket S3 y cola SQS para carga masiva
#

echo "🚀 Inicializando LocalStack..."

# Esperar a que LocalStack esté listo
echo "⏳ Esperando LocalStack..."
sleep 5

# Configurar AWS CLI para LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Bucket S3
BUCKET_NAME="medisupply-bulk-uploads"
echo "📦 Creando bucket S3: $BUCKET_NAME"
aws --endpoint-url=$AWS_ENDPOINT_URL s3 mb s3://$BUCKET_NAME 2>/dev/null || echo "   Bucket ya existe"

# Cola SQS
QUEUE_NAME="medisupply-bulk-upload-queue"
echo "📬 Creando cola SQS: $QUEUE_NAME"
aws --endpoint-url=$AWS_ENDPOINT_URL sqs create-queue \
  --queue-name $QUEUE_NAME \
  --attributes VisibilityTimeout=300,MessageRetentionPeriod=86400 \
  2>/dev/null || echo "   Cola ya existe"

# Obtener URL de la cola
QUEUE_URL=$(aws --endpoint-url=$AWS_ENDPOINT_URL sqs get-queue-url --queue-name $QUEUE_NAME --query 'QueueUrl' --output text 2>/dev/null)

echo ""
echo "✅ LocalStack inicializado correctamente"
echo ""
echo "📊 Recursos creados:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   SQS Queue: $QUEUE_NAME"
echo "   Queue URL: $QUEUE_URL"
echo ""
echo "💡 Verificar recursos:"
echo "   aws --endpoint-url=$AWS_ENDPOINT_URL s3 ls"
echo "   aws --endpoint-url=$AWS_ENDPOINT_URL sqs list-queues"
echo ""

