import psycopg2
from passlib.context import CryptContext

# Configurar bcrypt para hashear la contraseña
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Conectar a la base de datos
conn = psycopg2.connect('postgresql://postgres:paadmin@localhost:5432/avance-curricular')
cur = conn.cursor()

# Datos del administrador
email = "admin1502@upao.edu.pe"
password = "12345678"
nombre = "Administrador"
apellido = "Sistema"

# Hashear la contraseña
password_hash = pwd_context.hash(password)

# Verificar si el usuario ya existe
cur.execute("SELECT id, email FROM usuarios WHERE email = %s", (email,))
existing = cur.fetchone()

if existing:
    # Si existe, actualizarlo
    cur.execute("""
        UPDATE usuarios 
        SET password_hash = %s, is_admin = TRUE, nombre = %s, apellido = %s
        WHERE email = %s
    """, (password_hash, nombre, apellido, email))
    print(f"✅ Usuario {email} actualizado como administrador")
else:
    # Si no existe, crearlo
    cur.execute("""
        INSERT INTO usuarios (email, password_hash, nombre, apellido, is_active, is_admin)
        VALUES (%s, %s, %s, %s, TRUE, TRUE)
    """, (email, password_hash, nombre, apellido))
    print(f"✅ Usuario administrador {email} creado")

# Confirmar cambios
conn.commit()

# Verificar
cur.execute("SELECT id, email, nombre, apellido, is_admin FROM usuarios WHERE email = %s", (email,))
result = cur.fetchone()

print("\n📊 Datos del administrador:")
print(f"   ID: {result[0]}")
print(f"   Email: {result[1]}")
print(f"   Nombre: {result[2]} {result[3]}")
print(f"   Es Admin: {result[4]}")
print(f"   Contraseña: {password}")

# Cerrar conexión
cur.close()
conn.close()

print("\n✅ Administrador configurado correctamente")
print(f"\n🔐 Credenciales de acceso:")
print(f"   Email: {email}")
print(f"   Contraseña: {password}")
