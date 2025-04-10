from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.orm import Session
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Importar tus propios módulos
from database import get_db
from auth import authenticate_user
import schemas
import crud
import models
from email_service import EmailService

# Crear un router separado
router = APIRouter()

# Endpoint para crear configuración de email
@router.post("/email-config/", response_class=JSONResponse)
def create_email_config(
    config: schemas.EmailConfigCreate, 
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    # Verificar que el usuario tenga permisos
    if current_user.rol_id != 1:  # Asumiendo que rol_id 1 es admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para esta acción",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = crud.create_email_config(db=db, config_data=config.dict())
    return {"id": result.id, "success": True, "message": "Configuración creada exitosamente"}

# Endpoint para obtener configuración activa
@router.get("/email-config/active", response_class=JSONResponse)
def get_active_email_config(
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    config = crud.get_active_email_config(db=db)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay configuración de email activa",
        )
    
    # Convertir manualmente a diccionario para evitar problemas de serialización
    return {
        "id": config.id,
        "smtp_server": config.smtp_server,
        "smtp_port": config.smtp_port,
        "smtp_username": config.smtp_username,
        # No devolver la contraseña por seguridad
        "email_from": config.email_from,
        "is_active": config.is_active
    }

# Endpoint para actualizar configuración
@router.put("/email-config/{config_id}", response_class=JSONResponse)
def update_email_config(
    config_id: int, 
    config: schemas.EmailConfigUpdate, 
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    # Verificar que el usuario tenga permisos
    if current_user.rol_id != 1:  # Asumiendo que rol_id 1 es admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para esta acción",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    updated_config = crud.update_email_config(db=db, config_id=config_id, config_data=config.dict(exclude_unset=True))
    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de email no encontrada",
        )
    
    return {"id": updated_config.id, "success": True, "message": "Configuración actualizada exitosamente"}

# Endpoint para reenviar recibo
@router.post("/cobranzas/{cobranza_id}/reenviar-recibo", response_class=JSONResponse)
def reenviar_recibo_cobranza(
    cobranza_id: int, 
    email: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    # Obtener la cobranza
    db_cobranza = db.query(models.Cobranza).filter(models.Cobranza.id == cobranza_id).first()
    if not db_cobranza:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cobranza no encontrada"
        )
    
    # Obtener usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cobranza.usuario_id).first()
    
    # Determinar el email a usar
    recipient_email = email if email else (usuario.email if usuario else None)
    
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay email destinatario disponible"
        )
    
    # Obtener configuración de email
    email_config = crud.get_active_email_config(db=db)
    if not email_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay configuración de email activa"
        )
    
    # Crear servicio de email
    email_service = EmailService(
        smtp_server=email_config.smtp_server,
        smtp_port=email_config.smtp_port,
        username=email_config.smtp_username,
        password=email_config.smtp_password,
        sender_email=email_config.email_from
    )
    
    # Enviar el recibo
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
        return {"success": True, "message": "Recibo enviado exitosamente"}
    else:
        return {"success": False, "message": message}

# Endpoint para probar configuración de email
@router.post("/email-test", response_class=JSONResponse)
def test_email(
    email: str, 
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    # Obtener configuración activa
    email_config = crud.get_active_email_config(db=db)
    if not email_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay configuración de email activa"
        )
    
    try:
        # Crear mensaje de prueba
        msg = MIMEMultipart()
        msg['From'] = email_config.email_from
        msg['To'] = email
        msg['Subject'] = "Prueba de Configuración de Email - UARC"
        
        body = """
        Este es un mensaje de prueba para verificar la configuración de email.
        
        Si está recibiendo este mensaje, la configuración es correcta.
        
        Unidad de Árbitros de Río Cuarto
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Enviar email
        with smtplib.SMTP(email_config.smtp_server, email_config.smtp_port) as server:
            server.starttls()
            server.login(email_config.smtp_username, email_config.smtp_password)
            server.send_message(msg)
        
        return {"success": True, "message": "Email de prueba enviado exitosamente"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    

    # Endpoint para reenviar orden de pago
@router.post("/pagos/{pago_id}/reenviar-orden", response_class=JSONResponse)
def reenviar_orden_pago_endpoint(
    pago_id: int, 
    email: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    # Obtener el pago
    db_pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not db_pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Obtener usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_pago.usuario_id).first()
    
    # Determinar el email a usar
    recipient_email = email if email else (usuario.email if usuario else None)
    
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay email destinatario disponible"
        )
    
    # Obtener configuración de email
    email_config = crud.get_active_email_config(db=db)
    if not email_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay configuración de email activa"
        )
    
    # Crear servicio de email
    from email_service import EmailService
    email_service = EmailService(
        smtp_server=email_config.smtp_server,
        smtp_port=email_config.smtp_port,
        username=email_config.smtp_username,
        password=email_config.smtp_password,
        sender_email=email_config.email_from
    )
    
    # Enviar la orden de pago
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
        return {"success": True, "message": "Orden de pago enviada exitosamente"}
    else:
        return {"success": False, "message": message}
    
# Endpoint en email_routes.py
@router.post("/cuotas/{cuota_id}/reenviar-recibo", response_class=JSONResponse)
def reenviar_recibo_cuota_endpoint(
    cuota_id: int, 
    email: Optional[str] = None, 
    db: Session = Depends(get_db), 
    current_user: schemas.Usuario = Depends(authenticate_user)
):
    # Obtener la cuota
    db_cuota = db.query(models.Cuota).filter(models.Cuota.id == cuota_id).first()
    if not db_cuota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuota no encontrada"
        )
    
    if not db_cuota.pagado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuota no ha sido pagada aún"
        )
    
    # Obtener usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.id == db_cuota.usuario_id).first()
    
    # Determinar el email a usar
    recipient_email = email if email else (usuario.email if usuario else None)
    
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay email destinatario disponible"
        )
    
    # Obtener configuración de email
    email_config = crud.get_active_email_config(db=db)
    if not email_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay configuración de email activa"
        )
    
    # Crear servicio de email
    from email_service import EmailService
    email_service = EmailService(
        smtp_server=email_config.smtp_server,
        smtp_port=email_config.smtp_port,
        username=email_config.smtp_username,
        password=email_config.smtp_password,
        sender_email=email_config.email_from
    )
    
    # Enviar el recibo
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
        return {"success": True, "message": "Recibo de cuota enviado exitosamente"}
    else:
        return {"success": False, "message": message}    