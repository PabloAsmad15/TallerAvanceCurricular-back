"""
Script para exportar convalidaciones de la base de datos local
y luego importarlas a Supabase (producción)
"""
import os
import sys
from pathlib import Path
import csv
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Convalidacion, Curso, Malla

# Cargar variables de entorno
load_dotenv()

def export_convalidaciones_from_local():
    """Exporta convalidaciones de la BD local a CSV"""
    
    # Conectar a BD local
    local_db_url = os.getenv("DATABASE_URL", "postgresql://postgres:paadmin@localhost:5432/avance-curricular")
    print(f"🔌 Conectando a BD local: avance-curricular...")
    
    engine = create_engine(local_db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Usar query SQL directo (ORM no está trayendo los datos)
        from sqlalchemy import text
        query = text("""
            SELECT 
                c.id,
                c.curso_origen_id,
                c.curso_destino_id,
                c.malla_origen_anio,
                c.malla_destino_anio,
                co.codigo as origen_codigo,
                co.nombre as origen_nombre,
                cd.codigo as destino_codigo,
                cd.nombre as destino_nombre
            FROM convalidaciones c
            LEFT JOIN cursos co ON c.curso_origen_id = co.id
            LEFT JOIN cursos cd ON c.curso_destino_id = cd.id
        """)
        
        result = db.execute(query)
        convalidaciones_raw = result.fetchall()
        total = len(convalidaciones_raw)
        
        print(f"📊 Total de convalidaciones en local: {total}")
        
        if total == 0:
            print("⚠️  No hay convalidaciones para exportar")
            return
        
        # Crear archivo CSV
        output_file = "convalidaciones_export.csv"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Encabezados
            writer.writerow([
                'id',
                'curso_origen_id', 
                'curso_origen_codigo',
                'curso_origen_nombre',
                'malla_origen_anio',
                'curso_destino_id',
                'curso_destino_codigo', 
                'curso_destino_nombre',
                'malla_destino_anio'
            ])
            
            # Datos
            for row in convalidaciones_raw:
                # row es una tupla con: (id, curso_origen_id, curso_destino_id, 
                #                        malla_origen_anio, malla_destino_anio,
                #                        origen_codigo, origen_nombre, 
                #                        destino_codigo, destino_nombre)
                writer.writerow([
                    row[0],  # id
                    row[1],  # curso_origen_id
                    row[5],  # origen_codigo
                    row[6],  # origen_nombre
                    row[3],  # malla_origen_anio
                    row[2],  # curso_destino_id
                    row[7],  # destino_codigo
                    row[8],  # destino_nombre
                    row[4]   # malla_destino_anio
                ])
        
        print(f"✅ Convalidaciones exportadas a: {output_file}")
        print(f"📝 Total de registros exportados: {total}")
        
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def import_convalidaciones_to_supabase():
    """Importa convalidaciones desde CSV a Supabase"""
    
    csv_file = "convalidaciones_export.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Archivo {csv_file} no encontrado")
        print("   Ejecuta primero la exportación desde local")
        return
    
    # Conectar a Supabase (Session Pooler)
    supabase_url = os.getenv("SUPABASE_DATABASE_URL")
    if not supabase_url:
        print("❌ SUPABASE_DATABASE_URL no configurada en .env")
        return
    
    print(f"🔌 Conectando a Supabase...")
    
    engine = create_engine(supabase_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Leer CSV
        convalidaciones_importar = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                convalidaciones_importar.append(row)
        
        print(f"📊 Total de convalidaciones en CSV: {len(convalidaciones_importar)}")
        
        # Verificar cuántas ya existen en Supabase
        existentes = db.query(Convalidacion).count()
        print(f"📊 Convalidaciones existentes en Supabase: {existentes}")
        
        # Importar
        nuevas = 0
        duplicadas = 0
        errores = 0
        
        for i, row in enumerate(convalidaciones_importar, 1):
            try:
                curso_origen_id = int(row['curso_origen_id'])
                curso_destino_id = int(row['curso_destino_id'])
                
                # Verificar si ya existe
                existing = db.query(Convalidacion).filter(
                    Convalidacion.curso_origen_id == curso_origen_id,
                    Convalidacion.curso_destino_id == curso_destino_id
                ).first()
                
                if existing:
                    duplicadas += 1
                    print(f"⚠️  [{i}/{len(convalidaciones_importar)}] Ya existe: {row['curso_origen_codigo']} → {row['curso_destino_codigo']}")
                else:
                    # Crear nueva convalidación
                    conv = Convalidacion(
                        curso_origen_id=curso_origen_id,
                        curso_destino_id=curso_destino_id,
                        malla_origen_anio=int(row['malla_origen_anio']) if row.get('malla_origen_anio') else None,
                        malla_destino_anio=int(row['malla_destino_anio']) if row.get('malla_destino_anio') else None
                    )
                    
                    db.add(conv)
                    nuevas += 1
                    
                    if nuevas % 10 == 0:
                        print(f"✅ [{i}/{len(convalidaciones_importar)}] Importadas: {nuevas}")
                        db.commit()
            
            except Exception as e:
                errores += 1
                print(f"❌ Error en registro {i}: {e}")
                db.rollback()
        
        # Commit final
        db.commit()
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE IMPORTACIÓN")
        print("="*60)
        print(f"✅ Nuevas convalidaciones importadas: {nuevas}")
        print(f"⚠️  Duplicadas (omitidas): {duplicadas}")
        print(f"❌ Errores: {errores}")
        print(f"📊 Total en Supabase ahora: {db.query(Convalidacion).count()}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error al importar: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def main():
    """Función principal"""
    print("="*60)
    print("🔄 SINCRONIZACIÓN DE CONVALIDACIONES")
    print("="*60)
    print()
    
    # Permitir argumento de línea de comandos
    if len(sys.argv) > 1:
        opcion = sys.argv[1]
    else:
        print("Opciones:")
        print("1. Exportar desde BD local a CSV")
        print("2. Importar desde CSV a Supabase")
        print("3. Hacer ambas (Exportar + Importar)")
        print()
        opcion = input("Selecciona una opción (1/2/3): ").strip()
    
    if opcion == "1":
        print("\n📤 Exportando desde local...")
        export_convalidaciones_from_local()
    
    elif opcion == "2":
        print("\n📥 Importando a Supabase...")
        import_convalidaciones_to_supabase()
    
    elif opcion == "3":
        print("\n📤 Paso 1: Exportando desde local...")
        export_convalidaciones_from_local()
        
        print("\n📥 Paso 2: Importando a Supabase...")
        import_convalidaciones_to_supabase()
    
    else:
        print("❌ Opción inválida")


if __name__ == "__main__":
    main()
