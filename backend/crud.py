from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import Date, and_, cast, desc, extract, func, text
from sqlalchemy.orm import Session, joinedload

from audit_middleware import audit_trail
from auth import get_password_hash
from email_service import EmailService
import models
import schemas


# ==========================================
# Funciones Auxiliares para Email en Background
# ==========================================
def enviar_email_cobranza_background(db_session_factory, cobranza_id: int):
    """Procesa el envío de email de recibo en segundo plano sin bloquear el POST."""
    db = db_session_factory()
    try:
        db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
        if not db_cobranza or db_cobranza.tipo_documento != "recibo":
            return

        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
        if usuario and usuario.email:
            email_config = get_active_email_config(db)
            if email_config:
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
                    recipient_email=usuario.email
                )
                if success:
                    db_cobranza.email_enviado = True
                    db_cobranza.fecha_envio_email = datetime.now()
                    db_cobranza.email_destinatario = usuario.email
                    db.commit()
    except Exception as e:
        print(f"Error enviando email de cobranza en segundo plano: {str(e)}")
    finally:
        db.close()


def enviar_email_pago_background(db_session_factory, pago_id: int):
    """Procesa el envío de email de orden de pago en segundo plano sin bloquear el POST."""
    db = db_session_factory()
    try:
        db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
        if not db_pago or db_pago.tipo_documento != "orden_pago":
            return

        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
        if usuario and usuario.email:
            email_config = get_active_email_config(db)
            if email_config:
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
                    recipient_email=usuario.email
                )
                if success:
                    db_pago.email_enviado = True
                    db_pago.fecha_envio_email = datetime.now()
                    db_pago.email_destinatario = usuario.email
                    db.commit()
    except Exception as e:
        print(f"Error enviando email de pago en segundo plano: {str(e)}")
    finally:
        db.close()


def enviar_emails_cuotas_background(db_session_factory, para_email: List[Dict[str, Any]]):
    """Envía los recibos de cuotas en segundo plano, con su propia sesión de DB."""
    db = db_session_factory()
    try:
        email_config = get_active_email_config(db)
        if not email_config:
            return
        email_service = EmailService(
            smtp_server=email_config.smtp_server,
            smtp_port=email_config.smtp_port,
            username=email_config.smtp_username,
            password=email_config.smtp_password,
            sender_email=email_config.email_from
        )
        for item in para_email:
            try:
                db_cuota = db.query(models.Cuota).filter(models.Cuota.id == item["cuota_id"]).first()
                if not db_cuota:
                    continue
                success, message = email_service.send_cuota_receipt_email(
                    db=db,
                    cuota=db_cuota,
                    recipient_email=item["email"]
                )
                if success:
                    db_cuota.email_enviado = True
                    db_cuota.fecha_envio_email = datetime.now()
                    db_cuota.email_destinatario = item["email"]
                    db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error enviando recibo de cuota {item.get('cuota_id')}: {str(e)}")
    finally:
        db.close()


# ==========================================
# Funciones CRUD para Usuarios
# ==========================================
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
    
    if update_data.get("password"):
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


# ==========================================
# Funciones CRUD para Roles
# ==========================================
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
    
    usuarios_con_rol = db.query(models.Usuario).filter(models.Usuario.rol_id == rol_id).count()
    if usuarios_con_rol > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el rol porque hay {usuarios_con_rol} usuarios asignados a él"
        )
    
    db.delete(db_rol)
    db.commit()
    return {"message": "Rol eliminado exitosamente"}


# ==========================================
# Funciones CRUD para EmailConfig
# ==========================================
def create_email_config(db: Session, config_data: dict):
    db_config = models.EmailConfig(**config_data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_active_email_config(db: Session):
    return db.query(models.EmailConfig).filter(models.EmailConfig.is_active.is_(True)).first()

def update_email_config(db: Session, config_id: int, config_data: dict):
    db_config = db.query(models.EmailConfig).filter(models.EmailConfig.id == config_id).first()
    if not db_config:
        return None
    
    for key, value in config_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


# ==========================================
# Funciones CRUD para Retenciones
# ==========================================
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
    
    db.delete(db_retencion)
    db.commit()
    return {"message": "Retención eliminada exitosamente"}


# ==========================================
# Funciones CRUD para Pagos
# ==========================================
@audit_trail("pagos")
def create_pago(db: Session, pago: schemas.PagoCreate, current_user_id: int):
    db_pago = models.Pago(**pago.dict())
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
    
    if db_pago.tipo_documento == "factura":
        recibo_factura = f"FAC/REC.A-{db_pago.numero_factura}"
    else:
        ultima_orden_pago = db.query(models.Partida).filter(
            models.Partida.recibo_factura.like("O.P-%")
        ).order_by(models.Partida.id.desc()).first()
        
        if ultima_orden_pago and ultima_orden_pago.recibo_factura:
            try:
                ultimo_num = int(ultima_orden_pago.recibo_factura.split('-')[1])
                nuevo_num = ultimo_num + 1
            except (ValueError, IndexError):
                nuevo_num = 1
        else:
            nuevo_num = 1
        
        recibo_factura = f"O.P-{nuevo_num}"
    
    partida = models.Partida(
        fecha=db_pago.fecha,
        detalle=f"Pago {nombre_usuario}",
        monto=db_pago.monto,
        tipo="egreso",
        cuenta="CAJA",
        usuario_id=current_user_id,
        pago_id=db_pago.id,
        saldo=0,
        ingreso=0,
        egreso=db_pago.monto,
        recibo_factura=recibo_factura
    )
    db.add(partida)
    db.commit()

    recalcular_saldos_partidas(db)
    return db_pago

def reenviar_orden_pago(db: Session, pago_id: int, email: Optional[str] = None, current_user_id: Optional[int] = None):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        return {"success": False, "message": "Pago no encontrado"}
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
    recipient_email = email or (usuario.email if usuario else None)
    
    if not recipient_email:
        return {"success": False, "message": "No hay email destinatario disponible"}
    
    email_config = get_active_email_config(db)
    if not email_config:
        return {"success": False, "message": "No hay configuración de email activa"}
    
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
    
    if success:
        db_pago.email_enviado = True
        db_pago.fecha_envio_email = datetime.now()
        db_pago.email_destinatario = recipient_email
        db.commit()
        db.refresh(db_pago)
        return {"success": True, "message": "Orden de pago enviada exitosamente"}
    return {"success": False, "message": message}

@audit_trail("pagos")
def get_pagos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Pago).order_by(desc(models.Pago.fecha)).offset(skip).limit(limit).all()

@audit_trail("pagos")
def get_pago(db: Session, pago_id: int, current_user_id: Optional[int] = None):
    return db.query(models.Pago).filter(models.Pago.id == pago_id).first()

@audit_trail("pagos")
def update_pago(db: Session, pago_id: int, pago_update: schemas.PagoUpdate, current_user_id: Optional[int] = None):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    monto_anterior = db_pago.monto
    update_data = pago_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_pago, key, value)
    
    db.commit()
    db.refresh(db_pago)
    
    partida = db.query(models.Partida).filter(models.Partida.pago_id == pago_id).first()
    if partida:
        fecha_anterior = partida.fecha
        partida.fecha = db_pago.fecha
        
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
        
        partida.detalle = f"Pago {nombre_usuario}"
        partida.monto = db_pago.monto
        partida.egreso = db_pago.monto
        partida.usuario_id = db_pago.usuario_id
        db.commit()
        
        if abs(monto_anterior - db_pago.monto) > 0.01 or fecha_anterior != db_pago.fecha:
            recalcular_saldos_partidas(db)
    
    return db_pago

@audit_trail("pagos")
def delete_pago(db: Session, pago_id: int, current_user_id: Optional[int] = None):
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    partida = db.query(models.Partida).filter(models.Partida.pago_id == pago_id).first()
    if partida:
        db.delete(partida)
    
    db.delete(db_pago)
    db.commit()
    
    recalcular_saldos_partidas(db)
    return {"message": "Pago eliminado exitosamente"}


# ==========================================
# Funciones CRUD para Cobranza
# ==========================================
def reenviar_recibo(db: Session, cobranza_id: int, email: Optional[str] = None, current_user_id: Optional[int] = None):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        return {"success": False, "message": "Cobranza no encontrada"}
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
    recipient_email = email or (usuario.email if usuario else None)
    
    if not recipient_email:
        return {"success": False, "message": "No hay email destinatario disponible"}
    
    email_config = get_active_email_config(db)
    if not email_config:
        return {"success": False, "message": "No hay configuración de email activa"}
    
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
    
    if success:
        db_cobranza.email_enviado = True
        db_cobranza.fecha_envio_email = datetime.now()
        db_cobranza.email_destinatario = recipient_email
        db.commit()
        db.refresh(db_cobranza)
        return {"success": True, "message": "Recibo enviado exitosamente"}
    return {"success": False, "message": message}

@audit_trail("cobranza")
def create_cobranza(db: Session, cobranza: schemas.CobranzaCreate, current_user_id: int):
    if cobranza.retencion_id is not None:
        retencion = db.query(models.Retencion).filter(models.Retencion.id == cobranza.retencion_id).first()
        if not retencion:
            raise HTTPException(status_code=404, detail="Retención no encontrada")
    
    db_cobranza = models.Cobranza(**cobranza.dict())
    db.add(db_cobranza)
    db.commit()
    db.refresh(db_cobranza)
    
    if db_cobranza.tipo_documento == "factura":
        recibo_factura = f"FAC/REC.A-{db_cobranza.numero_factura}"
    else:
        ultimo_recibo = db.query(models.Partida).filter(
            models.Partida.recibo_factura.like("REC-%")
        ).order_by(models.Partida.id.desc()).first()
        
        if ultimo_recibo and ultimo_recibo.recibo_factura:
            try:
                ultimo_num = int(ultimo_recibo.recibo_factura.split('-')[1])
                nuevo_num = ultimo_num + 1
            except (ValueError, IndexError):
                nuevo_num = 1
        else:
            nuevo_num = 1
        
        recibo_factura = f"REC-{nuevo_num}"
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"

    partida = models.Partida(
        fecha=db_cobranza.fecha,
        detalle=f"Cobranza - {nombre_usuario}",
        monto=db_cobranza.monto,
        tipo="ingreso",
        cuenta="CAJA",
        usuario_id=current_user_id,
        cobranza_id=db_cobranza.id,
        saldo=0,
        ingreso=db_cobranza.monto,
        egreso=0,
        recibo_factura=recibo_factura
    )
    db.add(partida)
    db.commit()

    # recalcular_saldos_partidas(db)
    return db_cobranza

@audit_trail("cobranza")
def update_cobranza(db: Session, cobranza_id: int, cobranza_update: schemas.CobranzaUpdate, current_user_id: Optional[int] = None):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    monto_anterior = db_cobranza.monto
    update_data = cobranza_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cobranza, key, value)
    
    db.commit()
    db.refresh(db_cobranza)
    
    partida = db.query(models.Partida).filter(models.Partida.cobranza_id == cobranza_id).first()
    if partida:
        partida.fecha = db_cobranza.fecha
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
        
        partida.detalle = f"Cobranza {nombre_usuario}"
        partida.monto = db_cobranza.monto
        partida.ingreso = db_cobranza.monto
        partida.usuario_id = db_cobranza.usuario_id
        db.commit()
        
        if abs(monto_anterior - db_cobranza.monto) > 0.01:
            recalcular_saldos_partidas(db)
    
    return db_cobranza

def get_cobranza(db: Session, cobranza_id: int):
    return db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()

def get_cobranzas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cobranza).order_by(desc(models.Cobranza.fecha)).offset(skip).limit(limit).all()

@audit_trail("cobranza")
def delete_cobranza(db: Session, cobranza_id: int, current_user_id: Optional[int] = None):
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    monto_cobranza = db_cobranza.monto
    usuario_id = db_cobranza.usuario_id
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"
    
    partida = db.query(models.Partida).filter(models.Partida.cobranza_id == cobranza_id).first()
    if partida:
        db.delete(partida)

    db.delete(db_cobranza)
    db.commit()
    
    recalcular_saldos_partidas(db)
    
    partida_eliminacion = models.Partida(
        fecha=func.now(),
        detalle=f"ELIMINACIÓN Cobranza - {nombre_usuario} (ID: {cobranza_id})",
        monto=monto_cobranza,
        tipo="anulacion",
        cuenta="CAJA",
        usuario_id=current_user_id,
        ingreso=0,
        egreso=0,
        saldo=0
    )
    db.add(partida_eliminacion)
    db.commit()
    
    return {"message": "Cobranza eliminada exitosamente"}


# ==========================================
# Funciones CRUD para Cuotas
# ==========================================
def siguiente_nro_comprobante(db: Session) -> int:
    """Obtiene el próximo nro_comprobante de la secuencia (atómico, sin carreras)."""
    return db.execute(text("SELECT nextval('cuota_nro_comprobante_seq')")).scalar()


@audit_trail("cuota")
def create_cuota(db: Session, cuota: schemas.CuotaCreate, current_user_id: int, no_generar_movimiento: bool = False):
    nro_comprobante = siguiente_nro_comprobante(db)

    cuota_data = cuota.dict()
    cuota_data['creado_por_usuario_id'] = current_user_id
    cuota_data['nro_comprobante'] = nro_comprobante

    db_cuota = models.Cuota(**cuota_data)
    db.add(db_cuota)
    db.commit()
    db.refresh(db_cuota)

    if not no_generar_movimiento:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cuota.usuario_id).first()
        nombre_usuario = usuario.nombre if usuario else "Usuario desconocido"

        partida = models.Partida(
            fecha=db_cuota.fecha,
            detalle=f"Cuota {nombre_usuario}",
            monto=db_cuota.monto,
            tipo="ingreso",
            cuenta="CUOTAS",
            usuario_id=current_user_id,
            recibo_factura=f"C.S.-{db_cuota.nro_comprobante}",
            saldo=0,
            ingreso=db_cuota.monto,
            egreso=0
        )
        db.add(partida)
        db.commit()
        recalcular_saldos_partidas(db)

    return db_cuota

@audit_trail("cuota")
def pagar_cuota(
    db: Session,
    cuota_id: int,
    monto_pagado: float,
    generar_movimiento: bool = True,
    actualizar_saldo: bool = True,
    current_user_id: Optional[int] = None,
):
    cuota = db.query(models.Cuota).options(joinedload(models.Cuota.usuario)).filter(models.Cuota.id == cuota_id).first()

    if not cuota:
        raise ValueError("No se encontró la cuota")
    if cuota.pagado:
        raise ValueError("La cuota ya está pagada")

    cuota.pagado = True
    cuota.monto_pagado = Decimal(monto_pagado)
    cuota.pagado_por_usuario_id = current_user_id
    cuota.fecha_pago = datetime.now()

    cuota.monto_total_pendiente = None
    cuota.cuotas_pendientes = None
    cuota.fecha_primera_deuda = None
    cuota.meses_atraso = None

    if generar_movimiento:
        nueva_partida = models.Partida(
            fecha=datetime.now().date(),
            cuenta="INGRESOS",
            detalle=f"Pago de cuota de {cuota.usuario.nombre}" if cuota.usuario else "Pago de cuota",
            ingreso=Decimal(monto_pagado),
            egreso=0,
            saldo=0,
            usuario_id=current_user_id,
            monto=Decimal(monto_pagado),
            tipo="ingreso",
            recibo_factura=f"C.S.-{cuota.nro_comprobante}",
        )
        db.add(nueva_partida)
        db.commit()

        recalcular_saldos_partidas(db)

        if actualizar_saldo:
            db.refresh(nueva_partida)
            cuota.saldo_actual = nueva_partida.saldo

    db.commit()
    db.refresh(cuota)

    return cuota

def cobro_mensual(db: Session, fecha: date, items: List[schemas.CobroMensualItem], current_user_id: int):
    """
    Registra el cobro del mes para varios árbitros en una sola transacción.
    Cada árbitro va en su propio SAVEPOINT: si uno falla, no afecta al resto.
    Los saldos se recalculan una sola vez al final.
    """
    ok: List[Dict[str, Any]] = []
    errores: List[Dict[str, Any]] = []
    para_email: List[Dict[str, Any]] = []

    for item in items:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == item.usuario_id).first()
        nombre = usuario.nombre if usuario else f"Usuario {item.usuario_id}"

        if not usuario:
            errores.append({"usuario_id": item.usuario_id, "nombre": nombre, "error": "Usuario no encontrado"})
            continue
        if not item.monto or item.monto <= 0:
            errores.append({"usuario_id": item.usuario_id, "nombre": nombre, "error": "Monto inválido"})
            continue

        try:
            with db.begin_nested():
                cuota = db.query(models.Cuota).filter(
                    models.Cuota.usuario_id == item.usuario_id,
                    extract('year', models.Cuota.fecha) == fecha.year,
                    extract('month', models.Cuota.fecha) == fecha.month,
                ).first()

                if cuota and cuota.pagado:
                    raise ValueError("La cuota del mes ya está pagada")

                if not cuota:
                    cuota = models.Cuota(
                        usuario_id=item.usuario_id,
                        fecha=fecha,
                        monto=Decimal(str(item.monto)),
                        pagado=False,
                        monto_pagado=0,
                        nro_comprobante=siguiente_nro_comprobante(db),
                        creado_por_usuario_id=current_user_id,
                    )
                    db.add(cuota)
                    db.flush()
                    db.add(models.Auditoria(
                        usuario_id=current_user_id,
                        accion="crear",
                        tabla_afectada="cuota",
                        registro_id=cuota.id,
                        fecha=datetime.now(),
                        detalles="Creación de registro en cuota (cobro mensual)",
                    ))

                monto = Decimal(str(item.monto))
                cuota.pagado = True
                cuota.monto_pagado = monto
                cuota.pagado_por_usuario_id = current_user_id
                cuota.fecha_pago = datetime.now()
                cuota.monto_total_pendiente = None
                cuota.cuotas_pendientes = None
                cuota.fecha_primera_deuda = None
                cuota.meses_atraso = None

                db.add(models.Partida(
                    fecha=datetime.now().date(),
                    cuenta="INGRESOS",
                    detalle=f"Pago de cuota de {nombre}",
                    ingreso=monto,
                    egreso=0,
                    saldo=0,
                    usuario_id=current_user_id,
                    monto=monto,
                    tipo="ingreso",
                    recibo_factura=f"C.S.-{cuota.nro_comprobante}",
                ))
                db.flush()

            ok.append({"usuario_id": item.usuario_id, "nombre": nombre, "cuota_id": cuota.id})
            if usuario.email:
                para_email.append({"cuota_id": cuota.id, "email": usuario.email})
        except Exception as e:
            errores.append({"usuario_id": item.usuario_id, "nombre": nombre, "error": str(e)})

    # Recalcula saldos UNA sola vez y hace el commit final de toda la transacción
    if ok:
        recalcular_saldos_partidas(db)
    else:
        db.commit()

    return {"ok": ok, "errores": errores, "para_email": para_email}


def get_cuota(db: Session, cuota_id: int):
    return db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()

def get_cuotas(db: Session, skip: int = 0, limit: int = 100, pagado: Optional[bool] = None):
    query = db.query(models.Cuota).options(joinedload(models.Cuota.usuario))

    if pagado is not None:
        query = query.filter(models.Cuota.pagado == pagado)

    cuotas = query.order_by(desc(models.Cuota.fecha)).offset(skip).limit(limit).all()

    cuotas_procesadas = []
    usuarios_cuotas = {}
    fecha_actual = datetime.now().date()

    for cuota in cuotas:
        if not cuota.pagado:
            if cuota.usuario_id not in usuarios_cuotas:
                usuarios_cuotas[cuota.usuario_id] = {
                    'cuotas': [],
                    'monto_total': 0,
                    'fecha_primera': cuota.fecha
                }

            usuarios_cuotas[cuota.usuario_id]['cuotas'].append(cuota)
            usuarios_cuotas[cuota.usuario_id]['monto_total'] += cuota.monto

            if cuota.fecha < usuarios_cuotas[cuota.usuario_id]['fecha_primera']:
                usuarios_cuotas[cuota.usuario_id]['fecha_primera'] = cuota.fecha

    for cuota in cuotas:
        info_usuario = usuarios_cuotas.get(cuota.usuario_id, {})
        meses_atraso = (fecha_actual.year - cuota.fecha.year) * 12 + (fecha_actual.month - cuota.fecha.month)

        cuota_dict = {
            "id": cuota.id,
            "fecha": cuota.fecha,
            "monto": cuota.monto,
            "pagado": cuota.pagado,
            "usuario_id": cuota.usuario_id,
            "usuario": {
                "id": cuota.usuario.id,
                "nombre": str(cuota.usuario.nombre)
            } if cuota.usuario else None,
            "meses_atraso": meses_atraso if not cuota.pagado else None,
            "cuotas_pendientes": len(info_usuario.get('cuotas', [])) if not cuota.pagado else None,
            "fecha_primera_deuda": info_usuario.get('fecha_primera') if not cuota.pagado else None
        }

        cuotas_procesadas.append(cuota_dict)

    return cuotas_procesadas

def get_cuotas_by_usuario(db: Session, usuario_id: int, pagado: Optional[bool] = None):
    query = db.query(models.Cuota).filter(models.Cuota.usuario_id == usuario_id)
    
    if pagado is not None:
        query = query.filter(models.Cuota.pagado == pagado)
    
    cuotas = query.order_by(desc(models.Cuota.fecha)).all()
    cuotas_pendientes = [cuota for cuota in cuotas if not cuota.pagado]
    fecha_actual = datetime.now().date()
    
    if cuotas_pendientes:
        monto_total_pendiente = sum(cuota.monto for cuota in cuotas_pendientes)
        fecha_primera_deuda = min(cuota.fecha for cuota in cuotas_pendientes)
        meses_atraso = (fecha_actual.year - fecha_primera_deuda.year) * 12 + (fecha_actual.month - fecha_primera_deuda.month)
        
        for cuota in cuotas_pendientes:
            cuota.monto_total_pendiente = float(monto_total_pendiente)
            cuota.cuotas_pendientes = len(cuotas_pendientes)
            cuota.fecha_primera_deuda = fecha_primera_deuda
            cuota.meses_atraso = meses_atraso
    
    return cuotas

@audit_trail("cuota")
def update_cuota(db: Session, cuota_id: int, cuota_update: schemas.CuotaUpdate, current_user_id: Optional[int] = None):
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    
    for key, value in cuota_update.dict(exclude_unset=True).items():
        setattr(db_cuota, key, value)
    
    db.commit()
    db.refresh(db_cuota)
    return db_cuota

def reenviar_recibo_cuota(db: Session, cuota_id: int, email: Optional[str] = None, current_user_id: Optional[int] = None):
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        return {"success": False, "message": "Cuota no encontrada"}
    
    if not db_cuota.pagado:
        return {"success": False, "message": "La cuota no ha sido pagada aún"}
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cuota.usuario_id).first()
    recipient_email = email or (usuario.email if usuario else None)
    
    if not recipient_email:
        return {"success": False, "message": "No hay email destinatario disponible"}
    
    email_config = get_active_email_config(db)
    if not email_config:
        return {"success": False, "message": "No hay configuración de email activa"}
    
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
    
    if success:
        db_cuota.email_enviado = True
        db_cuota.fecha_envio_email = datetime.now()
        db_cuota.email_destinatario = recipient_email
        db.commit()
        db.refresh(db_cuota)
        return {"success": True, "message": "Recibo de cuota enviado exitosamente"}
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


# ==========================================
# Funciones CRUD para Partidas
# ==========================================
@audit_trail("partidas")
def create_partida(db: Session, partida: schemas.PartidaCreate, current_user_id: Optional[int] = None):
    db_partida = models.Partida(**partida.dict(exclude={'saldo'}), saldo=0)
    
    if current_user_id:
        db_partida.usuario_id = current_user_id
    
    db.add(db_partida)
    db.commit()
    db.refresh(db_partida)

    recalcular_saldos_partidas(db)
    db.refresh(db_partida)

    return db_partida

@audit_trail("partidas")
def update_partida(db: Session, partida_id: int, partida_update: schemas.PartidaUpdate, current_user_id: Optional[int] = None):
    db_partida = db.query(models.Partida).filter(models.Partida.id == partida_id).first()
    if not db_partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    update_data = partida_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_partida, key, value)
    
    db.commit()
    db.refresh(db_partida)

    recalcular_saldos_partidas(db)
    db.refresh(db_partida)

    return db_partida

@audit_trail("partidas")
def delete_partida(db: Session, partida_id: int, current_user_id: Optional[int] = None):
    db_partida = db.query(models.Partida).filter(models.Partida.id == partida_id).first()
    if not db_partida:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    db.delete(db_partida)
    db.commit()

    recalcular_saldos_partidas(db)
    return {"message": "Partida eliminada exitosamente"}


# ==========================================
# Funciones CRUD para Categorías
# ==========================================
def create_categoria(db: Session, categoria: schemas.CategoriaCreate):
    max_id = db.query(func.max(models.Categoria.id)).scalar() or 0
    db_categoria = models.Categoria(
        id=max_id + 1,
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


# ==========================================
# Consultas Financieras y Reportes
# ==========================================
def get_balance(db: Session, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None):
    query = db.query(models.Partida)
    
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
            "ingresos": float(ingresos),
            "egresos": float(egresos),
            "balance": float(ingresos) - float(egresos),
        })
    
    return {"anio": year_to_query, "datos": result}

def get_nombre_mes(month_number: int) -> str:
    nombres = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    return nombres.get(month_number, "")

def get_partidas_por_mes(db: Session, mes: int, anio: int):
    return (
        db.query(models.Partida)
        .filter(
            extract('month', models.Partida.fecha) == mes,
            extract('year', models.Partida.fecha) == anio,
        )
        .order_by(models.Partida.fecha, models.Partida.id)
        .all()
    )


# ==========================================
# Auditoría y Auxiliares
# ==========================================
@audit_trail("partidas")
def get_partida(
    db: Session, 
    partida_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 100, 
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    cuenta: Optional[str] = None,
    current_user_id: Optional[int] = None
):
    if partida_id:
        return db.query(models.Partida).filter(models.Partida.id == partida_id).first()
    
    query = db.query(models.Partida)
    
    if fecha_desde:
        query = query.filter(models.Partida.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(models.Partida.fecha <= fecha_hasta)
    if tipo:
        query = query.filter(models.Partida.tipo == tipo)
    if cuenta:
        query = query.filter(models.Partida.cuenta == cuenta)
    
    partidas = query.order_by(
        models.Partida.fecha.desc(), 
        models.Partida.id.desc()
    ).offset(skip).limit(limit).all()

    for partida in partidas:
        auditoria = db.query(models.Auditoria)\
            .filter(
                models.Auditoria.tabla_afectada == 'partidas', 
                models.Auditoria.registro_id == partida.id
            )\
            .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
            .order_by(models.Auditoria.fecha.desc())\
            .first()
        
        partida.usuario_auditoria = auditoria.usuario.nombre if auditoria and auditoria.usuario else 'Sin registro'
        
        if partida.fecha and hasattr(partida.fecha, 'tzinfo'):
            tz_arg = timezone(timedelta(hours=-3))
            fecha_local = partida.fecha.astimezone(tz_arg) if partida.fecha.tzinfo else partida.fecha.replace(tzinfo=timezone.utc).astimezone(tz_arg)
            partida.fecha = fecha_local.date()
        elif partida.fecha and hasattr(partida.fecha, 'date'):
            partida.fecha = partida.fecha.date()
    
    return partidas

def get_cuotas_pendientes(db: Session):
    try:
        today = date.today()
        query_result = db.query(
            models.Cuota.id.label('cuota_id'),
            models.Usuario.id.label('usuario_id'),
            models.Usuario.nombre.label('nombre_usuario'),
            models.Cuota.monto,
            models.Cuota.fecha
        ).join(
            models.Usuario, models.Cuota.usuario_id == models.Usuario.id
        ).filter(
            and_(
                models.Cuota.pagado.is_(False),
                cast(models.Cuota.fecha, Date) < today
            )
        ).all()
        
        result = []
        for row in query_result:
            fecha_cuota = row.fecha
            if isinstance(fecha_cuota, datetime):
                fecha_cuota = fecha_cuota.date()
            elif isinstance(fecha_cuota, str):
                fecha_cuota = datetime.strptime(fecha_cuota, "%Y-%m-%d").date()
            
            dias_vencido = (today - fecha_cuota).days
            
            result.append({
                "cuota_id": row.cuota_id,
                "usuario_id": row.usuario_id,
                "nombre_usuario": row.nombre_usuario,
                "monto": float(row.monto) if row.monto else 0.0,
                "fecha": fecha_cuota.strftime("%Y-%m-%d"),
                "dias_vencido": dias_vencido
            })
        return result
    except Exception as e:
        print(f"Error en get_cuotas_pendientes: {e}")
        return []

def recalcular_saldos_partidas(db: Session):
    """Recalcula los saldos de todas las partidas en orden cronológico de forma rápida"""
    partidas = db.query(models.Partida).order_by(
        models.Partida.fecha,
        models.Partida.id
    ).all()
    
    if not partidas:
        return {"message": "No hay partidas para recalcular", "partidas_actualizadas": 0}

    saldo_actual = 0.0
    total_ingresos_sumados = 0.0
    total_egresos_sumados = 0.0

    # Actualizar saldos en la sesión local sin hacer commit por cada iteración
    for partida in partidas:
        ingreso_val = float(partida.ingreso or 0)
        egreso_val = float(partida.egreso or 0)

        if partida.tipo == "ingreso":
            saldo_actual += ingreso_val
            total_ingresos_sumados += ingreso_val
        elif partida.tipo == "egreso":
            saldo_actual -= egreso_val
            total_egresos_sumados += egreso_val

        partida.saldo = saldo_actual

    # UN SOLO commit para persistir todos los cambios de un solo golpe
    db.commit()

    return {
        "message": "Saldos recalculados correctamente",
        "partidas_actualizadas": len(partidas),
        "total_ingresos": total_ingresos_sumados,
        "total_egresos": total_egresos_sumados,
        "saldo_final": saldo_actual,
    }

def get_auditoria(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    tabla_afectada: Optional[str] = None, 
    usuario_id: Optional[int] = None,
    fecha_desde: Optional[str] = None, 
    fecha_hasta: Optional[str] = None
):
    query = db.query(models.Auditoria)
    
    if tabla_afectada:
        query = query.filter(models.Auditoria.tabla_afectada == tabla_afectada)
    if usuario_id:
        query = query.filter(models.Auditoria.usuario_id == usuario_id)
    if fecha_desde:
        query = query.filter(models.Auditoria.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(models.Auditoria.fecha <= fecha_hasta)
    
    return query.order_by(desc(models.Auditoria.fecha)).offset(skip).limit(limit).all()