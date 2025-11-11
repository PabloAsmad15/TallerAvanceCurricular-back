import psycopg2

# Conectar a la base de datos
conn = psycopg2.connect('postgresql://postgres:paadmin@localhost:5432/avance-curricular')
cur = conn.cursor()

# Quitar admin de tu usuario personal
cur.execute("UPDATE usuarios SET is_admin = FALSE WHERE email = 'pasmadm1@upao.edu.pe'")

# Asegurar que solo admin1502 sea admin
cur.execute("UPDATE usuarios SET is_admin = FALSE WHERE email != 'admin1502@upao.edu.pe'")
cur.execute("UPDATE usuarios SET is_admin = TRUE WHERE email = 'admin1502@upao.edu.pe'")

conn.commit()

# Verificar
cur.execute("SELECT email, nombre, apellido, is_admin FROM usuarios ORDER BY is_admin DESC")
usuarios = cur.fetchall()

print("📊 Estado actual de usuarios:\n")
for email, nombre, apellido, is_admin in usuarios:
    admin_badge = "🔑 ADMIN" if is_admin else "👤 Usuario"
    print(f"{admin_badge} | {email} | {nombre} {apellido}")

cur.close()
conn.close()

print("\n✅ Permisos actualizados correctamente")
print("✅ Solo admin1502@upao.edu.pe tiene permisos de administrador")
