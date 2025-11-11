from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, recommendations, mallas, cursos, admin
from .database import engine, Base

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Recomendación Curricular UPAO",
    description="API para recomendación de avance curricular con IA",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:3000"
    ],  # Frontend URLs
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
