from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Campo para identificar administradores
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    recomendaciones = relationship("Recomendacion", back_populates="usuario")


class Malla(Base):
    __tablename__ = "mallas"
    
    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, unique=True, nullable=False)  # 2015, 2019, 2022, 2025
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    cursos = relationship("Curso", back_populates="malla")


class Curso(Base):
    __tablename__ = "cursos"
    
    id = Column(Integer, primary_key=True, index=True)
    malla_id = Column(Integer, ForeignKey("mallas.id"), nullable=False)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(200), nullable=False)
    creditos = Column(Integer, nullable=False)
    ciclo = Column(Integer, nullable=False)  # 1-10
    tipo = Column(String(50))  # Obligatorio, Electivo, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    malla = relationship("Malla", back_populates="cursos")
    prerequisitos = relationship(
        "Prerequisito",
        foreign_keys="Prerequisito.curso_id",
        back_populates="curso"
    )


class Prerequisito(Base):
    __tablename__ = "prerequisitos"
    
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    prerequisito_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    curso = relationship("Curso", foreign_keys=[curso_id])
    prerequisito_curso = relationship("Curso", foreign_keys=[prerequisito_id])


class Convalidacion(Base):
    __tablename__ = "convalidaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    curso_origen_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    curso_destino_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    malla_origen_anio = Column(Integer, nullable=False)
    malla_destino_anio = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    curso_origen = relationship("Curso", foreign_keys=[curso_origen_id])
    curso_destino = relationship("Curso", foreign_keys=[curso_destino_id])


class Recomendacion(Base):
    __tablename__ = "recomendaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    malla_id = Column(Integer, ForeignKey("mallas.id"), nullable=False)
    algoritmo_usado = Column(String(50), nullable=False)  # "constraint_programming" o "backtracking"
    cursos_aprobados = Column(Text)  # JSON string con IDs de cursos aprobados
    cursos_recomendados = Column(Text)  # JSON string con recomendación
    razon_algoritmo = Column(Text)  # Por qué el agente eligió ese algoritmo
    tiempo_ejecucion = Column(Float)  # Tiempo en segundos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="recomendaciones")
    malla = relationship("Malla")


class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario")
