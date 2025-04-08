import requests
import json
from PySide6.QtCore import QObject, Signal

class Session(QObject):
    # Señales para notificar cambios en la sesión
    login_success = Signal(dict)  # emite la información del usuario
    login_failed = Signal(str)    # emite el mensaje de error
    logout_signal = Signal()      # emite cuando se cierra sesión
    
    def __init__(self):
        super().__init__()
        self.token = None
        self.user_info = None
        self.api_url = "http://localhost:8000/api"

    def set_token(self, token):
        self.token = token

    def get_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def login(self, email, password):
        """Función para iniciar sesión y obtener token"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                
                # Obtener información del usuario
                user_info = self.get_user_info()
                if user_info:
                    self.user_info = user_info
                    self.login_success.emit(user_info)
                    return True
                else:
                    self.login_failed.emit("No se pudo obtener información del usuario")
                    return False
            else:
                error_message = "Error al iniciar sesión"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_message = error_data["detail"]
                except:
                    pass
                self.login_failed.emit(error_message)
                return False
        except Exception as e:
            self.login_failed.emit(f"Error de conexión: {str(e)}")
            return False

    def get_user_info(self):
        """Obtiene la información del usuario usando el token"""
        if not self.token:
            return None
            
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.api_url}/usuarios/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                
                # Obtener información del rol
                rol_response = requests.get(f"{self.api_url}/roles/{user_data['rol_id']}", headers=headers)
                if rol_response.status_code == 200:
                    rol_data = rol_response.json()
                    user_data['rol'] = rol_data['nombre']
                else:
                    user_data['rol'] = "Desconocido"
                    
                return user_data
            else:
                return None
        except Exception as e:
            print(f"Error al obtener información del usuario: {e}")
            return None

    def check_token_validity(self):
        """Verifica si el token actual es válido"""
        if not self.token:
            return False
        
        headers = self.get_headers()
        
        try:
            response = requests.get(f"{self.api_url}/usuarios/me", headers=headers)
            return response.status_code == 200
        except:
            return False

    def logout(self):
        """Cierra la sesión del usuario"""
        self.token = None
        self.user_info = None
        self.logout_signal.emit()

# Instancia global
session = Session()