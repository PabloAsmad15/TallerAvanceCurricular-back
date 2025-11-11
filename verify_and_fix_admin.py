import psycopg2

# Conectar a la base de datos
conn = psycopg2.connect('postgresql://postgres:paadmin@localhost:5432/avance-curricular')
cur = conn.cursor()

print("🔧 Corrigiendo permisos de administrador...\n")

# Primero, hacer a TODOS los usuarios normales
cur.execute("UPDATE usuarios SET is_admin = FALSE")
print("✅ Todos los usuarios configurados como usuarios normales")

# Luego, hacer admin SOLO a admin1502@upao.edu.pe
cur.execute("UPDATE usuarios SET is_admin = TRUE WHERE email = 'admin1502@upao.edu.pe'")
print("✅ admin1502@upao.edu.pe configurado como administrador")

conn.commit()

# Verificar el resultado
cur.execute("SELECT id, email, nombre, apellido, is_admin FROM usuarios ORDER BY id")
usuarios = cur.fetchall()

print("\n📊 Estado FINAL de usuarios:\n")
print(f"{'ID':<5} {'EMAIL':<30} {'NOMBRE':<30} {'ROL':<15}")
print("-" * 80)

for user_id, email, nombre, apellido, is_admin in usuarios:
    nombre_completo = f"{nombre} {apellido}"
    rol = "🔑 ADMINISTRADOR" if is_admin else "👤 Usuario"
    print(f"{user_id:<5} {email:<30} {nombre_completo:<30} {rol:<15}")

# Contar
cur.execute("SELECT COUNT(*) FROM usuarios WHERE is_admin = TRUE")
total_admins = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM usuarios WHERE is_admin = FALSE")
total_usuarios = cur.fetchone()[0]

print("\n" + "=" * 80)
print(f"Total Administradores: {total_admins}")
print(f"Total Usuarios Normales: {total_usuarios}")
print("=" * 80)

if total_admins == 1:
    print("\n✅ CORRECTO: Solo hay 1 administrador en el sistema")
else:
    print(f"\n⚠️  ADVERTENCIA: Hay {total_admins} administradores")

cur.close()
conn.close()
