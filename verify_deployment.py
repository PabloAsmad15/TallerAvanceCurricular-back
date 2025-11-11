"""
Script para verificar que la configuración está correcta antes de deployment
"""
import sys
import os

print("=" * 70)
print("🔍 VERIFICACIÓN DE CONFIGURACIÓN PARA DEPLOYMENT")
print("=" * 70)
print()

# Simular environment de Render
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:paadmin@db.ldhiqmeubrlbnowsdoru.supabase.co:5432/postgres")
os.environ.setdefault("SECRET_KEY", "bCmsTkGIKf-yVX-mW9be6uCMUM9iF9TEVlNfrQMIEfI")
os.environ.setdefault("RESEND_API_KEY", "re_Fbi4gPis_DAfAFzX261nVQjmbiYew5iUS")
os.environ.setdefault("GEMINI_API_KEY", "AIzaSyDOxlfoHQqrgyubJZVgavWLI0yzEdmOmk8")
os.environ.setdefault("FRONTEND_URL", "https://tu-frontend.vercel.app")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

try:
    print("1️⃣  Importando configuración...")
    from app.config import settings
    print("   ✅ Config importado correctamente")
    print()
    
    print("2️⃣  Verificando variables de entorno:")
    print(f"   DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    print(f"   SECRET_KEY: {settings.SECRET_KEY[:20]}...")
    print(f"   RESEND_API_KEY: {settings.RESEND_API_KEY[:20]}...")
    print(f"   GEMINI_API_KEY: {settings.GEMINI_API_KEY[:20]}...")
    print(f"   MAIL_FROM: {settings.MAIL_FROM}")
    print(f"   MAIL_FROM_NAME: {settings.MAIL_FROM_NAME}")
    print(f"   FRONTEND_URL: {settings.FRONTEND_URL}")
    print("   ✅ Todas las variables están configuradas")
    print()
    
    print("3️⃣  Probando conexión a base de datos...")
    from app.database import engine
    conn = engine.connect()
    print("   ✅ Conexión a Supabase exitosa")
    conn.close()
    print()
    
    print("4️⃣  Importando aplicación FastAPI...")
    from app.main import app
    print("   ✅ App importada correctamente")
    print()
    
    print("5️⃣  Verificando routers...")
    routes_count = len(app.routes)
    print(f"   ✅ {routes_count} rutas registradas")
    print()
    
    print("=" * 70)
    print("✅ ¡TODO ESTÁ LISTO PARA DEPLOYMENT!")
    print("=" * 70)
    print()
    print("📋 Siguiente paso:")
    print("   Ve a Render y haz 'Manual Deploy' → 'Clear build cache & deploy'")
    print()
    
except Exception as e:
    print()
    print("=" * 70)
    print("❌ ERROR ENCONTRADO:")
    print("=" * 70)
    print()
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensaje: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)
