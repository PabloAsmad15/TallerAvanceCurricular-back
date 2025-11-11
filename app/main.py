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

# CORS - Usar variable de entorno ALLOWED_ORIGINS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
