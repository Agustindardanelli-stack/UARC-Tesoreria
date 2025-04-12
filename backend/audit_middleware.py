from functools import wraps
from sqlalchemy.orm import Session
from datetime import datetime
import models

def audit_trail(tabla_afectada):
    def decorator(func):
        @wraps(func)
        def wrapper(db: Session, *args, **kwargs):
            current_user_id = kwargs.get('current_user_id')
            
            print(f"Iniciando auditoría para {tabla_afectada}")
            print(f"Usuario ID: {current_user_id}")
            
            # Eliminar current_user_id de kwargs para no interferir con la función original
            if 'current_user_id' in kwargs:
                del kwargs['current_user_id']
            
            # Realizar la operación original
            resultado = func(db, *args, **kwargs)
            
            # Determinar la acción
            if 'create' in func.__name__.lower():
                accion = "Creación"
            elif 'update' in func.__name__.lower():
                accion = "Actualización"
            elif 'delete' in func.__name__.lower():
                accion = "Eliminación"
            else:
                accion = "Operación"
            
            # Obtener el ID del registro
            registro_id = getattr(resultado, 'id', None)
            
            # Crear registro de auditoría si hay usuario y registro
            if current_user_id and registro_id:
                print(f"Creando registro de auditoría para {tabla_afectada}")
                registro_auditoria = models.Auditoria(
                    usuario_id=current_user_id,
                    accion=accion,
                    tabla_afectada=tabla_afectada,
                    registro_id=registro_id,
                    fecha=datetime.now(),
                    detalles=str(resultado)
                )
                
                # Asignar ID específico según la tabla
                if tabla_afectada == 'partidas':
                    registro_auditoria.pago_id = registro_id
                
                
                
                # Asignar ID específico según la tabla
                if tabla_afectada == 'pagos':
                    registro_auditoria.pago_id = registro_id
                elif tabla_afectada == 'cobranza':
                    registro_auditoria.cobranza_id = registro_id
                elif tabla_afectada == 'cuota':
                    registro_auditoria.cuota_id = registro_id
                elif tabla_afectada == 'partidas':
                    # Añade aquí otros modelos si es necesario
                    pass
                
                db.add(registro_auditoria)
                db.commit()
                print(f"Registro de auditoría creado para {tabla_afectada}")
            
            return resultado
        return wrapper
    return decorator