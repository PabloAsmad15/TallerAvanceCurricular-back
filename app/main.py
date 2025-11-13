from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, recommendations, mallas, cursos, admin
from .database import engine, Base
from .config import settings
from .firebase_config import initialize_firebase
import os

# Crear tablas
Base.metadata.create_all(bind=engine)

# Inicializar Firebase
try:
    initialize_firebase()
    print("✅ Firebase inicializado correctamente")
except Exception as e:
    print(f"⚠️  Error inicializando Firebase: {e}")
    print("El sistema funcionará sin Firebase Auth")

app = FastAPI(
    title="Sistema de Recomendación Curricular UPAO",
    description="API para recomendación de avance curricular con IA",
    version="1.0.0"
)

# CORS - Usar variable de entorno ALLOWED_ORIGINS con soporte para wildcards
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = allowed_origins_str.split(",")

# Agregar soporte para wildcards de Vercel
# Permitir todas las URLs de Vercel que coincidan con el patrón del proyecto
import re
def origin_validator(origin: str) -> bool:
    """Valida si el origen está permitido"""
    # Verificar si está en la lista exacta
    if origin in allowed_origins:
        return True
    
    # Verificar si es un deployment de Vercel del proyecto
    vercel_pattern = r'^https://taller-avance-curricular-front(-[a-z0-9]+)?(-git-[a-z0-9-]+)?(-[a-z0-9]+)?\.vercel\.app$'
    if re.match(vercel_pattern, origin):
        return True
    
    # Verificar localhost
    if origin.startswith("http://localhost:"):
        return True
    
    return False

# Usar allow_origin_regex o configurar middleware personalizado
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://taller-avance-curricular-front.*\.vercel\.app",
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recomendaciones"])
app.include_router(mallas.router, prefix="/api/mallas", tags=["Mallas"])
app.include_router(cursos.router, prefix="/api/cursos", tags=["Cursos"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administración"])


@app.get("/")
def root():
    return {
        "message": "API de Recomendación Curricular UPAO",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
