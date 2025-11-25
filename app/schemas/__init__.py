from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Schemas de Usuario/Auth
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str


class UsuarioCreate(UsuarioBase):
    password: str
    
    @validator('email')
    def email_must_be_upao(cls, v):
        if not v.endswith('@upao.edu.pe'):
            raise ValueError('El correo debe terminar en @upao.edu.pe')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioResponse(UsuarioBase):
    id: int
    is_active: bool
    is_admin: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioResponse


class TokenData(BaseModel):
    email: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


# Schemas de Malla
class MallaBase(BaseModel):
    anio: int
    nombre: str
    descripcion: Optional[str] = None


class MallaResponse(MallaBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schemas de Curso
class CursoBase(BaseModel):
    codigo: str
    nombre: str
    creditos: int
    ciclo: int
    tipo: Optional[str] = None


class CursoResponse(CursoBase):
    id: int
    malla_id: int
    
    class Config:
        from_attributes = True


class CursoPorCiclo(BaseModel):
    ciclo: int
    cursos: List[CursoResponse]


# Schemas de Recomendación
class RecomendacionRequest(BaseModel):
    malla_id: int
    cursos_aprobados: List[str]  # Lista de CÓDIGOS de cursos aprobados (ej: ["ICSI-506", "CIEN-752"])


class CursoRecomendado(BaseModel):
    curso_id: int
    codigo: str
    nombre: str
    creditos: int
    ciclo: int
    prioridad: int  # 1: Alta, 2: Media, 3: Baja
    razon: str


class RecomendacionResponse(BaseModel):
    id: int
    algoritmo_usado: str
    razon_algoritmo: str
    cursos_recomendados: List[CursoRecomendado]
    tiempo_ejecucion: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# Schemas para comparación de algoritmos
class ResultadoAlgoritmo(BaseModel):
    algoritmo: str
    cursos_recomendados: List[CursoRecomendado]
    tiempo_ejecucion: float
    total_creditos: int
    numero_cursos: int
    cumple_limite_creditos: bool
    error: Optional[str] = None


class ComparacionAlgoritmosResponse(BaseModel):
    malla_id: int
    cursos_aprobados: List[str]
    max_creditos: int
    resultados: List[ResultadoAlgoritmo]
    algoritmo_seleccionado: str
    razon_seleccion: str
    metricas_comparacion: Dict[str, Any]


# Schemas de Prerequisitos
class PrerequistoResponse(BaseModel):
    id: int
    curso_id: int
    prerequisito_id: int
    
    class Config:
        from_attributes = True


# Schemas de Convalidación
class ConvalidacionResponse(BaseModel):
    id: int
    curso_origen_id: int
    curso_destino_id: int
    malla_origen_anio: int
    malla_destino_anio: int
    
    class Config:
        from_attributes = True
