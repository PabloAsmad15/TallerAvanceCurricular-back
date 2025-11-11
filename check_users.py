import psycopg2

conn = psycopg2.connect('postgresql://postgres:paadmin@localhost:5432/avance-curricular')
cur = conn.cursor()

cur.execute("SELECT id, email, nombre, apellido, is_admin FROM usuarios")
users = cur.fetchall()

print("📊 Usuarios en la base de datos:\n")
for user in users:
    print(f"ID: {user[0]}")
    print(f"Email: {user[1]}")
    print(f"Nombre: {user[2]} {user[3]}")
    print(f"Es Admin: {user[4]}")
    print("-" * 50)

cur.close()
conn.close()
