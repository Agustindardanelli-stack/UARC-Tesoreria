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
    
    # # Verificar si hay pagos con esta retención
    # # pagos_con_retencion = db.query(models.Pago).filter(models.Pago.retencion_id == retencion_id).count()
    # if pagos_con_retencion > 0:
    #     raise HTTPException(
    #         status_code=400, 
    #         detail=f"No se puede eliminar la retención porque hay {pagos_con_retencion} pagos asociados a ella"
    #     )
    
    db.delete(db_retencion)
    db.commit()
    return {"message": "Retención eliminada exitosamente"}

# Funciones CRUD para Pagos
@audit_trail("pagos")
def create_pago(db: Session, pago: schemas.PagoCreate, current_user_id: int):
    # Crear el pago
    db_pago = models.Pago(**pago.dict())
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    
    # Obtener información del usuario para el detalle
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
    
    # Obtener la última partida para calcular el saldo
    ultima_partida = db.query(models.Partida).order_by(models.Partida.id.desc()).first()
    saldo_anterior = ultima_partida.saldo if ultima_partida else 0
    nuevo_saldo = saldo_anterior - db_pago.monto
    
    # Crear partida asociada al pago (egreso)
    partida = models.Partida(
        fecha=db_pago.fecha,
        detalle=f"Pago {nombre_usuario}",
        monto=db_pago.monto,
        tipo="egreso",
        cuenta="CAJA",
        usuario_id=current_user_id,  # Usuario que realiza la acción
        pago_id=db_pago.id,
        saldo=nuevo_saldo,
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

# Añadir función para reenviar órdenes de pago
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
def get_pagos(db: Session, skip: int = 0, limit: int = 100,):
    
    pagos = db.query(models.Pago).order_by(desc(models.Pago.fecha)).offset(skip).limit(limit).all()
    
    return pagos

@audit_trail("pagos")
def get_pago(db: Session, pago_id: int, current_user_id: int = None):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    return pago


@audit_trail("pagos")
def update_pago(db: Session, pago_id: int, pago_update: schemas.PagoUpdate, current_user_id: int = None):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Guardar monto anterior para comparar
    monto_anterior = db_pago.monto
    
    update_data = pago_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_pago, key, value)
    
    db.commit()
    db.refresh(db_pago)
    
    # Actualizar partida asociada
    partida = db.query(models.Partida).filter(models.Partida.pago_id == pago_id).first()
    if partida:
        partida.fecha = db_pago.fecha
        
        # Obtener nombre de usuario
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
        
        partida.detalle = f"Pago {nombre_usuario}"
        partida.monto = db_pago.monto
        partida.egreso = db_pago.monto
        partida.usuario_id = db_pago.usuario_id
        db.commit()
        
        # Si el monto cambió, recalcular los saldos de todas las partidas posteriores
        if abs(monto_anterior - db_pago.monto) > 0.01:
            partidas_posteriores = db.query(models.Partida).filter(
                models.Partida.fecha >= partida.fecha,
                models.Partida.id != partida.id
            ).order_by(models.Partida.fecha, models.Partida.id).all()
            
            # Obtener saldo actualizado para esta partida
            saldo_actual = partida.saldo
            
            # Actualizar saldos para todas las partidas posteriores
            for p in partidas_posteriores:
                if p.tipo == "ingreso":
                    saldo_actual += p.monto
                else:  # egreso
                    saldo_actual -= p.monto
                
                p.saldo = saldo_actual
            
            db.commit()
    
    return db_pago
@audit_trail("pagos")
def delete_pago(db: Session, pago_id: int, current_user_id: int = None):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Guardar fecha y monto del pago para recalcular saldos después
    fecha_pago = db_pago.fecha
    monto_pago = db_pago.monto
    
    # Encontrar la partida asociada
    partida = db.query(models.Partida).filter(models.Partida.pago_id == pago_id).first()
    
    # Eliminar partida asociada
    if partida:
        db.delete(partida)
    
    # Eliminar el pago
    db.delete(db_pago)
    db.commit()
    
    # Recalcular saldos de todas las partidas posteriores a la fecha del pago eliminado
    partidas_posteriores = db.query(models.Partida).filter(
        models.Partida.fecha >= fecha_pago
    ).order_by(models.Partida.fecha, models.Partida.id).all()
    
    # Si hay partidas posteriores, recalcular saldos
    if partidas_posteriores:
        # Obtener el saldo anterior a la partida eliminada
        partida_anterior = db.query(models.Partida).filter(
            models.Partida.fecha < fecha_pago
        ).order_by(models.Partida.fecha.desc(), models.Partida.id.desc()).first()
        
        saldo_inicial = partida_anterior.saldo if partida_anterior else 0
        
        # Recalcular saldos para todas las partidas posteriores
        saldo_actual = saldo_inicial
        for p in partidas_posteriores:
            if p.tipo == "ingreso":
                saldo_actual += p.monto
            else:  # egreso
                saldo_actual -= p.monto
            
            p.saldo = saldo_actual
        
        db.commit()
    
    return {"message": "Pago eliminado exitosamente"}

# Añadir función para reenviar recibos
def reenviar_recibo(db: Session, cobranza_id: int, email: str = None , current_user_id: int = None):
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
# Funciones CRUD para Cobranzas
@audit_trail("cobranza")
def create_cobranza(db: Session, cobranza: schemas.CobranzaCreate, current_user_id: int):
    # Validar retencion_id si se proporciona
    if cobranza.retencion_id is not None:
        retencion = db.query(models.Retencion).filter(models.Retencion.id == cobranza.retencion_id).first()
        if not retencion:
            raise HTTPException(status_code=404, detail="Retención no encontrada")

    db_cobranza = models.Cobranza(**cobranza.dict())
    db.add(db_cobranza)
    db.commit()
    db.refresh(db_cobranza)
    
    # Obtener la última partida para calcular el saldo
    ultima_partida = db.query(models.Partida).order_by(models.Partida.id.desc()).first()
    saldo_anterior = ultima_partida.saldo if ultima_partida else 0
    nuevo_saldo = saldo_anterior + db_cobranza.monto
    
    partida = models.Partida(
        fecha=db_cobranza.fecha,
        detalle=f"Cobranza - {db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first().nombre}",
        monto=db_cobranza.monto,
        tipo="ingreso",
        cuenta="CAJA",
        usuario_id=current_user_id,  # Usuario que REALIZA la acción
        cobranza_id=db_cobranza.id,
        saldo=nuevo_saldo,
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

@audit_trail("cobranza")
def update_cobranza(db: Session, cobranza_id: int, cobranza_update: schemas.CobranzaUpdate, current_user_id: int = None):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    # Guardar monto anterior para comparar
    monto_anterior = db_cobranza.monto
    
    update_data = cobranza_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cobranza, key, value)
    
    db.commit()
    db.refresh(db_cobranza)
    
    # Actualizar partida asociada
    partida = db.query(models.Partida).filter(models.Partida.cobranza_id == cobranza_id).first()
    if partida:
        partida.fecha = db_cobranza.fecha
        
        # Obtener nombre de usuario
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
        
        partida.detalle = f"Cobranza {nombre_usuario}"
        partida.monto = db_cobranza.monto
        partida.ingreso = db_cobranza.monto
        partida.usuario_id = db_cobranza.usuario_id
        db.commit()
        
        # Si el monto cambió, recalcular los saldos de todas las partidas posteriores
        if abs(monto_anterior - db_cobranza.monto) > 0.01:
            partidas_posteriores = db.query(models.Partida).filter(
                models.Partida.fecha >= partida.fecha,
                models.Partida.id != partida.id
            ).order_by(models.Partida.fecha, models.Partida.id).all()
            
            # Obtener saldo actualizado para esta partida
            saldo_actual = partida.saldo
            
            # Actualizar saldos para todas las partidas posteriores
            for p in partidas_posteriores:
                if p.tipo == "ingreso":
                    saldo_actual += p.monto
                else:  # egreso
                    saldo_actual -= p.monto
                
                p.saldo = saldo_actual
            
            db.commit()
    
    return db_cobranza
def get_cobranza(db: Session, cobranza_id: int):
    return db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()

def get_cobranzas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cobranza).order_by(desc(models.Cobranza.fecha)).offset(skip).limit(limit).all()


@audit_trail("cobranza")
def delete_cobranza(db: Session, cobranza_id: int, current_user_id: int = None):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    # Guardar información relevante antes de eliminar
    fecha_cobranza = db_cobranza.fecha
    monto_cobranza = db_cobranza.monto
    usuario_id = db_cobranza.usuario_id
    
    # Obtener información del usuario para registro
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
    
    # Encontrar la partida asociada
    partida = db.query(models.Partida).filter(models.Partida.cobranza_id == cobranza_id).first()
    
    # Eliminar partida asociada
    if partida:
        db.delete(partida)
    
    # Eliminar la cobranza
    db.delete(db_cobranza)
    db.commit()
    
    # Crear partida/movimiento que registre la eliminación
    partida_eliminacion = models.Partida(
        fecha=func.now(),
        detalle=f"ELIMINACIÓN Cobranza - {nombre_usuario} (ID: {cobranza_id})",
        monto=monto_cobranza,
        tipo="anulacion",  # Nuevo tipo para identificar eliminaciones
        cuenta="CAJA",
        usuario_id=current_user_id,  # Usuario que realizó la eliminación
        ingreso=0,
        egreso=0,  # No afecta el balance nuevamente
        saldo=0  # Se calculará después
    )
    db.add(partida_eliminacion)
    db.commit()
    db.refresh(partida_eliminacion)
    
    # Recalcular saldos
    recalcular_saldos_transacciones(db)
    
    return {"message": "Cobranza eliminada exitosamente"}
# Funciones CRUD para Cuotas
@audit_trail("cuota")
def create_cuota(db: Session, cuota: schemas.CuotaCreate, current_user_id: int, no_generar_movimiento: bool = False):
    # Crear la cuota
    db_cuota = models.Cuota(**cuota.dict())
    db.add(db_cuota)
    db.commit()
    db.refresh(db_cuota)
    
    # Solo crear partida si no_generar_movimiento es False
    if not no_generar_movimiento:
        # Obtener información del usuario para el detalle
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cuota.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
        
        partida = models.Partida(
            fecha=db_cuota.fecha,
            detalle=f"Cuota {nombre_usuario}",
            monto=db_cuota.monto,
            tipo="ingreso",
            cuenta="CUOTAS",
            usuario_id=current_user_id,  # Usuario que realiza la acción
            saldo=0,
            ingreso=db_cuota.monto,
            egreso=0
        )
        db.add(partida)
        db.commit()
    
    return db_cuota

def get_cuota(db: Session, cuota_id: int):
    return db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()

def get_cuotas(db: Session, skip: int = 0, limit: int = 100, pagado: Optional[bool] = None):
    # Consulta base de cuotas
    query = db.query(models.Cuota)
    
    # Filtrar por estado de pago si se especifica
    if pagado is not None:
        query = query.filter(models.Cuota.pagado == pagado)
    
    # Ordenar por fecha, más recientes primero
    cuotas = query.order_by(desc(models.Cuota.fecha)).offset(skip).limit(limit).all()
    
    # Procesar cuotas para mostrar deudas acumuladas
    cuotas_procesadas = []
    usuarios_cuotas = {}
    fecha_actual = datetime.now().date()

    for cuota in cuotas:
        # Si la cuota no está pagada, agrupar por usuario
        if not cuota.pagado:
            if cuota.usuario_id not in usuarios_cuotas:
                usuarios_cuotas[cuota.usuario_id] = {
                    'cuotas': [],
                    'monto_total': 0,
                    'fecha_primera': cuota.fecha
                }
            
            usuarios_cuotas[cuota.usuario_id]['cuotas'].append(cuota)
            usuarios_cuotas[cuota.usuario_id]['monto_total'] += cuota.monto
            
            # Actualizar fecha primera si es más antigua
            if cuota.fecha < usuarios_cuotas[cuota.usuario_id]['fecha_primera']:
                usuarios_cuotas[cuota.usuario_id]['fecha_primera'] = cuota.fecha

    # Modificar las cuotas para incluir información de deuda
    for cuota in cuotas:
        # Si el usuario tiene múltiples cuotas pendientes, añadir información
        if not cuota.pagado and cuota.usuario_id in usuarios_cuotas:
            info_usuario = usuarios_cuotas[cuota.usuario_id]
            
            # Calcular meses de atraso
            meses_atraso = (fecha_actual.year - cuota.fecha.year) * 12 + (fecha_actual.month - cuota.fecha.month)
            
            # Si hay más de una cuota pendiente, añadir información adicional
            if len(info_usuario['cuotas']) > 1:
                cuota.monto_total_pendiente = float(info_usuario['monto_total'])
                cuota.cuotas_pendientes = len(info_usuario['cuotas'])
                cuota.fecha_primera_deuda = info_usuario['fecha_primera']
                cuota.meses_atraso = meses_atraso
        
        cuotas_procesadas.append(cuota)
    
    return cuotas_procesadas

def calcular_meses_atraso(fecha_cuota):
    """
    Calcula los meses de atraso desde una fecha de cuota
    """
    # Obtener fecha actual
    fecha_actual = datetime.now().date()
    
    # Calcular meses de atraso
    meses_atraso = (
        (fecha_actual.year - fecha_cuota.year) * 12 + 
        (fecha_actual.month - fecha_cuota.month)
    )
    
    # Ajustar si el día actual es menor que el día de la cuota
    if fecha_actual.day < fecha_cuota.day:
        meses_atraso -= 1
    
    return max(0, meses_atraso)

def get_cuotas_by_usuario(db: Session, usuario_id: int, pagado: Optional[bool] = None):
    # Consulta base de cuotas para un usuario específico
    query = db.query(models.Cuota).filter(models.Cuota.usuario_id == usuario_id)
    
    # Filtrar por estado de pago si se especifica
    if pagado is not None:
        query = query.filter(models.Cuota.pagado == pagado)
    
    # Ordenar por fecha, más recientes primero
    cuotas = query.order_by(desc(models.Cuota.fecha)).all()
    
    # Procesar cuotas no pagadas
    cuotas_pendientes = [cuota for cuota in cuotas if not cuota.pagado]
    fecha_actual = datetime.now().date()
    
    # Si hay cuotas pendientes, añadir información de deuda
    if cuotas_pendientes:
        # Calcular monto total de cuotas pendientes
        monto_total_pendiente = sum(cuota.monto for cuota in cuotas_pendientes)
        
        # Encontrar la fecha de la primera cuota pendiente
        fecha_primera_deuda = min(cuota.fecha for cuota in cuotas_pendientes)
        
        # Calcular meses de atraso
        meses_atraso = (fecha_actual.year - fecha_primera_deuda.year) * 12 + (fecha_actual.month - fecha_primera_deuda.month)
        
        # Añadir información a cada cuota pendiente
        for cuota in cuotas_pendientes:
            cuota.monto_total_pendiente = float(monto_total_pendiente)
            cuota.cuotas_pendientes = len(cuotas_pendientes)
            cuota.fecha_primera_deuda = fecha_primera_deuda
            cuota.meses_atraso = meses_atraso
    
    return cuotas
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
def pagar_cuota(db: Session, cuota_id: int, monto_pagado: float, current_user_id: int, generar_movimiento: bool = True):
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    
    if db_cuota.pagado:
        raise HTTPException(status_code=400, detail="La cuota ya ha sido pagada")
    
    # Actualizar cuota
    db_cuota.monto_pagado = monto_pagado
    db_cuota.fecha_pago = func.now()
    db_cuota.pagado = True
    
    # Crear partida directamente sin crear cobranza
    if generar_movimiento:
        # Crear partida asociada directamente a la cuota
        partida = models.Partida(
            fecha=func.now(),
            detalle=f"Pago de cuota societaria del {db_cuota.fecha.strftime('%d/%m/%Y')}",
            monto=monto_pagado,
            tipo="ingreso",
            cuenta="CAJA",
            usuario_id=db_cuota.usuario_id,
            # No asignar cobranza_id
            saldo=0,  # Se calculará correctamente después
            ingreso=monto_pagado,
            egreso=0
        )
        db.add(partida)
        db.commit()
        
        # Recalcular saldo
        try:
            # Obtener todas las partidas en orden cronológico
            partidas = db.query(models.Partida).order_by(
                models.Partida.fecha,
                models.Partida.id
            ).all()
            
            # Recalcular saldos
            saldo_actual = 0
            for p in partidas:
                if p.tipo == "ingreso":
                    saldo_actual += p.monto
                else:  # egreso o anulacion
                    saldo_actual -= p.monto
                
                p.saldo = saldo_actual
            
            db.commit()
        except Exception as e:
            print(f"Error al recalcular saldos: {str(e)}")
    
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
def reenviar_recibo_cuota(db: Session, cuota_id: int, email: str = None , current_user_id: int = None):
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
    # Obtener la última partida para calcular el saldo
    ultima_partida = db.query(models.Partida).order_by(models.Partida.id.desc()).first()
    
    # Calcular nuevo saldo
    saldo_anterior = ultima_partida.saldo if ultima_partida else 0
    
    if partida.tipo == 'ingreso':
        nuevo_saldo = saldo_anterior + partida.monto
    else:  # egreso
        nuevo_saldo = saldo_anterior - partida.monto
    
    # Crear partida con el saldo calculado
    db_partida = models.Partida(**partida.dict(exclude={'saldo'}), saldo=nuevo_saldo)
    
    # Si se proporciona current_user_id, establecerlo como usuario
    if current_user_id:
        db_partida.usuario_id = current_user_id
    
    db.add(db_partida)
    db.commit()
    db.refresh(db_partida)
    return db_partida

@audit_trail("partidas")
def get_partida(
    db: Session, 
    partida_id: int = None, 
    skip: int = 0, 
    limit: int = 100, 
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    cuenta: Optional[str] = None,
    current_user_id: int = None
):
    # Si se busca una partida específica
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
    
    # Ordenar por fecha
    query = query.order_by(models.Partida.fecha.desc(), models.Partida.id.desc())
    
    # Aplicar paginación
    partidas = query.offset(skip).limit(limit).all()
    
    # Obtener el último saldo calculado
    ultima_partida = db.query(models.Partida).order_by(models.Partida.fecha.desc(), models.Partida.id.desc()).first()
    saldo_inicial = ultima_partida.saldo if ultima_partida else 0
    
    # Calcular saldos acumulativos
    saldo_acumulado = saldo_inicial
    for partida in reversed(partidas):
        # Ajustar saldo antes de asignarlo
        if partida.tipo == 'ingreso':
            saldo_acumulado -= partida.monto
        else:  # egreso
            saldo_acumulado += partida.monto
        
        partida.saldo = saldo_acumulado
    
    # Obtener información de auditoría para cada partida
    for partida in partidas:
        # Buscar el primer registro de auditoría para esta partida
        auditoria = db.query(models.Auditoria)\
            .filter(
                models.Auditoria.tabla_afectada == 'partidas', 
                models.Auditoria.registro_id == partida.id
            )\
            .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
            .order_by(models.Auditoria.fecha.desc())\
            .first()
        
        # Asignar nombre de usuario de auditoría
        partida.usuario_auditoria = auditoria.usuario.nombre if auditoria and auditoria.usuario else 'Sin registro'
    
    return list(reversed(partidas))

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
    # Obtener el mayor ID existente
    max_id = db.query(func.max(models.Categoria.id)).scalar() or 0
    
    # Crear objeto de categoria con un ID nuevo
    db_categoria = models.Categoria(
        id=max_id + 1,  # Asignar un ID mayor que el máximo existente
        nombre=categoria.nombre
    )
    
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
    
    # Verificar si hay divisiones con esta categoría en lugar de transacciones
    divisiones_con_categoria = db.query(models.RetencionDivision).filter(
        models.RetencionDivision.categoria_id == categoria_id
    ).count()
    
    if divisiones_con_categoria > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar la categoría porque hay {divisiones_con_categoria} divisiones asociadas a ella"
        )
    
    db.delete(db_categoria)
    db.commit()
    return {"message": "Categoría eliminada exitosamente"}

# Funciones CRUD para Transacciones
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from typing import Optional
import models
import schemas

def create_transaccion(db: Session, transaccion: schemas.TransaccionCreate, current_user_id: Optional[int] = None):
    """
    Crea una nueva transacción y calcula el saldo acumulado
    """
    # Crear el diccionario con los datos de la transacción
    transaccion_data = transaccion.dict()
    
    # Crear objeto de transacción sin guardar aún (sin el saldo)
    db_transaccion = models.Transaccion(**transaccion_data)
    
    # Obtener la última transacción para obtener el último saldo
    ultima_transaccion = db.query(models.Transaccion).order_by(
        desc(models.Transaccion.id)
    ).first()
    
    ultimo_saldo = 0  # Saldo inicial si no hay transacciones previas
    
    if ultima_transaccion and hasattr(ultima_transaccion, 'saldo') and ultima_transaccion.saldo is not None:
        ultimo_saldo = float(ultima_transaccion.saldo)
    
    # Calcular nuevo saldo
    if db_transaccion.tipo == "ingreso":
        nuevo_saldo = ultimo_saldo + float(db_transaccion.monto)
    else:  # egreso
        nuevo_saldo = ultimo_saldo - float(db_transaccion.monto)
    
    # Asignar el nuevo saldo a la transacción
    db_transaccion.saldo = nuevo_saldo
    
    # Guardar en la base de datos
    db.add(db_transaccion)
    db.commit()
    db.refresh(db_transaccion)
    
    # Registrar en auditoría si se proporciona un usuario
    if current_user_id:
        auditoria = models.Auditoria(
            usuario_id=current_user_id,
            accion="crear",
            tabla_afectada="transacciones",
            registro_id=db_transaccion.id,
            detalles=f"Creación de transacción: {db_transaccion.tipo} por {db_transaccion.monto}"
        )
        db.add(auditoria)
        db.commit()
    
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

def update_transaccion(db: Session, transaccion_id: int, transaccion_update: schemas.TransaccionUpdate, current_user_id: Optional[int] = None):
    db_transaccion = db.query(models.Transaccion).filter(models.Transaccion.id == transaccion_id).first()
    if not db_transaccion:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    update_data = transaccion_update.dict(exclude_unset=True)
    
    # Guardar valores anteriores para registrar en auditoría
    old_values = {
        "tipo": db_transaccion.tipo,
        "monto": float(db_transaccion.monto),
        "fecha": db_transaccion.fecha
    }
    
    # Si se cambia el tipo o monto, recalcular todos los saldos a partir de esta transacción
    recalcular_saldos = False
    if "tipo" in update_data or "monto" in update_data:
        recalcular_saldos = True
    
    # Actualizar los campos de la transacción
    for key, value in update_data.items():
        setattr(db_transaccion, key, value)
    
    # Guardar cambios iniciales
    db.commit()
    db.refresh(db_transaccion)
    
    # Si es necesario recalcular saldos
    if recalcular_saldos:
        # Obtener todas las transacciones desde esta en adelante
        transacciones = db.query(models.Transaccion).filter(
            models.Transaccion.fecha >= db_transaccion.fecha
        ).order_by(
            models.Transaccion.fecha,
            models.Transaccion.id
        ).all()
        
        # Obtener el saldo anterior a esta transacción
        transaccion_anterior = db.query(models.Transaccion).filter(
            models.Transaccion.id < transaccion_id
        ).order_by(
            desc(models.Transaccion.id)
        ).first()
        
        saldo_actual = 0
        if transaccion_anterior and hasattr(transaccion_anterior, 'saldo') and transaccion_anterior.saldo is not None:
            saldo_actual = float(transaccion_anterior.saldo)
        
        # Recalcular saldos para cada transacción
        for t in transacciones:
            if t.tipo == "ingreso":
                saldo_actual += float(t.monto)
            else:  # egreso
                saldo_actual -= float(t.monto)
            
            # Actualizar el saldo
            t.saldo = saldo_actual
        
        # Guardar cambios de saldos
        db.commit()
    
    # Registrar en auditoría si se proporciona un usuario
    if current_user_id:
        # Crear registro de cambios
        cambios = []
        for key, old_value in old_values.items():
            if key in update_data and update_data[key] != old_value:
                cambios.append(f"{key}: {old_value} -> {update_data[key]}")
        
        cambios_str = ", ".join(cambios) if cambios else "Sin cambios en campos principales"
        
        auditoria = models.Auditoria(
            usuario_id=current_user_id,
            accion="actualizar",
            tabla_afectada="transacciones",
            registro_id=db_transaccion.id,
            detalles=f"Actualización de transacción: {cambios_str}"
        )
        db.add(auditoria)
        db.commit()
    
    return db_transaccion

def delete_transaccion(db: Session, transaccion_id: int, current_user_id: Optional[int] = None):
    db_transaccion = db.query(models.Transaccion).filter(models.Transaccion.id == transaccion_id).first()
    if not db_transaccion:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    
    # Guardar información de la transacción para el registro de auditoría
    transaccion_info = {
        "id": db_transaccion.id,
        "tipo": db_transaccion.tipo,
        "monto": float(db_transaccion.monto),
        "fecha": db_transaccion.fecha
    }
    
    # Eliminar la transacción
    db.delete(db_transaccion)
    db.commit()
    
    # Recalcular saldos después de eliminar la transacción
    transacciones = db.query(models.Transaccion).filter(
        models.Transaccion.fecha >= transaccion_info["fecha"]
    ).order_by(
        models.Transaccion.fecha,
        models.Transaccion.id
    ).all()
    
    if transacciones:
        # Obtener el saldo anterior a la fecha de la transacción eliminada
        transaccion_anterior = db.query(models.Transaccion).filter(
            models.Transaccion.fecha < transaccion_info["fecha"]
        ).order_by(
            desc(models.Transaccion.fecha),
            desc(models.Transaccion.id)
        ).first()
        
        saldo_actual = 0
        if transaccion_anterior and hasattr(transaccion_anterior, 'saldo') and transaccion_anterior.saldo is not None:
            saldo_actual = float(transaccion_anterior.saldo)
        
        # Recalcular saldos para cada transacción
        for t in transacciones:
            if t.tipo == "ingreso":
                saldo_actual += float(t.monto)
            else:  # egreso
                saldo_actual -= float(t.monto)
            
            # Actualizar el saldo
            t.saldo = saldo_actual
        
        # Guardar cambios de saldos
        db.commit()
    
    # Registrar en auditoría si se proporciona un usuario
    if current_user_id:
        auditoria = models.Auditoria(
            usuario_id=current_user_id,
            accion="eliminar",
            tabla_afectada="transacciones",
            registro_id=transaccion_info["id"],
            detalles=f"Eliminación de transacción: {transaccion_info['tipo']} por {transaccion_info['monto']} del {transaccion_info['fecha']}"
        )
        db.add(auditoria)
        db.commit()
    
    return {"message": "Transacción eliminada exitosamente"}

def recalcular_saldos_transacciones(db: Session):
    """
    Recalcula los saldos de todas las transacciones en orden cronológico
    """
    # Obtener todas las transacciones ordenadas por fecha y luego por ID
    transacciones = db.query(models.Transaccion).order_by(
        models.Transaccion.fecha,
        models.Transaccion.id
    ).all()
    
    if not transacciones:
        return {"message": "No hay transacciones para recalcular", "transacciones_actualizadas": 0}
    
    saldo_actual = 0
    transacciones_actualizadas = 0
    
    # Recalcular saldos para cada transacción
    for transaccion in transacciones:
        if transaccion.tipo == "ingreso":
            saldo_actual += float(transaccion.monto)
        else:  # egreso
            saldo_actual -= float(transaccion.monto)
        
        # Actualizar el saldo
        transaccion.saldo = saldo_actual
        transacciones_actualizadas += 1
    
    # Guardar cambios
    db.commit()
    
    return {
        "message": "Saldos recalculados correctamente", 
        "transacciones_actualizadas": transacciones_actualizadas
    }

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

def get_auditoria(db: Session, skip: int = 0, limit: int = 100, 
                tabla_afectada: Optional[str] = None, usuario_id: Optional[int] = None,
                fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None,
                create_usuario: int = None):
    query = db.query(models.Auditoria)
    
    # Aplicar filtros
    if tabla_afectada:
        query = query.filter(models.Auditoria.tabla_afectada == tabla_afectada)
    
    if usuario_id:
        query = query.filter(models.Auditoria.usuario_id == usuario_id)
    
    if fecha_desde:
        query = query.filter(models.Auditoria.fecha >= fecha_desde)
    
    if fecha_hasta:
        query = query.filter(models.Auditoria.fecha <= fecha_hasta)
    
    # Ordenar y paginar
    return query.order_by(desc(models.Auditoria.fecha)).offset(skip).limit(limit).all()