from database import SessionLocal
from models import Usuario, Rol
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from typing import Optional, Dict, Any, Tuple

# Configuración para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_all_roles(self):
        """Obtiene todos los roles disponibles de la base de datos"""
        try:
            return self.db.query(Rol).all()
        except Exception as e:
            print(f"Error al obtener roles: {str(e)}")
            return []
    
    def check_user_exists(self, email: str) -> bool:
        """Verifica si ya existe un usuario con el email proporcionado"""
        try:
            existing_user = self.db.query(Usuario).filter(Usuario.email == email).first()
            return existing_user is not None
        except Exception as e:
            print(f"Error al verificar usuario existente: {str(e)}")
            return False
    
    def add_user(self, nombre: str, email: str, password: str, rol_id: int = None, rol_nombre: str = None) -> Tuple[bool, str]:        
        try:
            # Verificar si el usuario ya existe
            if self.check_user_exists(email):
                return False, "⚠️ El usuario ya existe en la base de datos."
            
            # Hashear la contraseña
            password_hash = pwd_context.hash(password)
            
            # Determinar el rol_id
            if rol_id is None and rol_nombre:
                # Buscar el rol por nombre
                rol = self.db.query(Rol).filter(Rol.nombre == rol_nombre).first()
                if rol:
                    rol_id = rol.id
                else:
                    return False, f"❌ Error: El rol '{rol_nombre}' no existe."
            
            if rol_id is None:
                return False, "❌ Error: Debe proporcionar un rol válido."
            
            # Crear el nuevo usuario
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                password_hash=password_hash,
                rol_id=rol_id
            )
            
            # Guardar en la base de datos
            self.db.add(nuevo_usuario)
            self.db.commit()
            
            return True, f"✅ Usuario {nombre} agregado con éxito."
            
        except IntegrityError:
            self.db.rollback()
            return False, "❌ Error: No se pudo agregar el usuario. Verifica los datos."
        except Exception as e:
            self.db.rollback()
            return False, f"❌ Error: {str(e)}"
    
    def get_role_by_name(self, role_name: str) -> Optional[Rol]:
        """Obtiene un rol por su nombre"""
        try:
            return self.db.query(Rol).filter(Rol.nombre == role_name).first()
        except Exception as e:
            print(f"Error al obtener rol por nombre: {str(e)}")
            return None
    
    def get_role_by_id(self, role_id: int) -> Optional[Rol]:
        """Obtiene un rol por su ID"""
        try:
            return self.db.query(Rol).filter(Rol.id == role_id).first()
        except Exception as e:
            print(f"Error al obtener rol por ID: {str(e)}")
            return None
    
    def get_all_users(self):
        """Obtiene todos los usuarios de la base de datos"""
        try:
            return self.db.query(Usuario).all()
        except Exception as e:
            print(f"Error al obtener usuarios: {str(e)}")
            return []
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.db:
            self.db.close()
    
    def __del__(self):
        """Destructor para asegurar que la sesión se cierre"""
        self.close()


# Ejecutar directamente como script (similar a tu versión original)
if __name__ == "__main__":
    user_manager = UserManager()
    
    try:
        # Datos del nuevo usuario (como en tu versión original)
        nombre = "TESORERO"
        email = "agusdardanelli16@gmail.com"
        password = "1234"
        rol_nombre = "tesorero"
        
        # Agregar usuario usando el nombre del rol
        success, message = user_manager.add_user(
            nombre=nombre,
            email=email,
            password=password,
            rol_nombre=rol_nombre
        )
        
        print(message)
        
    finally:
        user_manager.close()