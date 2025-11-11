import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import Usuario
from app.utils.security import verify_password, get_password_hash

def check_admin():
    db = SessionLocal()
    try:
        # Buscar el admin
        admin = db.query(Usuario).filter(Usuario.email == "admin1502@upao.edu.pe").first()
        
        if not admin:
            print("❌ Usuario admin1502@upao.edu.pe NO encontrado")
            return
        
        print(f"✅ Usuario encontrado:")
        print(f"   Email: {admin.email}")
        print(f"   Nombre: {admin.nombre} {admin.apellido}")
        print(f"   Is Admin: {admin.is_admin}")
        print(f"   Is Active: {admin.is_active}")
        print(f"   Password Hash: {admin.password_hash[:50]}...")
        
        # Probar la contraseña
        password = "12345678"
        if verify_password(password, admin.password_hash):
            print(f"\n✅ La contraseña '{password}' es CORRECTA")
        else:
            print(f"\n❌ La contraseña '{password}' es INCORRECTA")
            print("\nGenerando nuevo hash correcto...")
            new_hash = get_password_hash(password)
            print(f"Nuevo hash: {new_hash}")
            
            # Actualizar
            admin.password_hash = new_hash
            db.commit()
            print("✅ Contraseña actualizada")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
