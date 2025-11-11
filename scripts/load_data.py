"""
Script para cargar datos de mallas curriculares desde CSV.

Uso:
    python scripts/load_data.py

Estructura esperada de CSVs:
- data/mallas/malla_2015.csv
- data/mallas/malla_2019.csv
- data/mallas/malla_2022.csv
- data/mallas/malla_2025.csv
- data/mallas/convalidaciones.csv

Formato CSV de mallas:
codigo,nombre,creditos,ciclo,tipo,prerequisitos

Formato CSV de convalidaciones:
curso_origen_codigo,curso_destino_codigo,malla_origen,malla_destino
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Malla, Curso, Prerequisito, Convalidacion

# Crear tablas
Base.metadata.create_all(bind=engine)


def load_mallas(db: Session):
    """Cargar definiciones de mallas"""
    mallas_data = [
        {"anio": 2015, "nombre": "Malla Curricular 2015", "descripcion": "Plan de estudios 2015"},
        {"anio": 2019, "nombre": "Malla Curricular 2019", "descripcion": "Plan de estudios 2019"},
        {"anio": 2022, "nombre": "Malla Curricular 2022", "descripcion": "Plan de estudios 2022"},
        {"anio": 2025, "nombre": "Malla Curricular 2025", "descripcion": "Plan de estudios 2025 (vigente)"},
    ]
    
    for malla_data in mallas_data:
        # Verificar si ya existe
        existing = db.query(Malla).filter(Malla.anio == malla_data["anio"]).first()
        if not existing:
            malla = Malla(**malla_data)
            db.add(malla)
            print(f"✅ Malla {malla_data['anio']} creada")
        else:
            print(f"⏭️  Malla {malla_data['anio']} ya existe")
    
    db.commit()


def load_cursos_from_csv(db: Session, csv_path: str, malla_anio: int):
    """Cargar cursos desde CSV"""
    
    if not os.path.exists(csv_path):
        print(f"⚠️  Archivo no encontrado: {csv_path}")
        print(f"   Por favor crea el archivo CSV con el formato:")
        print(f"   codigo,nombre,creditos,ciclo,tipo,prerequisitos")
        return
    
    # Obtener malla
    malla = db.query(Malla).filter(Malla.anio == malla_anio).first()
    if not malla:
        print(f"❌ Malla {malla_anio} no encontrada")
        return
    
    # Leer CSV con punto y coma como delimitador
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    
    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip()
    column_mapping = {
        'Código': 'codigo',
        'Codigo': 'codigo',
        'Nombre de la asignatura': 'nombre',
        'Nombre': 'nombre',
        'Creditos': 'creditos',
        'Créditos': 'creditos',
        'Ciclo': 'ciclo',
        'Prerrequisitos': 'prerequisitos',
        'Prerequisitos': 'prerequisitos'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    # Convertir ciclo romano a número si es necesario
    ciclo_map = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
    }
    if df['ciclo'].dtype == 'object':
        df['ciclo'] = df['ciclo'].map(lambda x: ciclo_map.get(x.strip(), x) if isinstance(x, str) else x)
    
    cursos_dict = {}  # codigo -> id
    
    # Primera pasada: crear cursos
    for _, row in df.iterrows():
        codigo = row['codigo'].strip()
        
        # Verificar si ya existe
        existing = db.query(Curso).filter(
            Curso.malla_id == malla.id,
            Curso.codigo == codigo
        ).first()
        
        if not existing:
            curso = Curso(
                malla_id=malla.id,
                codigo=codigo,
                nombre=row['nombre'].strip(),
                creditos=int(row['creditos']),
                ciclo=int(row['ciclo']),
                tipo=row.get('tipo', 'Obligatorio').strip() if pd.notna(row.get('tipo')) else 'Obligatorio'
            )
            db.add(curso)
            db.flush()  # Para obtener el ID
            cursos_dict[codigo] = curso.id
            print(f"   ✅ Curso creado: {codigo} - {curso.nombre}")
        else:
            cursos_dict[codigo] = existing.id
    
    db.commit()
    
    # Segunda pasada: crear prerequisitos
    for _, row in df.iterrows():
        codigo = row['codigo'].strip()
        prerequisitos_str = row.get('prerequisitos', '')
        
        if pd.notna(prerequisitos_str) and prerequisitos_str and str(prerequisitos_str).upper() != 'NINGUNO':
            prerequisitos_list = [p.strip() for p in str(prerequisitos_str).split(',')]
            
            for prereq_codigo in prerequisitos_list:
                if prereq_codigo and prereq_codigo != 'NINGUNO' and prereq_codigo in cursos_dict:
                    # Verificar si ya existe
                    existing_prereq = db.query(Prerequisito).filter(
                        Prerequisito.curso_id == cursos_dict[codigo],
                        Prerequisito.prerequisito_id == cursos_dict[prereq_codigo]
                    ).first()
                    
                    if not existing_prereq:
                        prerequisito = Prerequisito(
                            curso_id=cursos_dict[codigo],
                            prerequisito_id=cursos_dict[prereq_codigo]
                        )
                        db.add(prerequisito)
    
    db.commit()
    print(f"✅ Malla {malla_anio} cargada exitosamente")


def load_convalidaciones(db: Session, csv_path: str):
    """Cargar convalidaciones desde CSV"""
    
    if not os.path.exists(csv_path):
        print(f"⚠️  Archivo de convalidaciones no encontrado: {csv_path}")
        return
    
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # El CSV tiene formato: Malla_Origen;Codigo_Origen;Codigo_Destino_2025
        # Asumimos que el destino es siempre malla 2025
        malla_destino_anio = 2025
        malla_d = db.query(Malla).filter(Malla.anio == malla_destino_anio).first()
        
        if not malla_d:
            print(f"⚠️  Malla destino {malla_destino_anio} no encontrada")
            return
        
        for _, row in df.iterrows():
            malla_origen = int(row['Malla_Origen'])
            curso_origen_codigo = str(row['Codigo_Origen']).strip()
            curso_destino_codigo = str(row['Codigo_Destino_2025']).strip()
            
            # Buscar cursos
            malla_o = db.query(Malla).filter(Malla.anio == malla_origen).first()
            
            if not malla_o:
                continue
            
            curso_o = db.query(Curso).filter(
                Curso.malla_id == malla_o.id,
                Curso.codigo == curso_origen_codigo
            ).first()
            
            curso_d = db.query(Curso).filter(
                Curso.malla_id == malla_d.id,
                Curso.codigo == curso_destino_codigo
            ).first()
            
            if curso_o and curso_d:
                # Verificar si ya existe
                existing = db.query(Convalidacion).filter(
                    Convalidacion.curso_origen_id == curso_o.id,
                    Convalidacion.curso_destino_id == curso_d.id
                ).first()
                
                if not existing:
                    convalidacion = Convalidacion(
                        curso_origen_id=curso_o.id,
                        curso_destino_id=curso_d.id,
                        malla_origen_anio=malla_origen,
                        malla_destino_anio=malla_destino_anio
                    )
                    db.add(convalidacion)
        
        db.commit()
        print(f"✅ Convalidaciones cargadas")
    except Exception as e:
        print(f"⚠️  Error al cargar convalidaciones: {e}")
        print(f"   Se omitirá la carga de convalidaciones")


def main():
    """Función principal"""
    print("🚀 Iniciando carga de datos...")
    
    db = SessionLocal()
    
    try:
        # 1. Cargar mallas
        print("\n📚 Cargando mallas...")
        load_mallas(db)
        
        # 2. Cargar cursos de cada malla
        data_dir = Path(__file__).parent.parent / "data" / "mallas"
        
        print("\n📖 Cargando cursos...")
        for anio in [2015, 2019, 2022, 2025]:
            csv_path = data_dir / f"malla_{anio}.csv"
            print(f"\n   Procesando malla {anio}...")
            load_cursos_from_csv(db, str(csv_path), anio)
        
        # 3. Cargar convalidaciones
        print("\n🔄 Cargando convalidaciones...")
        conval_path = data_dir / "convalidaciones.csv"
        load_convalidaciones(db, str(conval_path))
        
        print("\n✅ ¡Datos cargados exitosamente!")
        print("\n📊 Resumen:")
        print(f"   - Mallas: {db.query(Malla).count()}")
        print(f"   - Cursos: {db.query(Curso).count()}")
        print(f"   - Prerequisitos: {db.query(Prerequisito).count()}")
        print(f"   - Convalidaciones: {db.query(Convalidacion).count()}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
