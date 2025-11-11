import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException

# Inicializar Firebase Admin SDK
def initialize_firebase():
    """Inicializar Firebase Admin SDK con las credenciales del service account"""
    try:
        # Verificar si Firebase ya está inicializado
        firebase_admin.get_app()
    except ValueError:
        # No está inicializado, proceder a inicializar
        
        # Opción 1: Usar archivo JSON (para desarrollo local)
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        else:
            # Opción 2: Usar variables de entorno (para producción)
            service_account_json = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
                "universe_domain": "googleapis.com"
            }
            
            # Validar que todas las variables estén presentes
            if not all([
                service_account_json["project_id"],
                service_account_json["private_key"],
                service_account_json["client_email"]
            ]):
                raise ValueError("Faltan variables de entorno de Firebase. Configura FIREBASE_* en .env")
            
            cred = credentials.Certificate(service_account_json)
            firebase_admin.initialize_app(cred)

async def verify_firebase_token(token: str) -> dict:
    """
    Verificar token de Firebase y retornar los datos del usuario
    
    Args:
        token: Token de Firebase (ID Token)
    
    Returns:
        dict con datos del usuario de Firebase
    
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        # Verificar el token con Firebase
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token de Firebase inválido")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token de Firebase expirado")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error al verificar token: {str(e)}")

async def get_firebase_user(uid: str):
    """
    Obtener información del usuario de Firebase por UID
    
    Args:
        uid: UID del usuario en Firebase
    
    Returns:
        UserRecord de Firebase
    """
    try:
        user = auth.get_user(uid)
        return user
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en Firebase")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")
