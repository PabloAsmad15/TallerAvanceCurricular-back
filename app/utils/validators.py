"""
Funciones de validación para registro de usuarios
"""
import re
from fastapi import HTTPException, status


def validar_nombre_apellido(texto: str, campo: str = "Campo") -> str:
    """
    Valida que nombre o apellido contenga solo letras, espacios y puntos.
    NO permite que sea solo puntos, espacios, o una combinación de estos.
    
    Args:
        texto: El texto a validar (nombre o apellido)
        campo: Nombre del campo para el mensaje de error
        
    Returns:
        El texto validado (sin espacios al inicio/final)
        
    Raises:
        HTTPException si la validación falla
    """
    # Limpiar espacios al inicio y final
    texto = texto.strip()
    
    # Verificar que no esté vacío
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} no puede estar vacío"
        )
    
    # Verificar longitud mínima y máxima
    if len(texto) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} debe tener al menos 2 caracteres"
        )
    
    if len(texto) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} no puede tener más de 50 caracteres"
        )
    
    # Verificar que contenga al menos una letra
    if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', texto):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} debe contener al menos una letra"
        )
    
    # Verificar que solo contenga letras, espacios y puntos
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.]+$', texto):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} solo puede contener letras, espacios y puntos"
        )
    
    # Verificar que no sea solo puntos y/o espacios
    texto_sin_puntos_espacios = texto.replace('.', '').replace(' ', '')
    if not texto_sin_puntos_espacios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} no puede contener solo puntos y espacios"
        )
    
    return texto


def validar_password(password: str) -> str:
    """
    Valida que la contraseña cumpla con los requisitos de seguridad.
    Debe contener:
    - Al menos 8 caracteres
    - Al menos una letra
    - Al menos un número
    - Puede contener puntos y otros caracteres especiales
    - NO puede ser solo números o solo letras o solo puntos
    
    Args:
        password: La contraseña a validar
        
    Returns:
        La contraseña validada
        
    Raises:
        HTTPException si la validación falla
    """
    # Verificar longitud mínima
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    
    # Verificar longitud máxima
    if len(password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no puede tener más de 128 caracteres"
        )
    
    # Verificar que contenga al menos una letra
    if not re.search(r'[a-zA-Z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra"
        )
    
    # Verificar que contenga al menos un número
    if not re.search(r'\d', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número"
        )
    
    # Verificar que no sea solo letras
    if password.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no puede contener solo letras"
        )
    
    # Verificar que no sea solo números
    if password.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no puede contener solo números"
        )
    
    # Verificar que no sea solo puntos
    if all(c == '.' for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no puede contener solo puntos"
        )
    
    return password


def validar_email(email: str) -> str:
    """
    Valida el formato del email
    
    Args:
        email: El email a validar
        
    Returns:
        El email validado (en minúsculas)
        
    Raises:
        HTTPException si la validación falla
    """
    email = email.strip().lower()
    
    # Patrón regex para email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de email inválido"
        )
    
    return email
