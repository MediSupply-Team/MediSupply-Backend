"""
Tests básicos para el servicio de visitas
"""
from fastapi.testclient import TestClient
from main import app
from database import init_db
import os

# Usar base de datos de prueba
os.environ["DATABASE_URL"] = "sqlite:///./test_visitas.db"

client = TestClient(app)

def test_health():
    """Test del endpoint de health"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "visita-service"}

def test_crear_visita():
    """Test de creación de visita"""
    init_db()
    
    data = {
        "vendedor_id": 1,
        "cliente_id": 10,
        "nombre_contacto": "Dr. Test",
        "observaciones": "Observaciones de prueba",
        "estado": "pendiente"
    }
    
    response = client.post("/api/visitas", data=data)
    assert response.status_code == 200
    
    json_data = response.json()
    assert json_data["vendedor_id"] == 1
    assert json_data["cliente_id"] == 10
    assert json_data["nombre_contacto"] == "Dr. Test"
    assert json_data["estado"] == "pendiente"
    assert "id" in json_data

def test_listar_visitas():
    """Test de listado de visitas"""
    response = client.get("/api/visitas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_agregar_hallazgo_texto():
    """Test de agregar hallazgo de texto"""
    # Primero crear una visita
    data = {
        "vendedor_id": 1,
        "cliente_id": 10,
        "nombre_contacto": "Dr. Test",
        "estado": "pendiente"
    }
    response = client.post("/api/visitas", data=data)
    visita_id = response.json()["id"]
    
    # Agregar hallazgo
    hallazgo_data = {
        "contenido": "Texto de prueba del hallazgo",
        "descripcion": "Descripción de prueba"
    }
    
    response = client.post(f"/api/visitas/{visita_id}/hallazgos/texto", data=hallazgo_data)
    assert response.status_code == 200
    
    json_data = response.json()
    assert json_data["tipo"] == "texto"
    assert json_data["contenido"] == "Texto de prueba del hallazgo"
    assert json_data["visita_id"] == visita_id

def test_obtener_visita_completa():
    """Test de obtener visita con hallazgos"""
    # Crear visita
    data = {
        "vendedor_id": 1,
        "cliente_id": 10,
        "nombre_contacto": "Dr. Test",
        "estado": "pendiente"
    }
    response = client.post("/api/visitas", data=data)
    visita_id = response.json()["id"]
    
    # Agregar hallazgo
    hallazgo_data = {
        "contenido": "Hallazgo de prueba",
        "descripcion": "Descripción"
    }
    client.post(f"/api/visitas/{visita_id}/hallazgos/texto", data=hallazgo_data)
    
    # Obtener visita completa
    response = client.get(f"/api/visitas/{visita_id}")
    assert response.status_code == 200
    
    json_data = response.json()
    assert json_data["id"] == visita_id
    assert "hallazgos" in json_data
    assert len(json_data["hallazgos"]) == 1

def test_actualizar_estado():
    """Test de actualizar estado de visita"""
    # Crear visita
    data = {
        "vendedor_id": 1,
        "cliente_id": 10,
        "nombre_contacto": "Dr. Test",
        "estado": "pendiente"
    }
    response = client.post("/api/visitas", data=data)
    visita_id = response.json()["id"]
    
    # Actualizar estado
    response = client.patch(f"/api/visitas/{visita_id}/estado", data={"estado": "exitosa"})
    assert response.status_code == 200
    assert response.json()["estado"] == "exitosa"

if __name__ == "__main__":
    print("Ejecutando tests...")
    test_health()
    print("✅ test_health pasó")
    
    test_crear_visita()
    print("✅ test_crear_visita pasó")
    
    test_listar_visitas()
    print("✅ test_listar_visitas pasó")
    
    test_agregar_hallazgo_texto()
    print("✅ test_agregar_hallazgo_texto pasó")
    
    test_obtener_visita_completa()
    print("✅ test_obtener_visita_completa pasó")
    
    test_actualizar_estado()
    print("✅ test_actualizar_estado pasó")
    
    print("\n🎉 Todos los tests pasaron exitosamente!")
    
    # Limpiar base de datos de prueba
    if os.path.exists("./test_visitas.db"):
        os.remove("./test_visitas.db")
