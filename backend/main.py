from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Optional
from fastapi import Request, HTTPException, status
from database import SessionLocal
from jose import JWTError, jwt
from auth import get_current_user

import models
import schemas
import crud
from database import engine, get_db
from auth import authenticate_user, create_access_token, get_current_active_user, is_admin, is_tesorero
from config import settings

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para sistema de tesorería de asociación de árbitros",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Endpoint raíz
@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Tesorería"}

# Endpoint de autenticación
@app.post(f"{settings.API_PREFIX}/auth/login", response_model=schemas.Token, tags=["Auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Rutas de Usuarios
@app.post(f"{settings.API_PREFIX}/usuarios", response_model=schemas.Usuario, tags=["Usuarios"])
def create_usuario(
    usuario: schemas.UsuarioCreate, 
    db: Session = Depends(get_db), 
    
):
    db_user = crud.get_usuario_by_email(db, email=usuario.email)
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado") 
    return crud.create_usuario(
        db=db, 
        usuario=usuario, 
    
    )

@app.get(f"{settings.API_PREFIX}/usuarios", response_model=List[schemas.UsuarioDetalle], tags=["Usuarios"])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    usuarios = crud.get_usuarios(db, skip=skip, limit=limit)
    return usuarios

@app.get(f"{settings.API_PREFIX}/usuarios/me", response_model=schemas.UsuarioDetalle, tags=["Usuarios"])
def read_user_me(current_user: models.Usuario = Depends(get_current_active_user)):
    return current_user

@app.get(f"{settings.API_PREFIX}/usuarios/{{usuario_id}}", response_model=schemas.UsuarioDetalle, tags=["Usuarios"])
def read_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@app.put(f"{settings.API_PREFIX}/usuarios/{{usuario_id}}", response_model=schemas.Usuario, tags=["Usuarios"])
def update_usuario(
    usuario_id: int, 
    usuario: schemas.UsuarioUpdate, 
    db: Session = Depends(get_db), 
    
):
    return crud.update_usuario(
        db=db, 
        usuario_id=usuario_id, 
        usuario_update=usuario, 
    
    )

@app.delete(f"{settings.API_PREFIX}/usuarios/{{usuario_id}}", tags=["Usuarios"])
def delete_usuario(
    usuario_id: int, 
    db: Session = Depends(get_db), 
    
):
    return crud.delete_usuario(
        db=db, 
        usuario_id=usuario_id, 
        
    )

# Rutas de Roles
@app.post(f"{settings.API_PREFIX}/roles", response_model=schemas.Rol, tags=["Roles"])
def create_rol(
    rol: schemas.RolCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_admin)
):
    return crud.create_rol(
        db=db, 
        rol=rol, 
        current_user_id=current_user.id
    )

@app.get(f"{settings.API_PREFIX}/roles", response_model=List[schemas.Rol], tags=["Roles"])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles

@app.get(f"{settings.API_PREFIX}/roles/{{rol_id}}", response_model=schemas.Rol, tags=["Roles"])
def read_rol(rol_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    db_rol = crud.get_rol(db, rol_id=rol_id)
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return db_rol

@app.put(f"{settings.API_PREFIX}/roles/{{rol_id}}", response_model=schemas.Rol, tags=["Roles"])
def update_rol(
    rol_id: int, 
    rol: schemas.RolCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_admin)
):
    return crud.update_rol(
        db=db, 
        rol_id=rol_id, 
        rol_update=rol, 
        current_user_id=current_user.id
    )

@app.delete(f"{settings.API_PREFIX}/roles/{{rol_id}}", tags=["Roles"])
def delete_rol(
    rol_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_admin)
):
    return crud.delete_rol(
        db=db, 
        rol_id=rol_id, 
        current_user_id=current_user.id
    )

# Retenciones
@app.post(f"{settings.API_PREFIX}/retenciones", response_model=schemas.Retencion, tags=["Retenciones"])
def crear_retencion(
    retencion: schemas.RetencionCreate, 
    db: Session = Depends(get_db)
):
    return crud.create_retencion(
        db=db, 
        retencion=retencion
    )

@app.get(f"{settings.API_PREFIX}/retenciones", response_model=List[schemas.Retencion], tags=["Retenciones"])
def get_retenciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    retenciones = crud.get_retenciones(db, skip=skip, limit=limit)
    return retenciones

@app.delete(f"{settings.API_PREFIX}/retenciones/{{retencion_id}}", tags=["Retenciones"])
def delete_retencion(
    retencion_id: int, 
    db: Session = Depends(get_db)
):
    return crud.delete_retencion(
        db=db, 
        retencion_id=retencion_id
    )


@app.put(f"{settings.API_PREFIX}/retenciones/{{retencion_id}}", response_model=schemas.Retencion, tags=["Retenciones"])
def update_retencion(
    retencion_id: int, 
    retencion: schemas.RetencionUpdate, 
    db: Session = Depends(get_db)
):
    return crud.update_retencion(
        db=db, 
        retencion_id=retencion_id, 
        retencion_update=retencion
    )



# Rutas de Pagos
@app.post(f"{settings.API_PREFIX}/pagos", response_model=schemas.Pago, tags=["Pagos"])
def create_pago(
    pago: schemas.PagoCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    # Validar que el usuario exista
    usuario = crud.get_usuario(db, usuario_id=pago.usuario_id)
    if not usuario:

        raise HTTPException(status_code=404, detail="Usuario no encontrado")    
       

        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
  
    return crud.create_pago(
        db=db, 
        pago=pago, 
        current_user_id=current_user.id
    )

@app.get(f"{settings.API_PREFIX}/pagos", response_model=List[schemas.PagoDetalle], tags=["Pagos"])
def read_pagos(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Obtener pagos - MODIFICADO: quitado el parámetro current_user_id
    pagos = crud.get_pagos(db, skip=skip, limit=limit)
    
    # Obtener registros de auditoría para estos pagos
    pago_ids = [pago.id for pago in pagos]
    auditorias = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'pagos', 
            models.Auditoria.registro_id.in_(pago_ids)
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .all()
    
    # Crear un diccionario de mapeo de auditorías (última acción por registro)
    auditoria_map = {}
    for a in auditorias:
        if str(a.registro_id) not in auditoria_map:
            auditoria_map[str(a.registro_id)] = a.usuario.nombre if a.usuario else 'Sin usuario'
    
    # Añadir información de auditoría a cada pago
    for pago in pagos:
        pago.usuario_auditoria = auditoria_map.get(str(pago.id), 'Sin registro')
    
    return pagos

@app.get(f"{settings.API_PREFIX}/pagos/{{pago_id}}", response_model=schemas.PagoDetalle, tags=["Pagos"])
def read_pago(pago_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    db_pago = crud.get_pago(db, pago_id=pago_id, current_user_id=current_user.id)
    if db_pago is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return db_pago

@app.put(f"{settings.API_PREFIX}/pagos/{{pago_id}}", response_model=schemas.Pago, tags=["Pagos"])
def update_pago(
    pago_id: int, 
    pago: schemas.PagoUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.update_pago(
        db=db, 
        pago_id=pago_id, 
        pago_update=pago, 
        current_user_id=current_user.id
    )

@app.delete(f"{settings.API_PREFIX}/pagos/{{pago_id}}", tags=["Pagos"])
def delete_pago(
    pago_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.delete_pago(
        db=db, 
        pago_id=pago_id, 
        current_user_id=current_user.id
    )

# Rutas de Cobranzas
@app.post(f"{settings.API_PREFIX}/cobranzas", response_model=schemas.Cobranza, tags=["Cobranzas"])
def create_cobranza(
    cobranza: schemas.CobranzaCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    # Validar que el usuario exista
    usuario = crud.get_usuario(db, usuario_id=cobranza.usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return crud.create_cobranza(
        db=db, 
        cobranza=cobranza, 
        current_user_id=current_user.id
    )

@app.get(f"{settings.API_PREFIX}/cobranzas", response_model=List[schemas.CobranzaDetalle], tags=["Cobranzas"])
def read_cobranzas(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Obtener cobranzas
    cobranzas = crud.get_cobranzas(db, skip=skip, limit=limit)
    
    # Obtener registros de auditoría para estas cobranzas
    cobranza_ids = [cobranza.id for cobranza in cobranzas]
    auditorias = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'cobranza', 
            models.Auditoria.registro_id.in_(cobranza_ids)
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .all()
    
    # Crear un diccionario de mapeo de auditorías (última acción por registro)
    auditoria_map = {}
    for a in auditorias:
        if str(a.registro_id) not in auditoria_map:
            auditoria_map[str(a.registro_id)] = a.usuario.nombre if a.usuario else 'Sin usuario'
    
    # Añadir información de auditoría a cada cobranza
    for cobranza in cobranzas:
        cobranza.usuario_auditoria = auditoria_map.get(str(cobranza.id), 'Sin registro')
    
    return cobranzas

@app.get(f"{settings.API_PREFIX}/cobranzas/{{cobranza_id}}", response_model=schemas.CobranzaDetalle, tags=["Cobranzas"])
def read_cobranza(
    cobranza_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Obtener cobranza
    db_cobranza = crud.get_cobranza(db, cobranza_id=cobranza_id)
    if db_cobranza is None:
        raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    # Obtener registro de auditoría para esta cobranza
    auditoria = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'cobranza', 
            models.Auditoria.registro_id == cobranza_id
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .first()
    
    # Añadir información de auditoría a la cobranza
    db_cobranza.usuario_auditoria = auditoria.usuario.nombre if auditoria and auditoria.usuario else 'Sin registro'
    
    return db_cobranza

@app.put(f"{settings.API_PREFIX}/cobranzas/{{cobranza_id}}", response_model=schemas.Cobranza, tags=["Cobranzas"])
def update_cobranza(
    cobranza_id: int, 
    cobranza: schemas.CobranzaUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.update_cobranza(
        db=db, 
        cobranza_id=cobranza_id, 
        cobranza_update=cobranza, 
        current_user_id=current_user.id
    )

@app.delete(f"{settings.API_PREFIX}/cobranzas/{{cobranza_id}}", tags=["Cobranzas"])
def delete_cobranza(
    cobranza_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.delete_cobranza(
        db=db, 
        cobranza_id=cobranza_id, 
        current_user_id=current_user.id
    )

# Rutas de Cuotas
@app.post(f"{settings.API_PREFIX}/cuotas", response_model=schemas.Cuota, tags=["Cuotas"])
def create_cuota(
    cuota: schemas.CuotaCreate, 
    no_generar_movimiento: bool = True,  # Agregar este parámetro
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    # Validar que el usuario exista si se proporciona usuario_id
    if cuota.usuario_id:
        usuario = crud.get_usuario(db, usuario_id=cuota.usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return crud.create_cuota(
        db=db, 
        cuota=cuota, 
        current_user_id=current_user.id,
        no_generar_movimiento=no_generar_movimiento  # Agregar este parámetro
    )

from fastapi.responses import JSONResponse

@app.get(f"{settings.API_PREFIX}/cuotas", tags=["Cuotas"])
def read_cuotas(
    skip: int = 0, 
    limit: int = 100, 
    pagado: Optional[bool] = None, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    cuotas = crud.get_cuotas(db, skip=skip, limit=limit, pagado=pagado)

    from datetime import datetime

    for cuota in cuotas:
        if not cuota.pagado:
            meses_atraso = (
                (datetime.now().date().year - cuota.fecha.year) * 12 + 
                (datetime.now().date().month - cuota.fecha.month)
            )
            if datetime.now().date().day < cuota.fecha.day:
                meses_atraso -= 1
            cuota.meses_atraso = max(0, meses_atraso)

    cuota_ids = [cuota.id for cuota in cuotas]
    auditorias = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'cuota', 
            models.Auditoria.registro_id.in_(cuota_ids)
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .all()

    auditoria_map = {
        str(a.registro_id): a.usuario.nombre if a.usuario else 'Sin usuario'
        for a in auditorias if str(a.registro_id) not in auditoria_map
    }

    for cuota in cuotas:
        cuota.usuario_auditoria = auditoria_map.get(str(cuota.id), 'Sin registro')

    return JSONResponse(content=[cuota.__dict__ for cuota in cuotas])


@app.get(f"{settings.API_PREFIX}/cuotas/usuario/{{usuario_id}}", response_model=List[schemas.CuotaDetalle], tags=["Cuotas"])
def read_cuotas_by_usuario(
    usuario_id: int, 
    pagado: Optional[bool] = None, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Validar que el usuario exista
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener cuotas del usuario
    cuotas = crud.get_cuotas_by_usuario(db, usuario_id=usuario_id, pagado=pagado)
    
    # Calcular meses de atraso para cada cuota no pagada
    from datetime import datetime
    
    for cuota in cuotas:
        if not cuota.pagado:
            # Calcular meses de atraso
            meses_atraso = (
                (datetime.now().date().year - cuota.fecha.year) * 12 + 
                (datetime.now().date().month - cuota.fecha.month)
            )
            
            # Ajustar si el día actual es menor que el día de la cuota
            if datetime.now().date().day < cuota.fecha.day:
                meses_atraso -= 1
            
            # Asignar meses de atraso
            cuota.meses_atraso = max(0, meses_atraso)
    
    # Obtener registros de auditoría para estas cuotas
    cuota_ids = [cuota.id for cuota in cuotas]
    auditorias = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'cuota', 
            models.Auditoria.registro_id.in_(cuota_ids)
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .all()
    
    # Crear un diccionario de mapeo de auditorías (última acción por registro)
    auditoria_map = {}
    for a in auditorias:
        if str(a.registro_id) not in auditoria_map:
            auditoria_map[str(a.registro_id)] = a.usuario.nombre if a.usuario else 'Sin usuario'
    
    # Añadir información de auditoría a cada cuota
    for cuota in cuotas:
        cuota.usuario_auditoria = auditoria_map.get(str(cuota.id), 'Sin registro')
    
    return cuotas

@app.get(f"{settings.API_PREFIX}/cuotas/{{cuota_id}}", response_model=schemas.CuotaDetalle, tags=["Cuotas"])
def read_cuota(
    cuota_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Obtener cuota
    db_cuota = crud.get_cuota(db, cuota_id=cuota_id)
    if db_cuota is None:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
    
    # Obtener registro de auditoría para esta cuota
    auditoria = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'cuota', 
            models.Auditoria.registro_id == cuota_id
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .first()
    
    # Añadir información de auditoría a la cuota
    db_cuota.usuario_auditoria = auditoria.usuario.nombre if auditoria and auditoria.usuario else 'Sin registro'
    
    return db_cuota
@app.put(f"{settings.API_PREFIX}/cuotas/{{cuota_id}}", response_model=schemas.Cuota, tags=["Cuotas"])
def update_cuota(
    cuota_id: int, 
    cuota: schemas.CuotaUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.update_cuota(
        db=db, 
        cuota_id=cuota_id, 
        cuota_update=cuota, 
        current_user_id=current_user.id
    )

@app.put(f"{settings.API_PREFIX}/cuotas/{{cuota_id}}/pagar", response_model=schemas.Cuota, tags=["Cuotas"])
def pagar_cuota(
    cuota_id: int, 
    monto_pagado: float, 
    generar_movimiento: bool = True,  # Agregar este parámetro
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.pagar_cuota(
        db=db, 
        cuota_id=cuota_id, 
        monto_pagado=monto_pagado, 
        current_user_id=current_user.id,
        generar_movimiento=generar_movimiento  # Agregar este parámetro
    )

@app.delete(f"{settings.API_PREFIX}/cuotas/{{cuota_id}}", tags=["Cuotas"])
def delete_cuota(
    cuota_id: int, 
    db: Session = Depends(get_db), 
    
):
    return crud.delete_cuota(
        db=db, 
        cuota_id=cuota_id, 
        
    )

# Rutas de Partidas
@app.post(f"{settings.API_PREFIX}/partidas", response_model=schemas.Partida, tags=["Partidas"])
def create_partida(
    partida: schemas.PartidaCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    # Validaciones
    usuario = crud.get_usuario(db, usuario_id=partida.usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if partida.cobranza_id:
        cobranza = crud.get_cobranza(db, cobranza_id=partida.cobranza_id)
        if not cobranza:
            raise HTTPException(status_code=404, detail="Cobranza no encontrada")
    
    if partida.pago_id:
        pago = crud.get_pago(db, pago_id=partida.pago_id)
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    return crud.create_partida(
        db=db, 
        partida=partida,
        current_user_id=current_user.id
    )

@app.get(f"{settings.API_PREFIX}/partidas", response_model=List[schemas.PartidaDetalle], tags=["Partidas"])
def read_partidas(
    skip: int = 0, 
    limit: int = 100, 
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    cuenta: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_active_user)
):
    # Obtener partidas
    partidas = crud.get_partida(
        db, 
        skip=skip, 
        limit=limit, 
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo=tipo,
        cuenta=cuenta
    )
    
    # Obtener registros de auditoría para estas partidas
    partida_ids = [partida.id for partida in partidas]
    auditorias = db.query(models.Auditoria)\
        .filter(
            models.Auditoria.tabla_afectada == 'partidas', 
            models.Auditoria.registro_id.in_(partida_ids)
        )\
        .join(models.Usuario, models.Auditoria.usuario_id == models.Usuario.id, isouter=True)\
        .order_by(models.Auditoria.fecha.desc())\
        .all()
    
    # Crear un diccionario de mapeo de auditorías 
    auditoria_map = {}
    for a in auditorias:
        if str(a.registro_id) not in auditoria_map:
            auditoria_map[str(a.registro_id)] = a.usuario.nombre if a.usuario else 'Sin usuario'
    
    # Añadir información de auditoría a cada partida
    for partida in partidas:
        partida.usuario_auditoria = auditoria_map.get(str(partida.id), 'Sin registro')
    
    return partidas

@app.get(f"{settings.API_PREFIX}/partidas/{{partida_id}}", response_model=schemas.PartidaDetalle, tags=["Partidas"])
def read_partida(partida_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    db_partida = crud.get_partida(db, partida_id=partida_id, current_user_id=current_user.id)
    if db_partida is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return db_partida

@app.put(f"{settings.API_PREFIX}/partidas/{{partida_id}}", response_model=schemas.Partida, tags=["Partidas"])
def update_partida(
    partida_id: int, 
    partida: schemas.PartidaUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.update_partida(
        db=db, 
        partida_id=partida_id, 
        partida_update=partida, 
        current_user_id=current_user.id
    )

@app.delete(f"{settings.API_PREFIX}/partidas/{{partida_id}}", tags=["Partidas"])
def delete_partida(
    partida_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.delete_partida(
        db=db, 
        partida_id=partida_id, 
        current_user_id=current_user.id
    )

# Rutas de Categorías
@app.post(f"{settings.API_PREFIX}/categorias", response_model=schemas.Categoria, tags=["Categorías"])
def create_categoria(
    categoria: schemas.CategoriaCreate, 
    db: Session = Depends(get_db), 
    
):
    return crud.create_categoria(
        db=db, 
        categoria=categoria, 
    
    )

@app.get(f"{settings.API_PREFIX}/categorias", response_model=List[schemas.Categoria], tags=["Categorías"])
def read_categorias(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), ):
    categorias = crud.get_categorias(db, skip=skip, limit=limit)
    return categorias

@app.get(f"{settings.API_PREFIX}/categorias/{{categoria_id}}", response_model=schemas.Categoria, tags=["Categorías"])
def read_categoria(categoria_id: int, db: Session = Depends(get_db), ):
    db_categoria = crud.get_categoria(db, categoria_id=categoria_id)
    if db_categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

@app.put(f"{settings.API_PREFIX}/categorias/{{categoria_id}}", response_model=schemas.Categoria, tags=["Categorías"])
def update_categoria(
    categoria_id: int, 
    categoria: schemas.CategoriaUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_admin)
):
    return crud.update_categoria(
        db=db, 
        categoria_id=categoria_id, 
        categoria_update=categoria, 
        
    )

@app.delete(f"{settings.API_PREFIX}/categorias/{{categoria_id}}", tags=["Categorías"])
def delete_categoria(
    categoria_id: int, 
    db: Session = Depends(get_db), 
    
):
    return crud.delete_categoria(
        db=db, 
        categoria_id=categoria_id, 
    
    )

# Rutas de Transacciones
@app.post(f"{settings.API_PREFIX}/transacciones", response_model=schemas.Transaccion, tags=["Transacciones"])
def create_transaccion(
    transaccion: schemas.TransaccionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.create_transaccion(
        db=db, 
        transaccion=transaccion, 
        current_user_id=current_user.id
    )

@app.post(f"{settings.API_PREFIX}/transacciones", response_model=schemas.Transaccion, tags=["Transacciones"])
def create_transaccion(
    transaccion: schemas.TransaccionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.create_transaccion(
        db=db, 
        transaccion=transaccion, 
        current_user_id=current_user.id
    )

@app.get(f"{settings.API_PREFIX}/transacciones", response_model=List[schemas.TransaccionDetalle], tags=["Transacciones"])
def read_transacciones(
    skip: int = 0, 
    limit: int = 100, 
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    transacciones = crud.get_transacciones(
        db, 
        skip=skip, 
        limit=limit, 
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo=tipo
    )
    return transacciones

@app.get(f"{settings.API_PREFIX}/transacciones/{{transaccion_id}}", response_model=schemas.TransaccionDetalle, tags=["Transacciones"])
def read_transaccion(transaccion_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_active_user)):
    db_transaccion = crud.get_transaccion(db, transaccion_id=transaccion_id)
    if db_transaccion is None:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return db_transaccion

@app.put(f"{settings.API_PREFIX}/transacciones/{{transaccion_id}}", response_model=schemas.Transaccion, tags=["Transacciones"])
def update_transaccion(
    transaccion_id: int, 
    transaccion: schemas.TransaccionUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.update_transaccion(
        db=db, 
        transaccion_id=transaccion_id, 
        transaccion_update=transaccion, 
        current_user_id=current_user.id
    )

@app.delete(f"{settings.API_PREFIX}/transacciones/{{transaccion_id}}", tags=["Transacciones"])
def delete_transaccion(
    transaccion_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    return crud.delete_transaccion(
        db=db, 
        transaccion_id=transaccion_id, 
        current_user_id=current_user.id
    )

# Nuevo endpoint para recalcular saldos
@app.post(f"{settings.API_PREFIX}/transacciones/recalcular-saldos", tags=["Transacciones"])
def recalcular_saldos(
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    """
    Recalcula los saldos de todas las transacciones
    """
    return crud.recalcular_saldos_transacciones(db)
# Rutas de Auditoría
@app.get(f"{settings.API_PREFIX}/auditoria", response_model=List[schemas.AuditoriaDetalle], tags=["Auditoría"])
def read_auditoria(
    skip: int = 0, 
    limit: int = 100, 
    tabla_afectada: Optional[str] = None,
    usuario_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(is_tesorero)
):
    auditoria = crud.get_auditoria(
        db, 
        skip=skip, 
        limit=limit, 
        tabla_afectada=tabla_afectada,
        usuario_id=usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        create_usuario=current_user.id
    )
    return auditoria

# Endpoints para reportes y estadísticas
@app.get(f"{settings.API_PREFIX}/reportes/balance", tags=["Reportes"])
def get_balance(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] =  None,
    db: Session = Depends(get_db), 
    
):
    return crud.get_balance(db, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta )

@app.get(f"{settings.API_PREFIX}/reportes/ingresos_egresos_mensuales", tags=["Reportes"])
def get_ingresos_egresos_mensuales(
    anio: Optional[int] = None,
    db: Session = Depends(get_db), 
    
):
    return crud.get_ingresos_egresos_mensuales(db, anio=anio)

@app.get(f"{settings.API_PREFIX}/reportes/cuotas_pendientes", tags=["Reportes"])
def get_cuotas_pendientes(
    db: Session = Depends(get_db), 
    
):
    return crud.get_cuotas_pendientes(db,)

# email endpoints
@app.get(f"{settings.API_PREFIX}/email-config/active", response_model=None)
async def get_active_email_config(request: Request):
    db = SessionLocal()
    try:
        # Extraer token manualmente
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verificar token manualmente
        try:
            # Decodificar token sin usar dependencias
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudieron validar las credenciales",
                )
                
            # Obtener usuario directamente con la sesión
            current_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        config = crud.get_active_email_config(db=db)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay configuración de email activa",
            )
        
        return {
            "id": config.id,
            "smtp_server": config.smtp_server,
            "smtp_port": config.smtp_port,
            "smtp_username": config.smtp_username,
            "email_from": config.email_from,
            "is_active": config.is_active
        }
    finally:
        db.close()

@app.put(f"{settings.API_PREFIX}/email-config/{{config_id}}", response_model=None)
async def update_email_config(request: Request, config_id: int, config: schemas.EmailConfigUpdate):
    db = SessionLocal()
    try:
        # Extraer token manualmente
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verificar token manualmente
        try:
            # Decodificar token sin usar dependencias
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudieron validar las credenciales",
                )
                
            # Obtener usuario directamente con la sesión
            current_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        # Verificar permisos
        if current_user.rol_id != 1 and current_user.rol_id != 2:  # Permitir admin (1) y tesorero (2)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para esta acción",
            )
        
        updated_config = crud.update_email_config(
            db=db, 
            config_id=config_id, 
            config_data=config.dict(exclude_unset=True)
        )
        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración de email no encontrada",
            )
        
        return { 
            "id": updated_config.id,
            "smtp_server": updated_config.smtp_server,
            "smtp_port": updated_config.smtp_port,
            "smtp_username": updated_config.smtp_username,
            "email_from": updated_config.email_from,
            "is_active": updated_config.is_active
        }
    finally:
        db.close()

# Endpoint para reenviar recibo
@app.post(f"{settings.API_PREFIX}/cobranzas/{{cobranza_id}}/reenviar-recibo", response_model=None)
async def reenviar_recibo_cobranza(request: Request, cobranza_id: int, email: Optional[str] = None):
    db = SessionLocal()
    try:
        # Extraer token manualmente
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verificar token manualmente
        try:
            # Decodificar token sin usar dependencias
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudieron validar las credenciales",
                )
                
            # Obtener usuario directamente con la sesión
            current_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        result = crud.reenviar_recibo(
            db=db, 
            cobranza_id=cobranza_id, 
            email=email,
            
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return {"message": "Recibo enviado exitosamente", "success": True}
    finally:
        db.close()

# Endpoint para reenviar orden de pago
@app.post(f"{settings.API_PREFIX}/pagos/{{pago_id}}/reenviar-orden", response_model=None)
async def reenviar_orden_pago(request: Request, pago_id: int, email: Optional[str] = None):
    db = SessionLocal()
    try:
        # Extraer token manualmente
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verificar token manualmente
        try:
            # Decodificar token sin usar dependencias
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudieron validar las credenciales",
                )
                
            # Obtener usuario directamente con la sesión
            current_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        result = crud.reenviar_orden_pago(
            db=db, 
            pago_id=pago_id, 
            email=email,
            current_user_id=current_user.id
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return {"message": "Orden de pago enviada exitosamente", "success": True}
    finally:
        db.close()

# Endpoint para reenviar recibo de cuota
@app.post(f"{settings.API_PREFIX}/cuotas/{{cuota_id}}/reenviar-recibo", response_model=None)
async def reenviar_recibo_cuota(request: Request, cuota_id: int, email: Optional[str] = None):
    db = SessionLocal()
    try:
        # Extraer token manualmente
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verificar token manualmente
        try:
            # Decodificar token sin usar dependencias
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudieron validar las credenciales",
                )
                
            # Obtener usuario directamente con la sesión
            current_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        result = crud.reenviar_recibo_cuota(
            db=db, 
            cuota_id=cuota_id, 
            email=email,
            current_user_id=current_user.id
        )
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return {"message": "Recibo de cuota enviado exitosamente", "success": True}
    finally:
        db.close()

# Endpoint para probar email
@app.post(f"{settings.API_PREFIX}/email-test", response_model=None)
async def test_email(request: Request, email: str):
    db = SessionLocal()
    try:
        # Extraer token manualmente
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        
        # Verificar token manualmente
        try:
            # Decodificar token sin usar dependencias
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se pudieron validar las credenciales",
                )
                
            # Obtener usuario directamente con la sesión
            current_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                )
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        
        # Obtener configuración activa
        email_config = crud.get_active_email_config(db=db)
        if not email_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay configuración de email activa",
            )
        
        try:
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
            
            # Crear mensaje de prueba
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            msg = MIMEMultipart()
            msg['From'] = email_config.email_from
            msg['To'] = email
            msg['Subject'] = "Prueba de Configuración de Email - UARC"
            
            body = """
            Este es un mensaje de prueba para verificar la configuración de email.
            
            Si está recibiendo este mensaje, la configuración es correcta.
            
            Unidad de Árbitros de Río Cuarto
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))  # Añadido 'utf-8' para soportar caracteres especiales
            
            # Enviar email
            with smtplib.SMTP(email_config.smtp_server, email_config.smtp_port) as server:
                server.starttls()
                server.login(email_config.smtp_username, email_config.smtp_password)
                server.send_message(msg)
            
            return {"success": True, "message": "Email de prueba enviado exitosamente"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)