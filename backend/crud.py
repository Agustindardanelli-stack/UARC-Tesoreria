from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, extract
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import date, datetime
import models
import schemas
from audit_middleware import audit_trail
from auth import get_password_hash

# Funciones CRUD para Usuarios
def create_usuario(db: Session, usuario: schemas.UsuarioCreate):
    hashed_password = get_password_hash(usuario.password)
    db_usuario = models.Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=hashed_password,
        rol_id=usuario.rol_id
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

def update_usuario(db: Session, usuario_id: int, usuario_update: schemas.UsuarioUpdate):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = usuario_update.dict(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_usuario, key, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: int):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(db_usuario)
    db.commit()
    return {"message": "Usuario eliminado exitosamente"}

# Funciones CRUD para Roles
def create_rol(db: Session, rol: schemas.RolCreate):
    db_rol = models.Rol(**rol.dict())
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

def get_rol(db: Session, rol_id: int):
    return db.query(models.Rol).filter(models.Rol.id == rol_id).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rol).offset(skip).limit(limit).all()

def update_rol(db: Session, rol_id: int, rol_update: schemas.RolUpdate):
    db_rol = db.query(models.Rol).filter(models.Rol.id == rol_id).first()
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    update_data = rol_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_rol, key, value)
    
    db.commit()
    db.refresh(db_rol)
    return db_rol

def delete_rol(db: Session, rol_id: int):
    db_rol = db.query(models.Rol).filter(models.Rol.id == rol_id).first()
    if not db_rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Verificar si hay usuarios con este rol
    usuarios_con_rol = db.query(models.Usuario).filter(models.Usuario.rol_id == rol_id).count()
    if usuarios_con_rol > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el rol porque hay {usuarios_con_rol} usuarios asignados a él"
        )
    
    db.delete(db_rol)
    db.commit()
    return {"message": "Rol eliminado exitosamente"}


# Funciones CRUD para EmailConfig
def create_email_config(db: Session, config_data):
    db_config = models.EmailConfig(**config_data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_active_email_config(db: Session):
    return db.query(models.EmailConfig).filter(models.EmailConfig.is_active == True).first()

def update_email_config(db: Session, config_id: int, config_data):
    db_config = db.query(models.EmailConfig).filter(models.EmailConfig.id == config_id).first()
    if not db_config:
        return None
    
    for key, value in config_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config



# Funciones CRUD para Retenciones
def create_retencion(db: Session, retencion: schemas.RetencionCreate):
    db_retencion = models.Retencion(**retencion.dict())
    db.add(db_retencion)
    db.commit()
    db.refresh(db_retencion)
    return db_retencion

def get_retencion(db: Session, retencion_id: int):
    return db.query(models.Retencion).filter(models.Retencion.id == retencion_id).first()

def get_retenciones(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Retencion).offset(skip).limit(limit).all()

def update_retencion(db: Session, retencion_id: int, retencion_update: schemas.RetencionUpdate):
    db_retencion = db.query(models.Retencion).filter(models.Retencion.id == retencion_id).first()
    if not db_retencion:
        raise HTTPException(status_code=404, detail="Retención no encontrada")
    
    update_data = retencion_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_retencion, key, value)
    
    db.commit()
    db.refresh(db_retencion)
    return db_retencion

def delete_retencion(db: Session, retencion_id: int):
    db_retencion = db.query(models.Retencion).filter(models.Retencion.id == retencion_id).first()
    if not db_retencion:
        raise HTTPException(status_code=404, detail="Retención no encontrada")
    
    # Verificar si hay pagos con esta retención
    pagos_con_retencion = db.query(models.Pago).filter(models.Pago.retencion_id == retencion_id).count()
    if pagos_con_retencion > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar la retención porque hay {pagos_con_retencion} pagos asociados a ella"
        )
    
    db.delete(db_retencion)
    db.commit()
    return {"message": "Retención eliminada exitosamente"}

# Funciones CRUD para Pagos
@audit_trail("pagos")
def create_pago(db: Session, pago: schemas.PagoCreate):
    db_pago = models.Pago(**pago.dict())
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    
    # Obtener información del usuario para el detalle
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
    
    # Preparar el detalle, agregando la retención si existe
    detalle = f"Pago a {nombre_usuario}"
    if db_pago.retencion_id:
        retencion = db.query(models.Retencion).filter(models.Retencion.id == db_pago.retencion_id).first()
        if retencion:
            detalle += f" - {retencion.nombre}"
    
    # Crear partida asociada al pago (egreso)
    partida = models.Partida(
        fecha=db_pago.fecha,
        detalle=detalle,
        monto=db_pago.monto,
        tipo="egreso",
        cuenta="CAJA",
        usuario_id=db_pago.usuario_id,
        pago_id=db_pago.id,
        saldo=0,
        ingreso=0,
        egreso=db_pago.monto
    )
    db.add(partida)
    db.commit()
    
    try:
        # Verificar si hay configuración de email activa y el usuario tiene email
        if usuario and usuario.email:
            email_config = get_active_email_config(db)
            
            if email_config:
                # Importar aquí para evitar problemas de importación circular
                from email_service import EmailService
                
                # Crear servicio de email
                email_service = EmailService(
                    smtp_server=email_config.smtp_server,
                    smtp_port=email_config.smtp_port,
                    username=email_config.smtp_username,
                    password=email_config.smtp_password,
                    sender_email=email_config.email_from
                )
                
                # Enviar recibo
                success, message = email_service.send_payment_receipt_email(
                    db=db,
                    pago=db_pago, 
                    recipient_email=usuario.email
                )
                
                # Actualizar estado del envío
                if success:
                    db_pago.email_enviado = True
                    db_pago.fecha_envio_email = datetime.now()
                    db_pago.email_destinatario = usuario.email
                    db.commit()
                    db.refresh(db_pago)
                    print(f"Orden de pago enviada por email a {usuario.email}")
                else:
                    print(f"Error al enviar orden de pago: {message}")
    except Exception as e:
        print(f"Error en envío de orden de pago por email: {str(e)}")
    
    return db_pago

def reenviar_orden_pago(db: Session, pago_id: int, email: str = None, current_user_id: int = None):
    # Obtener el pago
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        return {"success": False, "message": "Pago no encontrado"}
    
    # Obtener usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
    
    # Determinar el email a usar
    recipient_email = email if email else (usuario.email if usuario else None)
    
    if not recipient_email:
        return {"success": False, "message": "No hay email destinatario disponible"}
    
    # Obtener configuración de email
    email_config = get_active_email_config(db)
    if not email_config:
        return {"success": False, "message": "No hay configuración de email activa"}
    
    # Importar aquí para evitar problemas de importación circular
    from email_service import EmailService
    
    # Enviar la orden de pago
    email_service = EmailService(
        smtp_server=email_config.smtp_server,
        smtp_port=email_config.smtp_port,
        username=email_config.smtp_username,
        password=email_config.smtp_password,
        sender_email=email_config.email_from
    )
    
    # Usando el método para órdenes de pago
    success, message = email_service.send_payment_receipt_email(
        db=db,
        pago=db_pago, 
        recipient_email=recipient_email
    )
    
    # Actualizar estado
    if success:
        db_pago.email_enviado = True
        db_pago.fecha_envio_email = datetime.now()
        db_pago.email_destinatario = recipient_email
        db.commit()
        db.refresh(db_pago)
        return {"success": True, "message": "Orden de pago enviada exitosamente"}
    else:
        return {"success": False, "message": message}

@audit_trail("pagos")
def get_pagos(db: Session, skip: int = 0, limit: int = 100):
    pagos = db.query(models.Pago).order_by(desc(models.Pago.fecha)).offset(skip).limit(limit).all()
    
    for pago in pagos:
        if pago.retencion_id is None:
            pago.retencion = None
    
    return pagos
@audit_trail("pagos")
def get_pago(db: Session, pago_id: int):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    
    if pago and pago.retencion_id is None:
        pago.retencion = None
    
    return pago
@audit_trail("pagos")
def update_pago(db: Session, pago_id: int, pago_update: schemas.PagoUpdate):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    update_data = pago_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_pago, key, value)
    
    db.commit()
    db.refresh(db_pago)
    
    # Actualizar partida asociada
    partida = db.query(models.Partida).filter(models.Partida.pago_id == pago_id).first()
    if partida:
        partida.fecha = db_pago.fecha
        partida.detalle = f"Pago a {db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first().nombre}"
        partida.monto = db_pago.monto
        partida.egreso = db_pago.monto
        partida.usuario_id = db_pago.usuario_id
        db.commit()
    
    return db_pago
@audit_trail("pagos")
def delete_pago(db: Session, pago_id: int):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Eliminar partida asociada
    partida = db.query(models.Partida).filter(models.Partida.pago_id == pago_id).first()
    if partida:
        db.delete(partida)
    
    db.delete(db_pago)
    db.commit()
    return {"message": "Pago eliminado exitosamente"}



# Añadir función para reenviar recibos
def reenviar_recibo(db: Session, cobranza_id: int, email: str = None):
    # Obtener la cobranza
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        return {"success": False, "message": "Cobranza no encontrada"}
    
    # Obtener usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
    
    # Determinar el email a usar
    recipient_email = email if email else (usuario.email if usuario else None)
    
    if not recipient_email:
        return {"success": False, "message": "No hay email destinatario disponible"}
    
    # Obtener configuración de email
    email_config = get_active_email_config(db)
    if not email_config:
        return {"success": False, "message": "No hay configuración de email activa"}
    
    # Importar aquí para evitar problemas de importación circular
    from email_service import EmailService
    
    # Enviar el recibo
    email_service = EmailService(
        smtp_server=email_config.smtp_server,
        smtp_port=email_config.smtp_port,
        username=email_config.smtp_username,
        password=email_config.smtp_password,
        sender_email=email_config.email_from
    )
    
    success, message = email_service.send_receipt_email(
        db=db,
        cobranza=db_cobranza, 
        recipient_email=recipient_email
    )
    
    # Actualizar estado
    if success:
        db_cobranza.email_enviado = True
        db_cobranza.fecha_envio_email = datetime.now()
        db_cobranza.email_destinatario = recipient_email
        db.commit()
        db.refresh(db_cobranza)
        return {"success": True, "message": "Recibo enviado exitosamente"}
    else:
        return {"success": False, "message": message}

# Funciones CRUD para Cobranzas
@audit_trail("cobranza")
def create_cobranza(db: Session, cobranza: schemas.CobranzaCreate):
    db_cobranza = models.Cobranza(**cobranza.dict())  # Nota: cambié cobranza_data a cobranza.dict()
    db.add(db_cobranza)
    db.commit()
    db.refresh(db_cobranza)
    
    partida = models.Partida(
        fecha=db_cobranza.fecha,
        detalle=f"Cobranza de {db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first().nombre}",
        monto=db_cobranza.monto,
        tipo="ingreso",
        cuenta="CAJA",
        usuario_id=db_cobranza.usuario_id,
        cobranza_id=db_cobranza.id,
        saldo=0,
        ingreso=db_cobranza.monto,
        egreso=0
    )
    db.add(partida)
    db.commit()
    
    try:
        # Obtener usuario para su email
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
        
        # Verificar si hay configuración de email activa y el usuario tiene email
        if usuario and usuario.email:
            email_config = get_active_email_config(db)
            
            if email_config:
                # Importar aquí para evitar problemas de importación circular
                from email_service import EmailService
                
                # Crear servicio de email
                email_service = EmailService(
                    smtp_server=email_config.smtp_server,
                    smtp_port=email_config.smtp_port,
                    username=email_config.smtp_username,
                    password=email_config.smtp_password,
                    sender_email=email_config.email_from
                )
                
                # Enviar recibo
                success, message = email_service.send_receipt_email(
                    db=db,
                    cobranza=db_cobranza, 
                    recipient_email=usuario.email
                )
                
                # Actualizar estado del envío
                if success:
                    db_cobranza.email_enviado = True
                    db_cobranza.fecha_envio_email = datetime.now()
                    db_cobranza.email_destinatario = usuario.email
                    db.commit()
                    db.refresh(db_cobranza)
                    print(f"Recibo enviado por email a {usuario.email}")
                else:
                    print(f"Error al enviar recibo: {message}")
    except Exception as e:
        print(f"Error en envío de recibo por email: {str(e)}")
    
    return db_cobranza
     


def get_cobranza(db: Session, cobranza_id: int):
    return db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()

def get_cobranzas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cobranza).order_by(desc(models.Cobranza.fecha)).offset(skip).limit(limit).all()
@audit_trail("cobranza")
def update_cobranza(db: Session, cobranza_id: int, cobranza_update: schemas.CobranzaUpdate):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    update_data = cobranza_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cobranza, key, value)
    
    db.commit()
    db.refresh(db_cobranza)
    
    # Actualizar partida asociada
    partida = db.query(models.Partida).filter(models.Partida.cobranza_id == cobranza_id).first()
    if partida:
        partida.fecha = db_cobranza.fecha
        partida.detalle = f"Cobranza de {db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first().nombre}"
        partida.monto = db_cobranza.monto
        partida.ingreso = db_cobranza.monto
        partida.usuario_id = db_cobranza.usuario_id
        db.commit()
    
    return db_cobranza
@audit_trail("cobranza")
def delete_cobranza(db: Session, cobranza_id: int):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    # Eliminar partida asociada
    partida = db.query(models.Partida).filter(models.Partida.cobranza_id == cobranza_id).first()
    if partida:
        db.delete(partida)
    
    db.delete(db_cobranza)
    db.commit()
    return {"message": "Cobranza eliminada exitosamente"}

# Funciones CRUD para Cuotas
@audit_trail("cuota")
def create_cuota(db: Session, cuota: schemas.CuotaCreate):
    db_cuota = models.Cuota(**cuota.dict())
    db.add(db_cuota)
    db.commit()
    db.refresh(db_cuota)
    return db_cuota

def get_cuota(db: Session, cuota_id: int):
    return db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()

def get_cuotas(db: Session, skip: int = 0, limit: int = 100, pagado: Optional[bool] = None):
    query = db.query(models.Cuota)
    
    if pagado is not None:
        query = query.filter(models.Cuota.pagado == pagado)
    
    return query.order_by(desc(models.Cuota.fecha)).offset(skip).limit(limit).all()

def get_cuotas_by_usuario(db: Session, usuario_id: int, pagado: Optional[bool] = None):
    query = db.query(models.Cuota).filter(models.Cuota.usuario_id == usuario_id)
    
    if pagado is not None:
        query = query.filter(models.Cuota.pagado == pagado)
    
    return query.order_by(desc(models.Cuota.fecha)).all()
@audit_trail("cuota")
def update_cuota(db: Session, cuota_id: int, cuota_update: schemas.CuotaUpdate):
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    
    update_data = cuota_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cuota, key, value)
    
    db.commit()
    db.refresh(db_cuota)
    return db_cuota
@audit_trail("cuota")
def pagar_cuota(db: Session, cuota_id: int, monto_pagado: float):
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    
    if db_cuota.pagado:
        raise HTTPException(status_code=400, detail="La cuota ya ha sido pagada")
    
    # Actualizar cuota
    db_cuota.monto_pagado = monto_pagado
    db_cuota.fecha_pago = func.now()
    db_cuota.pagado = True
    
    # Crear cobranza asociada
    cobranza = models.Cobranza(
        fecha=func.now(),
        monto=monto_pagado,
        usuario_id=db_cuota.usuario_id
    )
    db.add(cobranza)
    db.commit()
    db.refresh(cobranza)
    
    # Crear partida asociada a la cobranza
    partida = models.Partida(
        fecha=func.now(),
        detalle=f"Pago de cuota del {db_cuota.fecha.strftime('%d/%m/%Y')}",
        monto=monto_pagado,
        tipo="ingreso",
        cuenta="CAJA",
        usuario_id=db_cuota.usuario_id,
        cobranza_id=cobranza.id,
        saldo=0,
        ingreso=monto_pagado,
        egreso=0
    )
    db.add(partida)
    db.commit()
    
    try:
        # Obtener usuario para su email
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cuota.usuario_id).first()
        
        # Verificar si hay configuración de email activa y el usuario tiene email
        if usuario and usuario.email:
            email_config = get_active_email_config(db)
            
            if email_config:
                # Importar aquí para evitar problemas de importación circular
                from email_service import EmailService
                
                # Crear servicio de email
                email_service = EmailService(
                    smtp_server=email_config.smtp_server,
                    smtp_port=email_config.smtp_port,
                    username=email_config.smtp_username,
                    password=email_config.smtp_password,
                    sender_email=email_config.email_from
                )
                
                # Enviar recibo
                success, message = email_service.send_cuota_receipt_email(
                    db=db,
                    cuota=db_cuota, 
                    recipient_email=usuario.email
                )
                
                # Actualizar estado del envío
                if success:
                    db_cuota.email_enviado = True
                    db_cuota.fecha_envio_email = datetime.now()
                    db_cuota.email_destinatario = usuario.email
                    db.commit()
                    db.refresh(db_cuota)
                    print(f"Recibo de cuota enviado por email a {usuario.email}")
                else:
                    print(f"Error al enviar recibo de cuota: {message}")
    except Exception as e:
        print(f"Error en envío de recibo de cuota por email: {str(e)}")
    
    db.refresh(db_cuota)
    return db_cuota
# Función para reenviar recibo en crud.py
def reenviar_recibo_cuota(db: Session, cuota_id: int, email: str = None):
    # Obtener la cuota
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        return {"success": False, "message": "Cuota no encontrada"}
    
    if not db_cuota.pagado:
        return {"success": False, "message": "La cuota no ha sido pagada aún"}
    
    # Obtener usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cuota.usuario_id).first()
    
    # Determinar el email a usar
    recipient_email = email if email else (usuario.email if usuario else None)
    
    if not recipient_email:
        return {"success": False, "message": "No hay email destinatario disponible"}
    
    # Obtener configuración de email
    email_config = get_active_email_config(db)
    if not email_config:
        return {"success": False, "message": "No hay configuración de email activa"}
    
    # Importar aquí para evitar problemas de importación circular
    from email_service import EmailService
    
    # Enviar el recibo
    email_service = EmailService(
        smtp_server=email_config.smtp_server,
        smtp_port=email_config.smtp_port,
        username=email_config.smtp_username,
        password=email_config.smtp_password,
        sender_email=email_config.email_from
    )
    
    success, message = email_service.send_cuota_receipt_email(
        db=db,
        cuota=db_cuota, 
        recipient_email=recipient_email
    )
    
    # Actualizar estado
    if success:
        db_cuota.email_enviado = True
        db_cuota.fecha_envio_email = datetime.now()
        db_cuota.email_destinatario = recipient_email
        db.commit()
        db.refresh(db_cuota)
        return {"success": True, "message": "Recibo de cuota enviado exitosamente"}
    else:
        return {"success": False, "message": message}

def delete_cuota(db: Session, cuota_id: int):
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    
    if db_cuota.pagado:
        raise HTTPException(status_code=400, detail="No se puede eliminar una cuota que ya ha sido pagada")
    
    db.delete(db_cuota)
    db.commit()
    return {"message": "Cuota eliminada exitosamente"}

# Funciones CRUD para Partidas
@audit_trail("partidas")
def create_partida(db: Session, partida: schemas.PartidaCreate, current_user_id: int = None):
    db_partida = models.Partida(**partida.dict())
    db.add(db_partida)
    db.commit()
    db.refresh(db_partida)
    return db_partida

@audit_trail("partidas")
def get_partida(db: Session, partida_id: int = None, skip: int = 0, limit: int = 100,
               fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None,
               tipo: Optional[str] = None, cuenta: Optional[str] = None, current_user_id: int = None):
    if partida_id:
        return db.query(models.Partida).filter(models.Partida.id == partida_id).first()
    
    query = db.query(models.Partida)
    
    # Aplicar filtros
    if fecha_desde:
        query = query.filter(models.Partida.fecha >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(models.Partida.fecha <= fecha_hasta)
    
    if tipo:
        query = query.filter(models.Partida.tipo == tipo)
    
    if cuenta:
        query = query.filter(models.Partida.cuenta == cuenta)
    
    return query.order_by(desc(models.Partida.fecha)).offset(skip).limit(limit).all()

@audit_trail("partidas")
def update_partida(db: Session, partida_id: int, partida_update: schemas.PartidaUpdate, current_user_id: int = None):
    db_partida = db.query(models.Partida).filter(models.Partida.id == partida_id).first()
    if not db_partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    update_data = partida_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_partida, key, value)
    
    db.commit()
    db.refresh(db_partida)
    return db_partida

@audit_trail("partidas")
def delete_partida(db: Session, partida_id: int, current_user_id: int = None):
    db_partida = db.query(models.Partida).filter(models.Partida.id == partida_id).first()
    if not db_partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    db.delete(db_partida)
    db.commit()
    return {"message": "Partida eliminada exitosamente"}

# Funciones CRUD para Categorías
def create_categoria(db: Session, categoria: schemas.CategoriaCreate):
    db_categoria = models.Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def get_categoria(db: Session, categoria_id: int):
    return db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()

def get_categorias(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Categoria).offset(skip).limit(limit).all()

def update_categoria(db: Session, categoria_id: int, categoria_update: schemas.CategoriaUpdate):
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    update_data = categoria_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_categoria, key, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def delete_categoria(db: Session, categoria_id: int):
    db_categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar si hay transacciones con esta categoría
    transacciones_con_categoria = db.query(models.Transaccion).filter(models.Transaccion.categoria_id == categoria_id).count()
    if transacciones_con_categoria > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar la categoría porque hay {transacciones_con_categoria} transacciones asociadas a ella"
        )
    
    db.delete(db_categoria)
    db.commit()
    return {"message": "Categoría eliminada exitosamente"}

# Funciones CRUD para Transacciones
def create_transaccion(db: Session, transaccion: schemas.TransaccionCreate):
    db_transaccion = models.Transaccion(**transaccion.dict())
    db.add(db_transaccion)
    db.commit()
    db.refresh(db_transaccion)
    return db_transaccion

def get_transaccion(db: Session, transaccion_id: int):
    return db.query(models.Transaccion).filter(models.Transaccion.id == transaccion_id).first()

def get_transacciones(db: Session, skip: int = 0, limit: int = 100, 
                     fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None,
                     tipo: Optional[str] = None):
    query = db.query(models.Transaccion)
    
    # Aplicar filtros
    if fecha_desde:
        query = query.filter(models.Transaccion.fecha >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(models.Transaccion.fecha <= fecha_hasta)
    
    if tipo:
        query = query.filter(models.Transaccion.tipo == tipo)
    
    return query.order_by(desc(models.Transaccion.fecha)).offset(skip).limit(limit).all()

def update_transaccion(db: Session, transaccion_id: int, transaccion_update: schemas.TransaccionUpdate):
    db_transaccion = db.query(models.Transaccion).filter(models.Transaccion.id == transaccion_id).first()
    if not db_transaccion:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    update_data = transaccion_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_transaccion, key, value)
    
    db.commit()
    db.refresh(db_transaccion)
    return db_transaccion

def delete_transaccion(db: Session, transaccion_id: int):
    db_transaccion = db.query(models.Transaccion).filter(models.Transaccion.id == transaccion_id).first()
    if not db_transaccion:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    db.delete(db_transaccion)
    db.commit()
    return {"message": "Transacción eliminada exitosamente"}

# Funciones para Auditoría
def get_partida(db: Session, partida_id: int = None, skip: int = 0, limit: int = 100, 
               fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None,
               tipo: Optional[str] = None, cuenta: Optional[str] = None):
    query = db.query(models.Partida)
    
    # Aplicar filtros
    if fecha_desde:
        query = query.filter(models.Partida.fecha >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(models.Partida.fecha <= fecha_hasta)
    
    if tipo:
        query = query.filter(models.Partida.tipo == tipo)
    
    if cuenta:
        query = query.filter(models.Partida.cuenta == cuenta)
    
    # Ordenar y paginar
    query = query.order_by(desc(models.Partida.fecha)).offset(skip).limit(limit)
    
    # Obtener resultados
    return query.all()

# Funciones para Reportes
def get_balance(db: Session, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None):
    query = db.query(models.Partida)
    
    # Aplicar filtros
    if fecha_desde:
        query = query.filter(models.Partida.fecha >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(models.Partida.fecha <= fecha_hasta)
    
    ingresos = query.filter(models.Partida.tipo == "ingreso").with_entities(func.sum(models.Partida.monto)).scalar() or 0
    egresos = query.filter(models.Partida.tipo == "egreso").with_entities(func.sum(models.Partida.monto)).scalar() or 0
    
    saldo = ingresos - egresos
    
    return {
        "ingresos": ingresos,
        "egresos": egresos,
        "saldo": saldo,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta
    }

def get_ingresos_egresos_mensuales(db: Session, anio: Optional[int] = None):
    current_year = datetime.now().year
    year_to_query = anio if anio else current_year
    
    # Obtener ingresos y egresos por mes
    result = []
    
    for month in range(1, 13):
        ingresos = db.query(func.sum(models.Partida.monto)).filter(
            models.Partida.tipo == "ingreso",
            extract('year', models.Partida.fecha) == year_to_query,
            extract('month', models.Partida.fecha) == month
        ).scalar() or 0
        
        egresos = db.query(func.sum(models.Partida.monto)).filter(
            models.Partida.tipo == "egreso",
            extract('year', models.Partida.fecha) == year_to_query,
            extract('month', models.Partida.fecha) == month
        ).scalar() or 0
        
        result.append({
            "mes": month,
            "nombre_mes": get_nombre_mes(month),
            "ingresos": ingresos,
            "egresos": egresos,
            "balance": ingresos - egresos
        })
    
    return {
        "anio": year_to_query,
        "datos": result
    }

def get_cuotas_pendientes(db: Session):
    cuotas_pendientes = db.query(models.Cuota).filter(
        models.Cuota.pagado == False,
        models.Cuota.fecha < func.now()
    ).all()
    
    result = []
    
    for cuota in cuotas_pendientes:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == cuota.usuario_id).first()
        
        if usuario:
            result.append({
                "cuota_id": cuota.id,
                "usuario_id": usuario.id,
                "nombre_usuario": usuario.nombre,
                "monto": cuota.monto,
                "fecha": cuota.fecha.strftime("%Y-%m-%d"),
                "dias_vencido": (datetime.now().date() - cuota.fecha).days
            })
    
    return result

# Función auxiliar para obtener el nombre del mes
def get_nombre_mes(month_number):
    nombres_meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }
    return nombres_meses.get(month_number, "")