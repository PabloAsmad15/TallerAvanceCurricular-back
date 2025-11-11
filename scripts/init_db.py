"""
Script para inicializar la base de datos
"""
from app.database import engine, Base
from app.models import (
    Usuario, Malla, Curso, Prerequisito, 
    Convalidacion, Recomendacion, PasswordReset
)

def init_db():
    """Crea todas las tablas en la base de datos"""
    print("🚀 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ ¡Tablas creadas exitosamente!")

if __name__ == "__main__":
    init_db()
