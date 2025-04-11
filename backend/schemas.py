from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None

# Rol Schemas
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass
class RolUpdate(BaseModel):
    nombre: Optional[str] = None
class Rol(RolBase):
    id: int
    
    class Config:
        orm_mode = True

# Usuario Schemas
class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    password: str
    rol_id: int

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    rol_id: Optional[int] = None

class Usuario(UsuarioBase):
    id: int
    rol_id: int
    
    class Config:
        orm_mode = True

class UsuarioDetalle(Usuario):
    rol: Rol
    
    class Config:
        orm_mode = True

# Retencion Schemas
class RetencionBase(BaseModel):
    nombre: str
    monto: float

class RetencionCreate(RetencionBase):
    pass

class RetencionUpdate(BaseModel):
    nombre: Optional[str] = None
    monto: Optional[float] = None

class Retencion(RetencionBase):
    id: int
    
    class Config:
        orm_mode = True

# Categoria Schemas
class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None

class Categoria(CategoriaBase):
    id: int
    
    class Config:
        orm_mode = True

# RetencionDivision Schemas
class RetencionDivisionBase(BaseModel):
    retencion_id: int
    categoria_id: Optional[int] = None

class RetencionDivisionCreate(RetencionDivisionBase):
    pass

class RetencionDivision(RetencionDivisionBase):
    id: int
    
    class Config:
        orm_mode = True

class RetencionDivisionDetalle(RetencionDivision):
    retencion: Retencion
    categoria: Optional[Categoria] = None
    
    class Config:
        orm_mode = True

class EmailConfigBase(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    is_active: bool = True

class EmailConfigCreate(EmailConfigBase):
    pass

class EmailConfigUpdate(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    is_active: Optional[bool] = None

class EmailConfig(EmailConfigBase):
    id: int
    
    class Config:
        orm_mode = True

# Pago Schemas
class PagoBase(BaseModel):
    usuario_id: int
    fecha: date
    monto: float
    retencion_id: Optional[int] = None  # Hacer este campo opcional
    transaccion_id: Optional[int] = None

class PagoCreate(BaseModel):
    usuario_id: int
    fecha: date
    monto: float
    retencion_id: Optional[int] = None

class PagoUpdate(BaseModel):
    usuario_id: Optional[int] = None
    fecha: Optional[date] = None
    monto: Optional[float] = None
    retencion_id: Optional[int] = None
    transaccion_id: Optional[int] = None

class Pago(PagoBase):
    id: int
    
    class Config:
        orm_mode = True

class PagoDetalle(Pago):
    usuario: Usuario
    retencion: Optional[Retencion] = None  # Hacer la retención opcional
    
    class Config:
        orm_mode = True
# Cobranza Schemas
class CobranzaBase(BaseModel):
    usuario_id: int
    fecha: date
    monto: float
    transaccion_id: Optional[int] = None

class CobranzaCreate(CobranzaBase):
    pass

class CobranzaUpdate(BaseModel):
    usuario_id: Optional[int] = None
    fecha: Optional[date] = None
    monto: Optional[float] = None
    transaccion_id: Optional[int] = None

class Cobranza(CobranzaBase):
    id: int
    
    class Config:
        orm_mode = True

class CobranzaDetalle(Cobranza):
    usuario: Usuario
    
    class Config:
        orm_mode = True

# Partida Schemas
class PartidaBase(BaseModel):
    fecha: date
    cuenta: str
    detalle: Optional[str] = None
    recibo_factura: Optional[str] = None
    ingreso: float = 0
    egreso: float = 0
    saldo: float
    usuario_id: int
    cobranza_id: Optional[int] = None
    pago_id: Optional[int] = None
    monto: float
    tipo: str = Field(..., regex='^(ingreso|egreso)$')

class PartidaCreate(PartidaBase):
    pass

class PartidaUpdate(BaseModel):
    fecha: Optional[date] = None
    cuenta: Optional[str] = None
    detalle: Optional[str] = None
    recibo_factura: Optional[str] = None
    ingreso: Optional[float] = None
    egreso: Optional[float] = None
    saldo: Optional[float] = None
    usuario_id: Optional[int] = None
    cobranza_id: Optional[int] = None
    pago_id: Optional[int] = None
    monto: Optional[float] = None
    tipo: Optional[str] = Field(None, regex='^(ingreso|egreso)$')

class Partida(PartidaBase):
    id: int
    
    class Config:
        orm_mode = True

class PartidaDetalle(Partida):
    usuario: Usuario
    
    class Config:
        orm_mode = True

# Cuota Schemas
class CuotaBase(BaseModel):
    usuario_id: Optional[int] = None
    fecha: date
    monto: float
    pagado: bool = False
    monto_pagado: float = 0

class CuotaCreate(CuotaBase):
    pass

class CuotaUpdate(BaseModel):
    usuario_id: Optional[int] = None
    fecha: Optional[date] = None
    monto: Optional[float] = None
    pagado: Optional[bool] = None
    monto_pagado: Optional[float] = None

class Cuota(CuotaBase):
    id: int
    
    class Config:
        orm_mode = True

class CuotaDetalle(Cuota):
    usuario: Optional[Usuario] = None
    
    class Config:
        orm_mode = True

# Transaccion Schemas
class TransaccionBase(BaseModel):
    tipo: str = Field(..., regex='^(ingreso|egreso)$')
    monto: float
    fecha: date = Field(default_factory=date.today)
    usuario_id: Optional[int] = None
    referencia: Optional[str] = None

class TransaccionCreate(TransaccionBase):
    pass

class TransaccionUpdate(BaseModel):
    tipo: Optional[str] = Field(None, regex='^(ingreso|egreso)$')
    monto: Optional[float] = None
    fecha: Optional[date] = None
    usuario_id: Optional[int] = None
    referencia: Optional[str] = None

class Transaccion(TransaccionBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class TransaccionDetalle(Transaccion):
    usuario: Optional[Usuario] = None
    
    class Config:
        orm_mode = True

# Auditoria Schemas
class AuditoriaBase(BaseModel):
    usuario_id: Optional[int] = None
    accion: str
    tabla_afectada: str
    registro_id: int

class AuditoriaCreate(AuditoriaBase):
    pass

class Auditoria(AuditoriaBase):
    id: int
    fecha: datetime
    
    class Config:
        orm_mode = True

class AuditoriaDetalle(Auditoria):
    usuario: Optional[Usuario] = None
    
    class Config:
        orm_mode = True

# Response Schemas
class GenericResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None