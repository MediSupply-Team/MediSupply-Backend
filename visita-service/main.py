from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlmodel import Session, select
from database import get_session, init_db
from models import Visita, Hallazgo, EstadoVisita
from datetime import datetime
from typing import List, Optional
import storage

app = FastAPI(title="Visita Service", version="2.0.0")

# El almacenamiento se configura automáticamente en storage.py

@app.on_event("startup")
def on_startup():
    """Inicializa la base de datos al arrancar"""
    init_db()

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"ok": True, "service": "visita-service"}

# ============================================================
# ENDPOINTS DE VISITAS
# ============================================================

@app.post("/api/visitas", response_model=dict)
async def crear_visita(
    vendedor_id: int = Form(...),
    cliente_id: int = Form(...),
    nombre_contacto: str = Form(...),
    observaciones: Optional[str] = Form(None),
    estado: EstadoVisita = Form(EstadoVisita.PENDIENTE),
    fotos: Optional[List[UploadFile]] = File(None),
    videos: Optional[List[UploadFile]] = File(None),
    session: Session = Depends(get_session)
):
    """
    Crear una nueva visita a un cliente con fotos, videos y observaciones.
    
    - **vendedor_id**: ID del vendedor que realiza la visita
    - **cliente_id**: ID del cliente visitado
    - **nombre_contacto**: Nombre de la persona de contacto
    - **observaciones**: Texto con observaciones generales de la visita
    - **estado**: Estado de la visita (exitosa, pendiente, cancelada)
    - **fotos**: Lista de archivos de fotos (jpg, jpeg, png, gif)
    - **videos**: Lista de archivos de videos (mp4, avi, mov)
    """
    # 1. Crear la visita
    visita = Visita(
        vendedor_id=vendedor_id,
        cliente_id=cliente_id,
        nombre_contacto=nombre_contacto,
        observaciones=observaciones,
        estado=estado
    )
    session.add(visita)
    session.commit()
    session.refresh(visita)
    
    hallazgos_creados = []
    
    # 2. Procesar fotos si existen
    if fotos:
        for foto in fotos:
            if foto.filename:  # Verificar que no sea archivo vacío
                extension = foto.filename.split(".")[-1].lower()
                if extension not in ["jpg", "jpeg", "png", "gif"]:
                    # Eliminar la visita creada si hay error
                    session.delete(visita)
                    session.commit()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Formato de foto no válido: {foto.filename}. Permitidos: jpg, jpeg, png, gif"
                    )
                
                # Guardar archivo usando módulo storage
                filename = f"visita_{visita.id}_{datetime.utcnow().timestamp()}.{extension}"
                file_content = await foto.read()
                file_path = await storage.save_file(file_content, filename)
                
                # Crear hallazgo
                hallazgo = Hallazgo(
                    visita_id=visita.id,
                    tipo="foto",
                    contenido=file_path,
                    descripcion=f"Foto: {foto.filename}"
                )
                session.add(hallazgo)
                hallazgos_creados.append(hallazgo)
    
    # 3. Procesar videos si existen
    if videos:
        for video in videos:
            if video.filename:  # Verificar que no sea archivo vacío
                extension = video.filename.split(".")[-1].lower()
                if extension not in ["mp4", "avi", "mov"]:
                    # Eliminar visita y archivos subidos si hay error
                    for h in hallazgos_creados:
                        await storage.delete_file(h.contenido)
                    session.delete(visita)
                    session.commit()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Formato de video no válido: {video.filename}. Permitidos: mp4, avi, mov"
                    )
                
                # Guardar archivo usando módulo storage
                filename = f"visita_{visita.id}_{datetime.utcnow().timestamp()}.{extension}"
                file_content = await video.read()
                file_path = await storage.save_file(file_content, filename)
                
                # Crear hallazgo
                hallazgo = Hallazgo(
                    visita_id=visita.id,
                    tipo="video",
                    contenido=file_path,
                    descripcion=f"Video: {video.filename}"
                )
                session.add(hallazgo)
                hallazgos_creados.append(hallazgo)
    
    # 4. Guardar todos los hallazgos
    session.commit()
    
    # 5. Preparar respuesta
    hallazgos_response = [
        {
            "id": h.id,
            "tipo": h.tipo,
            "descripcion": h.descripcion,
            "url_descarga": f"/api/hallazgos/{h.id}/archivo"
        }
        for h in hallazgos_creados
    ]
    
    return {
        "id": visita.id,
        "vendedor_id": visita.vendedor_id,
        "cliente_id": visita.cliente_id,
        "nombre_contacto": visita.nombre_contacto,
        "observaciones": visita.observaciones,
        "estado": visita.estado,
        "fecha_visita": visita.fecha_visita.isoformat(),
        "created_at": visita.created_at.isoformat(),
        "hallazgos": hallazgos_response,
        "total_fotos": len([h for h in hallazgos_creados if h.tipo == "foto"]),
        "total_videos": len([h for h in hallazgos_creados if h.tipo == "video"])
    }

@app.get("/api/visitas", response_model=List[dict])
def listar_visitas(
    vendedor_id: Optional[int] = Query(None),
    cliente_id: Optional[int] = Query(None),
    estado: Optional[EstadoVisita] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Listar visitas con filtros opcionales.
    """
    query = select(Visita)
    
    if vendedor_id:
        query = query.where(Visita.vendedor_id == vendedor_id)
    if cliente_id:
        query = query.where(Visita.cliente_id == cliente_id)
    if estado:
        query = query.where(Visita.estado == estado)
    
    visitas = session.exec(query).all()
    
    return [
        {
            "id": v.id,
            "vendedor_id": v.vendedor_id,
            "cliente_id": v.cliente_id,
            "nombre_contacto": v.nombre_contacto,
            "observaciones": v.observaciones,
            "estado": v.estado,
            "fecha_visita": v.fecha_visita.isoformat(),
            "created_at": v.created_at.isoformat(),
            "cantidad_hallazgos": len(v.hallazgos) if v.hallazgos else 0
        }
        for v in visitas
    ]

@app.get("/api/visitas/{visita_id}", response_model=dict)
def obtener_visita(
    visita_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener detalle completo de una visita con sus hallazgos.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    hallazgos = [
        {
            "id": h.id,
            "tipo": h.tipo,
            "contenido": h.contenido,
            "descripcion": h.descripcion,
            "created_at": h.created_at.isoformat()
        }
        for h in visita.hallazgos
    ]
    
    return {
        "id": visita.id,
        "vendedor_id": visita.vendedor_id,
        "cliente_id": visita.cliente_id,
        "nombre_contacto": visita.nombre_contacto,
        "observaciones": visita.observaciones,
        "estado": visita.estado,
        "fecha_visita": visita.fecha_visita.isoformat(),
        "created_at": visita.created_at.isoformat(),
        "hallazgos": hallazgos
    }

@app.patch("/api/visitas/{visita_id}/estado")
def actualizar_estado_visita(
    visita_id: int,
    estado: EstadoVisita = Form(...),
    session: Session = Depends(get_session)
):
    """
    Actualizar el estado de una visita.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    visita.estado = estado
    visita.updated_at = datetime.utcnow()
    session.add(visita)
    session.commit()
    session.refresh(visita)
    
    return {
        "id": visita.id,
        "estado": visita.estado,
        "updated_at": visita.updated_at.isoformat()
    }

# ============================================================
# ENDPOINTS DE HALLAZGOS (FOTOS/VIDEOS/TEXTOS)
# ============================================================

@app.post("/api/visitas/{visita_id}/hallazgos/texto")
def agregar_hallazgo_texto(
    visita_id: int,
    contenido: str = Form(...),
    descripcion: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """
    Agregar un hallazgo de tipo texto a una visita.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    hallazgo = Hallazgo(
        visita_id=visita_id,
        tipo="texto",
        contenido=contenido,
        descripcion=descripcion
    )
    session.add(hallazgo)
    session.commit()
    session.refresh(hallazgo)
    
    return {
        "id": hallazgo.id,
        "visita_id": hallazgo.visita_id,
        "tipo": hallazgo.tipo,
        "contenido": hallazgo.contenido,
        "descripcion": hallazgo.descripcion,
        "created_at": hallazgo.created_at.isoformat()
    }

@app.post("/api/visitas/{visita_id}/hallazgos/archivo")
async def agregar_hallazgo_archivo(
    visita_id: int,
    archivo: UploadFile = File(...),
    tipo: str = Form(...),  # "foto" o "video"
    descripcion: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """
    Agregar un hallazgo de tipo foto o video a una visita.
    Soporta: jpg, jpeg, png, gif (fotos) y mp4, avi, mov (videos)
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    # Validar tipo
    if tipo not in ["foto", "video"]:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'foto' o 'video'")
    
    # Validar extensión
    extension = archivo.filename.split(".")[-1].lower()
    if tipo == "foto" and extension not in ["jpg", "jpeg", "png", "gif"]:
        raise HTTPException(status_code=400, detail="Formato de foto no válido")
    if tipo == "video" and extension not in ["mp4", "avi", "mov"]:
        raise HTTPException(status_code=400, detail="Formato de video no válido")
    
    # Guardar archivo
    filename = f"visita_{visita_id}_{datetime.utcnow().timestamp()}.{extension}"
    file_content = await archivo.read()
    file_path = await storage.save_file(file_content, filename)
    
    # Crear hallazgo
    hallazgo = Hallazgo(
        visita_id=visita_id,
        tipo=tipo,
        contenido=file_path,
        descripcion=descripcion
    )
    session.add(hallazgo)
    session.commit()
    session.refresh(hallazgo)
    
    return {
        "id": hallazgo.id,
        "visita_id": hallazgo.visita_id,
        "tipo": hallazgo.tipo,
        "contenido": hallazgo.contenido,
        "descripcion": hallazgo.descripcion,
        "created_at": hallazgo.created_at.isoformat()
    }

@app.get("/api/hallazgos/{hallazgo_id}/archivo")
async def descargar_hallazgo_archivo(
    hallazgo_id: int,
    session: Session = Depends(get_session)
):
    """
    Descargar archivo de un hallazgo (foto o video).
    """
    hallazgo = session.get(Hallazgo, hallazgo_id)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    
    if hallazgo.tipo not in ["foto", "video"]:
        raise HTTPException(status_code=400, detail="Este hallazgo no es un archivo")
    
    if not await storage.file_exists(hallazgo.contenido):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    file_content = await storage.get_file(hallazgo.contenido)
    
    # Determinar content-type basado en la extensión
    content_type = "application/octet-stream"
    if hallazgo.tipo == "foto":
        content_type = "image/jpeg"
    elif hallazgo.tipo == "video":
        content_type = "video/mp4"
    
    return Response(content=file_content, media_type=content_type)

@app.get("/api/visitas/{visita_id}/hallazgos")
def listar_hallazgos(
    visita_id: int,
    session: Session = Depends(get_session)
):
    """
    Listar todos los hallazgos de una visita.
    """
    visita = session.get(Visita, visita_id)
    if not visita:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    
    query = select(Hallazgo).where(Hallazgo.visita_id == visita_id)
    hallazgos = session.exec(query).all()
    
    return [
        {
            "id": h.id,
            "tipo": h.tipo,
            "contenido": h.contenido if h.tipo == "texto" else f"/api/hallazgos/{h.id}/archivo",
            "descripcion": h.descripcion,
            "created_at": h.created_at.isoformat()
        }
        for h in hallazgos
    ]

@app.delete("/api/hallazgos/{hallazgo_id}")
async def eliminar_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session)
):
    """
    Eliminar un hallazgo (y su archivo si existe).
    """
    hallazgo = session.get(Hallazgo, hallazgo_id)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    
    # Eliminar archivo si existe
    if hallazgo.tipo in ["foto", "video"]:
        if await storage.file_exists(hallazgo.contenido):
            await storage.delete_file(hallazgo.contenido)
    
    session.delete(hallazgo)
    session.commit()
    
    return {"message": "Hallazgo eliminado exitosamente"}
