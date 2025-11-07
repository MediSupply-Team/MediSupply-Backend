"""
Servicio de análisis de video usando Google Gemini AI
Procesa videos para generar resúmenes, etiquetas y recomendaciones de productos
"""
import os
import json
import google.generativeai as genai
from typing import Dict, Optional
import tempfile
import aiofiles
from datetime import datetime

# Configuración de Gemini
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

# Configurar la API de Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class VideoAnalysisService:
    """Servicio para análisis de videos con Gemini"""
    
    def __init__(self):
        self.model = None
        if GEMINI_API_KEY:
            try:
                self.model = genai.GenerativeModel(GEMINI_MODEL)
            except Exception as e:
                print(f"Error inicializando modelo Gemini: {e}")
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente"""
        return self.model is not None and GEMINI_API_KEY != ""
    
    async def analyze_video_from_url(self, video_url: str) -> Dict:
        """
        Analiza un video desde una URL (S3 o local) usando Gemini
        
        Args:
            video_url: URL del video (puede ser s3:// o path local)
        
        Returns:
            Dict con summary, tags y recommendations
        """
        if not self.is_configured():
            raise Exception("Gemini API no está configurada. Configure GEMINI_API_KEY en las variables de entorno.")
        
        try:
            # Importar storage para obtener el video
            import storage
            
            # Si es una URL de S3, necesitamos obtener el archivo
            if video_url.startswith("s3://"):
                # Para S3, necesitamos generar una URL firmada o descargar el video temporalmente
                video_content = await storage.get_file(video_url)
                
                # Guardar temporalmente para procesamiento
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                temp_file.write(video_content)
                temp_file.close()
                video_path = temp_file.name
            else:
                # Es un path local
                video_path = video_url
            
            # Subir el video a Gemini
            print(f"📤 Subiendo video a Gemini: {video_path}")
            video_file = genai.upload_file(path=video_path)
            
            # Esperar a que el video se procese
            print(f"⏳ Esperando procesamiento del video...")
            while video_file.state.name == "PROCESSING":
                import time
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise Exception(f"Error procesando video en Gemini: {video_file.state.name}")
            
            # Crear el prompt para análisis
            prompt = """
            Analiza este video de una visita médica/farmacéutica y proporciona:
            
            1. Un resumen detallado de lo que ocurre en el video (2-3 párrafos)
            2. Una lista de etiquetas o categorías relevantes (ej: "consulta médica", "inventario", "productos farmacéuticos", etc.)
            3. Una lista de recomendaciones de productos o acciones basadas en el contenido del video
            
            Responde ÚNICAMENTE con un objeto JSON válido en el siguiente formato, sin texto adicional:
            {
                "summary": "Descripción detallada del video...",
                "tags": ["etiqueta1", "etiqueta2", "etiqueta3"],
                "recommendations": ["Producto/Acción 1", "Producto/Acción 2", "Producto/Acción 3"]
            }
            """
            
            # Generar análisis
            print(f"🤖 Generando análisis con Gemini...")
            response = self.model.generate_content([prompt, video_file])
            
            # Limpiar archivo temporal si existe
            if video_url.startswith("s3://"):
                try:
                    os.unlink(video_path)
                except:
                    pass
            
            # Parsear respuesta
            result = self._parse_gemini_response(response.text)
            
            # Eliminar el archivo de Gemini
            try:
                genai.delete_file(video_file.name)
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"❌ Error en análisis de video: {str(e)}")
            raise Exception(f"Error analizando video: {str(e)}")
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """
        Parsea la respuesta de Gemini y extrae el JSON
        
        Args:
            response_text: Texto de respuesta de Gemini
        
        Returns:
            Dict con summary, tags y recommendations
        """
        try:
            # Intentar parsear directamente como JSON
            # Limpiar markdown code blocks si existen
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            result = json.loads(cleaned_text)
            
            # Validar que tenga los campos esperados
            if "summary" not in result:
                result["summary"] = "No se pudo generar un resumen"
            if "tags" not in result:
                result["tags"] = []
            if "recommendations" not in result:
                result["recommendations"] = []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parseando JSON de Gemini: {e}")
            print(f"Respuesta recibida: {response_text[:500]}")
            
            # Fallback: retornar el texto plano
            return {
                "summary": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "tags": ["análisis_pendiente"],
                "recommendations": ["Revisar video manualmente"]
            }
    
    async def analyze_video_from_bytes(self, video_content: bytes, filename: str = "video.mp4") -> Dict:
        """
        Analiza un video desde bytes directamente
        
        Args:
            video_content: Contenido del video en bytes
            filename: Nombre del archivo (para determinar extensión)
        
        Returns:
            Dict con summary, tags y recommendations
        """
        if not self.is_configured():
            raise Exception("Gemini API no está configurada. Configure GEMINI_API_KEY en las variables de entorno.")
        
        try:
            # Guardar temporalmente
            extension = filename.split(".")[-1] if "." in filename else "mp4"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}")
            temp_file.write(video_content)
            temp_file.close()
            
            # Analizar usando el método de URL
            result = await self.analyze_video_from_url(temp_file.name)
            
            # Limpiar archivo temporal
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"❌ Error en análisis de video desde bytes: {str(e)}")
            raise Exception(f"Error analizando video: {str(e)}")


# Instancia global del servicio
video_analysis_service = VideoAnalysisService()
