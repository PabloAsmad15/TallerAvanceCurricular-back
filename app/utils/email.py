import resend
from ..config import settings

# Configurar Resend
resend.api_key = settings.RESEND_API_KEY


async def send_password_reset_email(email: str, token: str):
    """Envía email para recuperación de contraseña"""
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    # En desarrollo, usar el email override si está configurado
    email_destino = settings.DEV_EMAIL_OVERRIDE if settings.DEV_EMAIL_OVERRIDE else email
    es_desarrollo = settings.DEV_EMAIL_OVERRIDE is not None
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                <h2 style="color: #003d7a;">Recuperación de Contraseña - UPAO</h2>
                {f'<p style="background: #fff3cd; padding: 10px; border-radius: 5px; font-size: 13px;"><strong>Modo desarrollo:</strong> Email solicitado para: {email}</p>' if es_desarrollo else ''}
                <p>Has solicitado restablecer tu contraseña.</p>
                <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background-color: #003d7a; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Restablecer Contraseña
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Si no solicitaste este cambio, puedes ignorar este correo.
                </p>
                <p style="color: #666; font-size: 14px;">
                    Este enlace expirará en 1 hora.
                </p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Sistema de Avance Curricular - Universidad Privada Antenor Orrego
                </p>
            </div>
        </body>
    </html>
    """
    
    params = {
        "from": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
        "to": [email_destino],
        "subject": "Recuperación de Contraseña - UPAO",
        "html": html,
    }
    
    response = resend.Emails.send(params)
    print(f"📧 Email enviado a: {email_destino} (solicitado por: {email})")
    return response


async def send_welcome_email(email: str, nombre: str):
    """Envía email de bienvenida"""
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                <h2 style="color: #003d7a;">¡Bienvenido al Sistema de Recomendación Curricular!</h2>
                <p>Hola {nombre},</p>
                <p>Tu cuenta ha sido creada exitosamente.</p>
                <p>Ahora puedes acceder al sistema y obtener recomendaciones personalizadas para tu avance curricular.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}" 
                       style="background-color: #003d7a; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Ir al Sistema
                    </a>
                </div>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Sistema de Avance Curricular - Universidad Privada Antenor Orrego
                </p>
            </div>
        </body>
    </html>
    """
    
    params = {
        "from": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
        "to": [email],
        "subject": "Bienvenido - Sistema de Avance Curricular UPAO",
        "html": html,
    }
    
    resend.Emails.send(params)

