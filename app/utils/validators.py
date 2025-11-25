"""
Funciones de validación para registro de usuarios
"""
import re
from fastapi import HTTPException, status


def validar_nombre_apellido(texto: str, campo: str = "Campo") -> str:
    """
    Valida que nombre o apellido sea válido.
    - Elimina múltiples espacios
    - Solo letras, espacios, puntos, apóstrofes y guiones
    - No permite caracteres especiales al inicio o fin
    - Capitaliza correctamente
    
    Args:
        texto: El texto a validar (nombre o apellido)
        campo: Nombre del campo para el mensaje de error
        
    Returns:
        El texto validado y formateado
        
    Raises:
        HTTPException si la validación falla
    """
    # Eliminar espacios múltiples y limpiar
    texto = re.sub(r'\s+', ' ', texto.strip())
    
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
    
    # Verificar que solo contenga letras, espacios, puntos, apóstrofes y guiones
    # Permite: "María José", "O'Connor", "García-Pérez", "da Silva"
    name_regex = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+(?:[\s.'\-][a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+)*$"
    if not re.match(name_regex, texto):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} solo puede contener letras, espacios, puntos, apóstrofes y guiones (sin caracteres especiales al inicio o fin)"
        )
    
    # Capitalizar cada palabra correctamente
    texto = ' '.join(word.capitalize() for word in texto.split())
    
    return texto


def validar_password(password: str) -> str:
    """
    Valida que la contraseña cumpla con requisitos de seguridad estrictos:
    - Al menos 8 caracteres, máximo 128
    - Al menos una letra minúscula
    - Al menos una letra mayúscula
    - Al menos un número
    - Al menos un carácter especial
    - Sin espacios
    - No contraseñas comunes
    
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
    
    # Verificar que contenga al menos una letra minúscula
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra minúscula"
        )
    
    # Verificar que contenga al menos una letra mayúscula
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una letra mayúscula"
        )
    
    # Verificar que contenga al menos un número
    if not re.search(r'\d', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número"
        )
    
    # Verificar que contenga al menos un carácter especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?\":{}|<>_-+=[]\\\/;'`~)"
        )
    
    # Verificar que no contenga espacios
    if ' ' in password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no puede contener espacios"
        )
    
    # Verificar que no sea una contraseña común
    common_passwords = [
        'password', '12345678', 'qwerty123', 'abc123', 'password123',
        'admin123', 'letmein', 'welcome123', '123456789', 'password1',
        'Password123', 'Admin123!'
    ]
    if password.lower() in [p.lower() for p in common_passwords]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña es demasiado común, elige una más segura"
        )
    
    return password


def validar_email(email: str) -> str:
    """
    Valida el formato del email con reglas estrictas
    
    Args:
        email: El email a validar
        
    Returns:
        El email validado (en minúsculas, sin espacios)
        
    Raises:
        HTTPException si la validación falla
    """
    # Limpiar y convertir a minúsculas
    email = email.strip().lower()
    
    # Validar que no tenga espacios
    if ' ' in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo no puede contener espacios"
        )
    
    # Regex estricto para validar email
    email_regex = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de email inválido"
        )
    
    # Validar que no tenga caracteres consecutivos problemáticos
    if '..' in email or '--' in email or '__' in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo no puede contener puntos, guiones o guiones bajos consecutivos"
        )
    
    # Validar la parte local (antes del @)
    local_part = email.split('@')[0]
    
    # No puede comenzar o terminar con . - _
    if local_part[0] in '.-_' or local_part[-1] in '.-_':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo no puede comenzar o terminar con punto, guion o guion bajo antes del @"
        )
    
    # VALIDAR QUE SEA DE @upao.edu.pe
    if not email.endswith('@upao.edu.pe'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo debe terminar en @upao.edu.pe"
        )
    
    # Validar longitud
    if len(email) > 254:  # RFC 5321
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email es demasiado largo"
        )
    
    if len(local_part) > 64:  # RFC 5321
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La parte local del email (antes del @) es demasiado larga"
        )
    
    return email
