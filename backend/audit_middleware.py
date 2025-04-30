from functools import wraps
from sqlalchemy.orm import Session
import models
from datetime import datetime
import inspect

def audit_trail(tabla_afectada):
    def decorator(func):
        @wraps(func)
        def wrapper(db: Session, *args, **kwargs):
            # Intentar extraer current_user_id
            current_user_id = None
            
            # Verificar si la función espera current_user_id
            sig = inspect.signature(func)
            if 'current_user_id' in sig.parameters:
                # Si current_user_id ya está en kwargs, extraerlo
                if 'current_user_id' in kwargs:
                    current_user_id = kwargs.pop('current_user_id')
                # Si no está en kwargs, intentar extraerlo de args si es posible
                elif len(args) > len(list(sig.parameters.keys())) - 1:
                    current_user_id = args[-1]
            
            # Ejecutar la función original
            try:
                # Si la función requiere current_user_id, pasarlo
                if 'current_user_id' in sig.parameters:
                    if current_user_id is None:
                        kwargs['current_user_id'] = None
                    else:
                        kwargs['current_user_id'] = current_user_id
                    resultado = func(db, *args, **kwargs)
                else:
                    resultado = func(db, *args, **kwargs)
            except TypeError:
                # Si falla, intentar ejecutar sin current_user_id
                resultado = func(db, *args, **kwargs)
            
            try:
                # Determinar el ID del registro creado
                if hasattr(resultado, 'id'):
                    registro_id = resultado.id
                else:
                    return resultado
                
                # Crear registro de auditoría
                auditoria = models.Auditoria(
                    usuario_id=current_user_id,  # Puede ser None si no se proporciona
                    accion="crear",
                    tabla_afectada=tabla_afectada,
                    registro_id=registro_id,
                    fecha=datetime.now(),
                    detalles=f"Creación de registro en {tabla_afectada}"
                )
                
                db.add(auditoria)
                db.commit()
            
            except Exception as e:
                print(f"Error en auditoría: {str(e)}")
                db.rollback()
            
            return resultado
        return wrapper
    return decorator