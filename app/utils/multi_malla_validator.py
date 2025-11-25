"""
Validador y convalidador de cursos de múltiples mallas
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Set, Tuple
from ..models import Curso, Convalidacion


def procesar_cursos_multi_malla(
    db: Session,
    malla_destino_anio: int,
    cursos_aprobados_multi_malla: List[Dict[str, any]]
) -> Tuple[List[int], Dict[str, any]]:
    """
    Procesa cursos aprobados de múltiples mallas y los convalida a la malla destino.
    
    Args:
        db: Sesión de base de datos
        malla_destino_anio: Año de la malla objetivo (ej: 2025)
        cursos_aprobados_multi_malla: Lista de {"codigo": "MATE-101", "malla_origen_anio": 2019}
    
    Returns:
        Tuple[List[int], Dict]: 
            - Lista de IDs de cursos convalidados en la malla destino
            - Diccionario con información de convalidación
    """
    
    print(f"\n{'='*60}")
    print(f"PROCESANDO CURSOS DE MÚLTIPLES MALLAS")
    print(f"{'='*60}")
    print(f"Malla destino: {malla_destino_anio}")
    print(f"Total cursos a procesar: {len(cursos_aprobados_multi_malla)}\n")
    
    cursos_convalidados_ids = []
    info_convalidacion = {
        "cursos_procesados": 0,
        "cursos_convalidados": 0,
        "cursos_ya_en_malla_destino": 0,
        "cursos_sin_convalidacion": 0,
        "detalles": []
    }
    
    # Agrupar por malla origen
    cursos_por_malla = {}
    for curso_data in cursos_aprobados_multi_malla:
        malla_origen = curso_data.get("malla_origen_anio")
        if malla_origen not in cursos_por_malla:
            cursos_por_malla[malla_origen] = []
        cursos_por_malla[malla_origen].append(curso_data.get("codigo"))
    
    print(f"📊 Cursos agrupados por malla:")
    for malla, codigos in cursos_por_malla.items():
        print(f"   Malla {malla}: {len(codigos)} cursos")
    print()
    
    # Procesar cada malla
    for malla_origen_anio, codigos in cursos_por_malla.items():
        print(f"🔍 Procesando Malla {malla_origen_anio} → {malla_destino_anio}")
        print(f"{'='*60}")
        
        # Si ya es la malla destino, no necesita convalidación
        if malla_origen_anio == malla_destino_anio:
            print(f"✓ Cursos ya son de la malla destino ({malla_destino_anio})")
            
            for codigo in codigos:
                curso = db.query(Curso).join(Curso.malla).filter(
                    Curso.codigo == codigo,
                    Curso.malla.has(anio=malla_destino_anio)
                ).first()
                
                if curso:
                    cursos_convalidados_ids.append(curso.id)
                    info_convalidacion["cursos_ya_en_malla_destino"] += 1
                    info_convalidacion["detalles"].append({
                        "codigo": codigo,
                        "malla_origen": malla_origen_anio,
                        "tipo": "mismo_malla",
                        "curso_destino_id": curso.id,
                        "curso_destino_codigo": curso.codigo
                    })
                    print(f"   ✓ {codigo} → ID {curso.id}")
            
            info_convalidacion["cursos_procesados"] += len(codigos)
            print()
            continue
        
        # Buscar convalidaciones
        for codigo in codigos:
            # 1. Buscar curso en malla origen
            curso_origen = db.query(Curso).join(Curso.malla).filter(
                Curso.codigo == codigo,
                Curso.malla.has(anio=malla_origen_anio)
            ).first()
            
            if not curso_origen:
                print(f"   ⚠️  {codigo}: No encontrado en malla {malla_origen_anio}")
                info_convalidacion["cursos_sin_convalidacion"] += 1
                info_convalidacion["detalles"].append({
                    "codigo": codigo,
                    "malla_origen": malla_origen_anio,
                    "tipo": "no_encontrado",
                    "error": f"No existe en malla {malla_origen_anio}"
                })
                continue
            
            # 2. Buscar convalidación hacia malla destino
            convalidacion = db.query(Convalidacion).filter(
                Convalidacion.curso_origen_id == curso_origen.id,
                Convalidacion.malla_origen_anio == malla_origen_anio,
                Convalidacion.malla_destino_anio == malla_destino_anio
            ).first()
            
            if convalidacion:
                # Obtener curso destino
                curso_destino = db.query(Curso).filter(
                    Curso.id == convalidacion.curso_destino_id
                ).first()
                
                if curso_destino:
                    cursos_convalidados_ids.append(curso_destino.id)
                    info_convalidacion["cursos_convalidados"] += 1
                    info_convalidacion["detalles"].append({
                        "codigo": codigo,
                        "malla_origen": malla_origen_anio,
                        "tipo": "convalidado",
                        "curso_destino_id": curso_destino.id,
                        "curso_destino_codigo": curso_destino.codigo,
                        "curso_destino_nombre": curso_destino.nombre
                    })
                    print(f"   ✓ {codigo} → {curso_destino.codigo} (ID {curso_destino.id})")
                else:
                    print(f"   ⚠️  {codigo}: Convalidación existe pero curso destino no encontrado")
            else:
                # No hay convalidación, intentar buscar por código en malla destino
                curso_mismo_codigo = db.query(Curso).join(Curso.malla).filter(
                    Curso.codigo == codigo,
                    Curso.malla.has(anio=malla_destino_anio)
                ).first()
                
                if curso_mismo_codigo:
                    cursos_convalidados_ids.append(curso_mismo_codigo.id)
                    info_convalidacion["cursos_convalidados"] += 1
                    info_convalidacion["detalles"].append({
                        "codigo": codigo,
                        "malla_origen": malla_origen_anio,
                        "tipo": "mismo_codigo",
                        "curso_destino_id": curso_mismo_codigo.id,
                        "curso_destino_codigo": curso_mismo_codigo.codigo,
                        "curso_destino_nombre": curso_mismo_codigo.nombre
                    })
                    print(f"   ✓ {codigo} → {codigo} (mismo código, ID {curso_mismo_codigo.id})")
                else:
                    print(f"   ⚠️  {codigo}: Sin convalidación a malla {malla_destino_anio}")
                    info_convalidacion["cursos_sin_convalidacion"] += 1
                    info_convalidacion["detalles"].append({
                        "codigo": codigo,
                        "malla_origen": malla_origen_anio,
                        "tipo": "sin_convalidacion",
                        "error": f"No hay equivalente en malla {malla_destino_anio}"
                    })
            
            info_convalidacion["cursos_procesados"] += 1
        
        print()
    
    # Resumen
    print(f"\n{'='*60}")
    print(f"RESUMEN DE CONVALIDACIÓN")
    print(f"{'='*60}")
    print(f"Total procesados: {info_convalidacion['cursos_procesados']}")
    print(f"✓ Ya en malla destino: {info_convalidacion['cursos_ya_en_malla_destino']}")
    print(f"✓ Convalidados: {info_convalidacion['cursos_convalidados']}")
    print(f"✗ Sin convalidación: {info_convalidacion['cursos_sin_convalidacion']}")
    print(f"Total IDs para recomendación: {len(cursos_convalidados_ids)}")
    print(f"{'='*60}\n")
    
    # Eliminar duplicados
    cursos_convalidados_ids = list(set(cursos_convalidados_ids))
    
    return cursos_convalidados_ids, info_convalidacion


def validar_cursos_multi_malla(
    db: Session,
    cursos_aprobados_multi_malla: List[Dict[str, any]]
) -> Dict[str, any]:
    """
    Valida que los cursos existen en sus respectivas mallas.
    
    Returns:
        Dict con resultado de validación
    """
    
    resultados = {
        "valido": True,
        "errores": [],
        "cursos_validados": []
    }
    
    for curso_data in cursos_aprobados_multi_malla:
        codigo = curso_data.get("codigo")
        malla_anio = curso_data.get("malla_origen_anio")
        
        curso = db.query(Curso).join(Curso.malla).filter(
            Curso.codigo == codigo,
            Curso.malla.has(anio=malla_anio)
        ).first()
        
        if curso:
            resultados["cursos_validados"].append({
                "codigo": codigo,
                "malla_anio": malla_anio,
                "curso_id": curso.id,
                "nombre": curso.nombre,
                "creditos": curso.creditos
            })
        else:
            resultados["valido"] = False
            resultados["errores"].append(
                f"Curso {codigo} no encontrado en malla {malla_anio}"
            )
    
    return resultados
