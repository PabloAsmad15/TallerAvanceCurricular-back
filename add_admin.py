import psycopg2

# Conectar a la base de datos
conn = psycopg2.connect('postgresql://postgres:paadmin@localhost:5432/avance-curricular')
cur = conn.cursor()

# Agregar columna is_admin si no existe
cur.execute('ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE')

# Marcar tu usuario como administrador
cur.execute("UPDATE usuarios SET is_admin = TRUE WHERE email = 'pasmadm1@upao.edu.pe'")

# Confirmar cambios
conn.commit()

# Verificar
cur.execute("SELECT email, nombre, is_admin FROM usuarios WHERE email = 'pasmadm1@upao.edu.pe'")
result = cur.fetchone()

if result:
    print(f"✅ Usuario actualizado:")
    print(f"   Email: {result[0]}")
    print(f"   Nombre: {result[1]}")
    print(f"   Es Admin: {result[2]}")
else:
    print("⚠️  Usuario no encontrado")

# Cerrar conexión
cur.close()
conn.close()

print("\n✅ Cambios aplicados correctamente")
