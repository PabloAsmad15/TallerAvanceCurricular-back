"""
Utilidades para validar cursos aprobados y prerequisitos
"""
from typing import List, Tuple, Set
from sqlalchemy.orm import Session
from app.models import Curso, Prerequisito, Convalidacion, Malla


def validar_cursos_aprobados(
    db: Session,
    malla_id: int,
    codigos_aprobados: List[str]
) -> Tuple[bool, List[str], List[dict]]:
    """
    Valida que los cursos marcados como aprobados cumplan con los prerequisitos.
    También considera convalidaciones.
    
    ⚠️ IMPORTANTE: Esta validación permite selecciones parciales de ciclos.
    Solo valida que los prerequisitos directos de cada curso estén aprobados.
    
    Args:
        db: Sesión de base de datos
        malla_id: ID de la malla curricular
        codigos_aprobados: Lista de códigos de cursos marcados como aprobados
        
    Returns:
        Tuple con:
        - bool: True si todos los cursos son válidos
        - List[str]: Lista de errores encontrados
        - List[dict]: Lista de advertencias (cursos que podrían estar mal seleccionados)
    """
    errores = []
    advertencias = []
    
    # Si no hay cursos aprobados, retornar válido (caso inicial)
    if not codigos_aprobados or len(codigos_aprobados) == 0:
        return True, [], []
    
    # Obtener todos los cursos de la malla con sus prerequisitos
    cursos = db.query(Curso).filter(Curso.malla_id == malla_id).all()
    cursos_dict = {c.codigo: c for c in cursos}
    
    # Obtener malla info
    malla = db.query(Malla).filter(Malla.id == malla_id).first()
    if not malla:
        errores.append("Malla no encontrada")
        return False, errores, advertencias
    
    # Obtener todas las convalidaciones que involucran esta malla
    convalidaciones = db.query(Convalidacion).filter(
        (Convalidacion.malla_destino_anio == malla.anio) |
        (Convalidacion.malla_origen_anio == malla.anio)
    ).all()
    
    # Crear mapa de convalidaciones bidireccional
    convalidaciones_map = {}
    for conv in convalidaciones:
        curso_destino = db.query(Curso).filter(Curso.id == conv.curso_destino_id).first()
        curso_origen = db.query(Curso).filter(Curso.id == conv.curso_origen_id).first()
        if curso_destino and curso_origen:
            # Mapeo: curso_destino puede ser cubierto por curso_origen
            if curso_destino.codigo not in convalidaciones_map:
                convalidaciones_map[curso_destino.codigo] = []
            convalidaciones_map[curso_destino.codigo].append(curso_origen.codigo)
            
            # Mapeo inverso: curso_origen puede cubrir curso_destino
            if curso_origen.codigo not in convalidaciones_map:
                convalidaciones_map[curso_origen.codigo] = []
            convalidaciones_map[curso_origen.codigo].append(curso_destino.codigo)
    
    # Validar cada curso aprobado
    cursos_aprobados_set = set(codigos_aprobados)
    
    # Agrupar cursos por ciclo para análisis
    cursos_por_ciclo = {}
    for codigo in codigos_aprobados:
        if codigo in cursos_dict:
            ciclo = cursos_dict[codigo].ciclo
            if ciclo not in cursos_por_ciclo:
                cursos_por_ciclo[ciclo] = []
            cursos_por_ciclo[ciclo].append(codigo)
    
    print(f"📊 Validando {len(codigos_aprobados)} cursos en {len(cursos_por_ciclo)} ciclos diferentes")
    
    for codigo in codigos_aprobados:
        if codigo not in cursos_dict:
            errores.append(f"❌ El curso {codigo} no existe en la malla {malla.anio}")
            continue
        
        curso = cursos_dict[codigo]
        
        # Obtener prerequisitos del curso
        prerequisitos = db.query(Prerequisito).filter(
            Prerequisito.curso_id == curso.id
        ).all()
        
        if not prerequisitos:
            # Sin prerequisitos, siempre válido
            continue
        
        prerequisitos_faltantes = []
        
        for prereq in prerequisitos:
            curso_prereq = db.query(Curso).filter(Curso.id == prereq.prerequisito_id).first()
            if not curso_prereq:
                continue
            
            # Verificar si el prerequisito está aprobado directamente
            prereq_aprobado = curso_prereq.codigo in cursos_aprobados_set
            
            # Si no está aprobado directamente, verificar convalidaciones
            if not prereq_aprobado and curso_prereq.codigo in convalidaciones_map:
                cursos_convalidables = convalidaciones_map[curso_prereq.codigo]
                prereq_aprobado = any(c in cursos_aprobados_set for c in cursos_convalidables)
            
            if not prereq_aprobado:
                prerequisitos_faltantes.append(f"{curso_prereq.codigo} - {curso_prereq.nombre}")
        
        if prerequisitos_faltantes:
            # Solo agregar error si es un curso de ciclo avanzado (3+)
            # Los cursos de ciclos 1-2 generalmente no tienen prerequisitos complejos
            if curso.ciclo >= 3:
                errores.append(
                    f"❌ {curso.codigo} ({curso.nombre}): "
                    f"Falta(n) prerequisito(s): {', '.join(prerequisitos_faltantes)}"
                )
            else:
                # Para ciclos tempranos, solo advertir
                advertencias.append({
                    "tipo": "prerequisito_ciclo_temprano",
                    "mensaje": f"⚠️ {curso.codigo} tiene prerequisito(s) no marcado(s): {', '.join(prerequisitos_faltantes)}",
                    "curso": curso.codigo,
                    "prerequisitos_faltantes": prerequisitos_faltantes
                })
    
    # Generar advertencias inteligentes
    if cursos_aprobados_set and cursos_por_ciclo:
        ciclo_max = max(cursos_por_ciclo.keys())
        ciclo_min = min(cursos_por_ciclo.keys())
        
        # Advertir sobre saltos grandes de ciclos (más de 2 ciclos sin cursos)
        if ciclo_max - ciclo_min > 2:
            ciclos_vacios = []
            for ciclo in range(ciclo_min + 1, ciclo_max):
                if ciclo not in cursos_por_ciclo:
                    ciclos_vacios.append(ciclo)
            
            if len(ciclos_vacios) > 0:
                advertencias.append({
                    "tipo": "ciclos_saltados",
                    "mensaje": f"⚠️ Tienes cursos del ciclo {ciclo_max} pero ninguno de: {', '.join(map(str, ciclos_vacios))}",
                    "ciclos_faltantes": ciclos_vacios
                })
        
        # Verificar si hay cursos de ciclos muy avanzados sin base
        if ciclo_max >= 7 and 1 not in cursos_por_ciclo:
            advertencias.append({
                "tipo": "sin_base",
                "mensaje": "⚠️ Tienes cursos avanzados pero no marcaste cursos del ciclo 1. Verifica tu selección."
            })
    
    # Resultado de la validación
    es_valido = len(errores) == 0
    
    if es_valido:
        print(f"✅ Validación exitosa: {len(codigos_aprobados)} cursos aprobados en {len(cursos_por_ciclo)} ciclos")
    else:
        print(f"❌ Validación fallida: {len(errores)} error(es) encontrado(s)")
        for error in errores[:3]:  # Mostrar solo los primeros 3
            print(f"   {error}")
    
    if advertencias:
        print(f"⚠️ {len(advertencias)} advertencia(s) encontrada(s)")
    
    return es_valido, errores, advertencias


def obtener_cursos_disponibles(
    db: Session,
    malla_id: int,
    codigos_aprobados: List[str]
) -> List[Curso]:
    """
    Obtiene la lista de cursos que están disponibles para cursar
    dado el conjunto de cursos ya aprobados.
    
    Args:
        db: Sesión de base de datos
        malla_id: ID de la malla curricular
        codigos_aprobados: Lista de códigos de cursos aprobados
        
    Returns:
        Lista de cursos disponibles para cursar
    """
    # Obtener IDs de cursos aprobados
    # Asegurarse de que todos los códigos sean string para evitar error de tipo en Postgres
    codigos_aprobados_str = [str(c) for c in codigos_aprobados]
    cursos_aprobados = db.query(Curso).filter(
        Curso.malla_id == malla_id,
        Curso.codigo.in_(codigos_aprobados_str)
    ).all()
    
    ids_aprobados = set(c.id for c in cursos_aprobados)
    
    # Obtener todos los cursos de la malla
    todos_cursos = db.query(Curso).filter(Curso.malla_id == malla_id).all()
    
    cursos_disponibles = []
    
    for curso in todos_cursos:
        # Si ya está aprobado, no está disponible
        if curso.id in ids_aprobados:
            continue
        
        # Verificar si cumple prerequisitos
        prerequisitos = db.query(Prerequisito).filter(
            Prerequisito.curso_id == curso.id
        ).all()
        
        cumple_prerequisitos = True
        for prereq in prerequisitos:
            if prereq.prerequisito_id not in ids_aprobados:
                cumple_prerequisitos = False
                break
        
        if cumple_prerequisitos:
            cursos_disponibles.append(curso)
    
    return cursos_disponibles
