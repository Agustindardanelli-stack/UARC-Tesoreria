from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Text, DateTime, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(Text, nullable=True)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    pagos = relationship("Pago", back_populates="usuario")
    cobranzas = relationship("Cobranza", back_populates="usuario")
    partidas = relationship("Partida", back_populates="usuario")
    cuotas = relationship("Cuota", back_populates="usuario")
    transacciones = relationship("Transaccion", back_populates="usuario")
    auditorias = relationship("Auditoria", back_populates="usuario")

class Rol(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="rol")

class Retencion(Base):
    __tablename__ = "retenciones"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    
    # Relaciones
    pagos = relationship("Pago", back_populates="retencion")
    divisiones = relationship("RetencionDivision", back_populates="retencion")

class Categoria(Base):
    __tablename__ = "categorias"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    
    # Relaciones
    divisiones = relationship("RetencionDivision", back_populates="categoria")

class RetencionDivision(Base):
    __tablename__ = "retenciones_division"
    
    id = Column(Integer, primary_key=True, index=True)
    retencion_id = Column(Integer, ForeignKey("retenciones.id", ondelete="CASCADE"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="CASCADE"), nullable=True)
    
    # Relaciones
    retencion = relationship("Retencion", back_populates="divisiones")
    categoria = relationship("Categoria", back_populates="divisiones")

class Pago(Base):
    __tablename__ = "pagos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(Date, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    retencion_id = Column(Integer, ForeignKey("retenciones.id", ondelete="CASCADE"), nullable=False)
    transaccion_id = Column(Integer, ForeignKey("transacciones.id"), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="pagos")
    retencion = relationship("Retencion", back_populates="pagos")
    transaccion = relationship("Transaccion", back_populates="pagos")
    partidas = relationship("Partida", back_populates="pago")
    email_enviado = Column(Boolean, default=False)
    fecha_envio_email = Column(DateTime, nullable=True)
    email_destinatario = Column(String(100), nullable=True)

class Cobranza(Base):
    __tablename__ = "cobranzas"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(Date, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    transaccion_id = Column(Integer, ForeignKey("transacciones.id"), nullable=True)
    
    # Nuevos campos para tracking de email
    email_enviado = Column(Boolean, default=False)
    fecha_envio_email = Column(DateTime, nullable=True)
    email_destinatario = Column(String(100), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="cobranzas")
    transaccion = relationship("Transaccion", back_populates="cobranzas")
    partidas = relationship("Partida", back_populates="cobranza")
class Partida(Base):
    __tablename__ = "partidas"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    cuenta = Column(String(50), nullable=False)
    detalle = Column(String(255), nullable=True)
    recibo_factura = Column(String(50), nullable=True)
    ingreso = Column(Numeric(10, 2), nullable=False, default=0)
    egreso = Column(Numeric(10, 2), nullable=False, default=0)
    saldo = Column(Numeric(10, 2), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    cobranza_id = Column(Integer, ForeignKey("cobranzas.id", ondelete="SET NULL"), nullable=True)
    pago_id = Column(Integer, ForeignKey("pagos.id", ondelete="SET NULL"), nullable=True)
    monto = Column(Numeric(10, 2), nullable=False)
    tipo = Column(String(10), nullable=False)
    
    __table_args__ = (
        CheckConstraint("tipo IN ('ingreso', 'egreso')", name="partidas_tipo_check"),
    )
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="partidas")
    cobranza = relationship("Cobranza", back_populates="partidas")
    pago = relationship("Pago", back_populates="partidas")

class EmailConfig(Base):
    __tablename__ = "email_config"
    
    id = Column(Integer, primary_key=True, index=True)
    smtp_server = Column(String(100), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    smtp_username = Column(String(100), nullable=False)
    smtp_password = Column(String(100), nullable=False)
    email_from = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

class Cuota(Base):
    __tablename__ = "cuota"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha = Column(Date, nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    pagado = Column(Boolean, default=False)
    monto_pagado = Column(Numeric(10, 2), default=0)
    email_enviado = Column(Boolean, default=False)
    fecha_envio_email = Column(DateTime, nullable=True)
    email_destinatario = Column(String(100), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="cuotas")

class Transaccion(Base):
    __tablename__ = "transacciones"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(10), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha = Column(Date, nullable=False, default=func.current_date())
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    referencia = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    __table_args__ = (
        CheckConstraint("tipo IN ('ingreso', 'egreso')", name="transacciones_tipo_check"),
    )
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="transacciones")
    pagos = relationship("Pago", back_populates="transaccion")
    cobranzas = relationship("Cobranza", back_populates="transaccion")

class Auditoria(Base):
    __tablename__ = "auditoria"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    accion = Column(Text, nullable=False)
    tabla_afectada = Column(Text, nullable=False)
    registro_id = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=func.current_timestamp())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="auditorias")