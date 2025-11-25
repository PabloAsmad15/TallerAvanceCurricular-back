from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import secrets
from ..database import get_db
from ..schemas import (
    UsuarioCreate, UsuarioResponse, Token, TokenWithUser, UsuarioLogin,
    ForgotPasswordRequest, ResetPasswordRequest
)
from ..models import Usuario, PasswordReset
from ..utils.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user
)
from ..utils.email import send_password_reset_email, send_welcome_email
from ..utils.validators import validar_nombre_apellido, validar_password, validar_email
from ..config import settings
from ..firebase_config import verify_firebase_token
from pydantic import BaseModel

router = APIRouter()


# Schemas para Firebase
class FirebaseLoginRequest(BaseModel):
    firebaseToken: str

class FirebaseRegisterRequest(BaseModel):
    firebaseToken: str
    firebaseUid: str
    email: str
    nombre: str
    apellido: str
    tipo: str = "estudiante"


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    
    # Validar email
    email_validado = validar_email(usuario.email)
    
    # Validar nombre y apellido
    nombre_validado = validar_nombre_apellido(usuario.nombre, "Nombre")
    apellido_validado = validar_nombre_apellido(usuario.apellido, "Apellido")
    
    # Validar contraseña
    validar_password(usuario.password)
    
    # Verificar si el email ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == email_validado).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Crear usuario
    hashed_password = get_password_hash(usuario.password)
    db_usuario = Usuario(
        email=email_validado,
        password_hash=hashed_password,
        nombre=nombre_validado,
        apellido=apellido_validado
    )
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    
    # Enviar email de bienvenida (sin bloquear)
    try:
        await send_welcome_email(usuario.email, usuario.nombre)
    except Exception as e:
        print(f"Error enviando email de bienvenida: {e}")
    
    return db_usuario


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Iniciar sesión"""
    
    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-json", response_model=TokenWithUser)
async def login_json(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    """Iniciar sesión con JSON (para frontend)"""
    
    usuario = db.query(Usuario).filter(Usuario.email == usuario_login.email).first()
    
    if not usuario or not verify_password(usuario_login.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    
    if not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=access_token_expires
    )
    
    # Devolver token y datos del usuario
    from ..schemas import UsuarioResponse
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": UsuarioResponse.from_orm(usuario)
    }


@router.get("/me", response_model=UsuarioResponse)
async def get_me(current_user: Usuario = Depends(get_current_active_user)):
    """Obtener información del usuario actual"""
    return current_user


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Solicitar recuperación de contraseña"""
    
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    # Si el usuario NO existe, devolver mensaje genérico sin crear token
    if not usuario:
        # Por seguridad, no revelamos si el email existe o no
        return {"message": "Si el correo existe, recibirás un enlace de recuperación"}
    
    # El usuario SÍ existe, procedemos a generar token
    # Generar token único
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Guardar token
    password_reset = PasswordReset(
        usuario_id=usuario.id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(password_reset)
    db.commit()
    
    # Enviar email
    email_sent = False
    error_message = None
    try:
        await send_password_reset_email(request.email, token)
        email_sent = True
        print(f"✅ Email de recuperación enviado exitosamente a {request.email}")
    except Exception as e:
        error_message = str(e)
        print(f"❌ Error enviando email: {error_message}")
        # En desarrollo, continuamos sin enviar email
        pass
    
    # En desarrollo, devolver el token si el email no se pudo enviar
    if not email_sent:
        return {
            "message": "Email no configurado - Token de recuperación (solo desarrollo)",
            "token": token,
            "reset_url": f"http://localhost:5173/reset-password?token={token}",
            "error": error_message
        }
    
    return {"message": "Si el correo existe, recibirás un enlace de recuperación"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Cambiar contraseña con token"""
    
    # Buscar token
    password_reset = db.query(PasswordReset).filter(
        PasswordReset.token == request.token,
        PasswordReset.used == False
    ).first()
    
    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o ya utilizado"
        )
    
    # Verificar expiración
    if datetime.utcnow() > password_reset.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado"
        )
    
    # Cambiar contraseña
    usuario = db.query(Usuario).filter(Usuario.id == password_reset.usuario_id).first()
    usuario.password_hash = get_password_hash(request.new_password)
    
    # Marcar token como usado
    password_reset.used = True
    
    db.commit()
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.post("/firebase-login", response_model=UsuarioResponse)
async def firebase_login(request: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Login con Firebase Auth - Verificar token y retornar datos del usuario de PostgreSQL"""
    
    print(f"🔐 Iniciando login Firebase")
    
    # 1. Verificar token de Firebase
    try:
        firebase_user = await verify_firebase_token(request.firebaseToken)
        firebase_uid = firebase_user.get('uid')
        email = firebase_user.get('email')
        print(f"✓ Token verificado - UID: {firebase_uid}, Email: {email}")
    except Exception as e:
        print(f"❌ Error verificando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de Firebase inválido: {str(e)}"
        )
    
    if not email:
        print(f"❌ Token sin email")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de Firebase no contiene un email"
        )
    
    # 2. Buscar usuario en PostgreSQL por email
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    
    if not usuario:
        print(f"❌ Usuario no encontrado con email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado. Debes registrarte primero."
        )
    
    print(f"✓ Usuario encontrado: {usuario.nombre} {usuario.apellido}")
    
    if not usuario.is_active:
        print(f"❌ Usuario inactivo")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    # 3. Actualizar firebase_uid si no existe
    if not usuario.firebase_uid:
        usuario.firebase_uid = firebase_uid
        db.commit()
        db.refresh(usuario)
        print(f"✓ Firebase UID actualizado")
    
    print(f"✅ Login exitoso para {email}")
    return usuario


@router.post("/firebase-register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def firebase_register(request: FirebaseRegisterRequest, db: Session = Depends(get_db)):
    """Registro con Firebase Auth - Crear usuario en PostgreSQL después de registro en Firebase"""
    
    print(f"📝 Iniciando registro Firebase para: {request.email}")
    print(f"   Nombre: {request.nombre}, Apellido: {request.apellido}, Tipo: {request.tipo}")
    
    # 0. Validar datos antes de verificar Firebase
    try:
        email_validado = validar_email(request.email)
        print(f"✓ Email validado: {email_validado}")
    except HTTPException as e:
        print(f"❌ Error validando email: {e.detail}")
        raise
    
    try:
        nombre_validado = validar_nombre_apellido(request.nombre, "Nombre")
        print(f"✓ Nombre validado: {nombre_validado}")
    except HTTPException as e:
        print(f"❌ Error validando nombre: {e.detail}")
        raise
    
    try:
        apellido_validado = validar_nombre_apellido(request.apellido, "Apellido")
        print(f"✓ Apellido validado: {apellido_validado}")
    except HTTPException as e:
        print(f"❌ Error validando apellido: {e.detail}")
        raise
    
    # 1. Verificar token de Firebase
    try:
        firebase_user = await verify_firebase_token(request.firebaseToken)
        firebase_uid = firebase_user.get('uid')
        print(f"✓ Token Firebase verificado, UID: {firebase_uid}")
    except Exception as e:
        print(f"❌ Error verificando token Firebase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de Firebase inválido: {str(e)}"
        )
    
    # 2. Verificar que el UID del token coincida con el enviado
    if firebase_uid != request.firebaseUid:
        print(f"❌ UID no coincide. Token: {firebase_uid}, Enviado: {request.firebaseUid}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El UID de Firebase no coincide con el token"
        )
    
    # 3. Verificar si el usuario ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == email_validado).first()
    if existing_user:
        print(f"❌ Usuario ya existe con email: {email_validado}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    print(f"✓ Email disponible, procediendo a crear usuario")
    
    # 4. Crear usuario en PostgreSQL
    # No necesitamos password_hash porque Firebase maneja la autenticación
    nuevo_usuario = Usuario(
        email=email_validado,
        nombre=nombre_validado,
        apellido=apellido_validado,
        firebase_uid=firebase_uid,
        password_hash="",  # Firebase maneja las contraseñas
        is_active=True
    )
    
    # Asignar rol de admin si el tipo es admin
    if request.tipo == "admin":
        nuevo_usuario.is_admin = True
    
    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        print(f"✅ Usuario creado exitosamente: ID {nuevo_usuario.id}")
    except Exception as e:
        print(f"❌ Error guardando usuario en DB: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando usuario: {str(e)}"
        )
    
    # 5. Enviar email de bienvenida (sin bloquear)
    try:
        await send_welcome_email(request.email, request.nombre)
    except Exception as e:
        print(f"⚠️  Error enviando email de bienvenida: {e}")
    
    return nuevo_usuario
