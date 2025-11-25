from pydantic import BaseModel, EmailStr, validator, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# Schemas de Usuario/Auth
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str


class UsuarioCreate(UsuarioBase):
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Convertir a minúsculas y eliminar espacios
        v = v.lower().strip()
        
        # Validar que no tenga espacios en el medio
        if ' ' in v:
            raise ValueError('El correo no puede contener espacios')
        
        # Validar formato de email con regex más estricto
        email_regex = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('El formato del correo electrónico no es válido')
        
        # Validar que no tenga caracteres consecutivos problemáticos
        if '..' in v or '--' in v or '__' in v:
            raise ValueError('El correo no puede contener puntos, guiones o guiones bajos consecutivos')
        
        # Validar que no comience o termine con punto, guion o guion bajo antes del @
        local_part = v.split('@')[0]
        if local_part.startswith('.') or local_part.endswith('.'):
            raise ValueError('El correo no puede comenzar o terminar con punto antes del @')
        if local_part.startswith('-') or local_part.endswith('-'):
            raise ValueError('El correo no puede comenzar o terminar con guion antes del @')
        if local_part.startswith('_') or local_part.endswith('_'):
            raise ValueError('El correo no puede comenzar o terminar con guion bajo antes del @')
        
        # VALIDAR QUE SEA DE @upao.edu.pe
        if not v.endswith('@upao.edu.pe'):
            raise ValueError('El correo debe terminar en @upao.edu.pe')
        
        return v
    
    @field_validator('nombre', 'apellido')
    @classmethod
    def validate_name(cls, v, info):
        field_name = info.field_name.capitalize()
        
        # Eliminar espacios múltiples y limpiar
        v = re.sub(r'\s+', ' ', v.strip())
        
        if not v:
            raise ValueError(f'{field_name} no puede estar vacío')
        
        # Validar longitud
        if len(v) < 2:
            raise ValueError(f'{field_name} debe tener al menos 2 caracteres')
        
        if len(v) > 50:
            raise ValueError(f'{field_name} no puede tener más de 50 caracteres')
        
        # Validar que solo contenga letras, espacios, puntos, apóstrofes y guiones
        # Permite: "María José", "O'Connor", "García-Pérez", "da Silva"
        name_regex = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+(?:[\s.'\-][a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+)*$"
        if not re.match(name_regex, v):
            raise ValueError(f'{field_name} solo puede contener letras, espacios, puntos, apóstrofes y guiones (sin caracteres especiales al inicio o fin)')
        
        # Validar que no tenga espacios al inicio o final (ya limpiados, pero por seguridad)
        if v != v.strip():
            raise ValueError(f'{field_name} no puede tener espacios al inicio o final')
        
        # Validar que no tenga múltiples espacios consecutivos (ya limpiados, pero por seguridad)
        if '  ' in v:
            raise ValueError(f'{field_name} no puede tener múltiples espacios consecutivos')
        
        # Capitalizar cada palabra correctamente
        v = ' '.join(word.capitalize() for word in v.split())
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Longitud mínima
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        # Longitud máxima
        if len(v) > 128:
            raise ValueError('La contraseña no puede tener más de 128 caracteres')
        
        # Debe contener al menos una letra minúscula
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        
        # Debe contener al menos una letra mayúscula
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        
        # Debe contener al menos un número
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        
        # Debe contener al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>_-+=[]\\\/;\'`~)')
        
        # No debe contener espacios
        if ' ' in v:
            raise ValueError('La contraseña no puede contener espacios')
        
        # Validar que no sea una contraseña común
        common_passwords = [
            'password', '12345678', 'qwerty123', 'abc123', 'password123',
            'admin123', 'letmein', 'welcome123', '123456789', 'password1'
        ]
        if v.lower() in common_passwords:
            raise ValueError('La contraseña es demasiado común, elige una más segura')
        
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
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        # Longitud mínima
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        # Longitud máxima
        if len(v) > 128:
            raise ValueError('La contraseña no puede tener más de 128 caracteres')
        
        # Debe contener al menos una letra minúscula
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        
        # Debe contener al menos una letra mayúscula
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        
        # Debe contener al menos un número
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        
        # Debe contener al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
        
        # No debe contener espacios
        if ' ' in v:
            raise ValueError('La contraseña no puede contener espacios')
        
        # Validar que no sea una contraseña común
        common_passwords = [
            'password', '12345678', 'qwerty123', 'abc123', 'password123',
            'admin123', 'letmein', 'welcome123', '123456789', 'password1'
        ]
        if v.lower() in common_passwords:
            raise ValueError('La contraseña es demasiado común, elige una más segura')
        
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
class CursoAprobadoMultiMalla(BaseModel):
    codigo: str
    malla_origen_anio: int  # De qué malla es este curso


class RecomendacionRequest(BaseModel):
    malla_id: int  # Malla objetivo (normalmente 2025)
    cursos_aprobados: List[str]  # Lista de CÓDIGOS de cursos aprobados (ej: ["ICSI-506", "CIEN-752"])
    # Nueva funcionalidad: cursos de múltiples mallas
    cursos_aprobados_multi_malla: Optional[List[CursoAprobadoMultiMalla]] = None


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
