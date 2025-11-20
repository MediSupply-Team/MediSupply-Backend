from functools import wraps
from flask import request, jsonify, current_app
import requests

def require_auth(f):
    """Validar que el request tiene un JWT válido"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify(error="Token no proporcionado"), 401
        
        token = auth_header.replace('Bearer ', '')
        auth_url = current_app.config.get("AUTH_SERVICE_URL")
        
        try:
            response = requests.post(
                f"{auth_url}/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            
            if response.status_code != 200:
                return jsonify(error="Token inválido"), 401
            
            # Usuario autenticado - guardar info
            request.user_info = response.json()
            
        except Exception as e:
            current_app.logger.error(f"Error validando token: {e}")
            return jsonify(error="Error de autenticación"), 503
        
        return f(*args, **kwargs)
    
    return decorated_function