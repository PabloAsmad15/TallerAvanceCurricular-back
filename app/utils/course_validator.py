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
    
    # Obtener todos los cursos de la malla con sus prerequisitos
    cursos = db.query(Curso).filter(Curso.malla_id == malla_id).all()
    cursos_dict = {c.codigo: c for c in cursos}
    
    # Obtener todas las convalidaciones que involucran esta malla
    convalidaciones = db.query(Convalidacion).filter(
        (Convalidacion.malla_destino_anio == db.query(Malla.anio).filter(Malla.id == malla_id).scalar())
    ).all()
    
    # Crear mapa de convalidaciones: curso_destino -> [cursos_origen]
    convalidaciones_map = {}
    for conv in convalidaciones:
        curso_destino = db.query(Curso).filter(Curso.id == conv.curso_destino_id).first()
        curso_origen = db.query(Curso).filter(Curso.id == conv.curso_origen_id).first()
        if curso_destino and curso_origen:
            if curso_destino.codigo not in convalidaciones_map:
                convalidaciones_map[curso_destino.codigo] = []
            convalidaciones_map[curso_destino.codigo].append(curso_origen.codigo)
    
    # Validar cada curso aprobado
    cursos_aprobados_set = set(codigos_aprobados)
    
    for codigo in codigos_aprobados:
        if codigo not in cursos_dict:
            errores.append(f"El curso {codigo} no existe en la malla seleccionada")
            continue
        
        curso = cursos_dict[codigo]
        
        # Obtener prerequisitos del curso
        prerequisitos = db.query(Prerequisito).filter(
            Prerequisito.curso_id == curso.id
        ).all()
        
        if prerequisitos:
            prerequisitos_faltantes = []
            
            for prereq in prerequisitos:
                curso_prereq = db.query(Curso).filter(Curso.id == prereq.prerequisito_id).first()
                if not curso_prereq:
                    continue
                
                # Verificar si el prerequisito está aprobado directamente
                prereq_aprobado = curso_prereq.codigo in cursos_aprobados_set
                
                # Si no está aprobado directamente, verificar si hay convalidación
                if not prereq_aprobado:
                    # Verificar si algún curso convalidado por el estudiante equivale a este prerequisito
                    if curso_prereq.codigo in convalidaciones_map:
                        cursos_convalidables = convalidaciones_map[curso_prereq.codigo]
                        prereq_aprobado = any(c in cursos_aprobados_set for c in cursos_convalidables)
                
                if not prereq_aprobado:
                    prerequisitos_faltantes.append(f"{curso_prereq.codigo} - {curso_prereq.nombre}")
            
            if prerequisitos_faltantes:
                errores.append(
                    f"❌ {curso.codigo} - {curso.nombre}: "
                    f"No puedes haber aprobado este curso sin antes aprobar sus prerequisitos: "
                    f"{', '.join(prerequisitos_faltantes)}"
                )
    
    # Generar advertencias para cursos de ciclos avanzados sin cursos de ciclos básicos
    if cursos_aprobados_set:
        ciclos_con_cursos = set()
        for codigo in codigos_aprobados:
            if codigo in cursos_dict:
                ciclos_con_cursos.add(cursos_dict[codigo].ciclo)
        
        ciclo_max = max(ciclos_con_cursos) if ciclos_con_cursos else 0
        ciclo_min = min(ciclos_con_cursos) if ciclos_con_cursos else 0
        
        # Si hay un gap muy grande entre ciclos, advertir
        if ciclo_max - ciclo_min > 3:
            # Verificar si hay ciclos intermedios sin cursos
            ciclos_vacios = []
            for ciclo in range(ciclo_min + 1, ciclo_max):
                if ciclo not in ciclos_con_cursos:
                    ciclos_vacios.append(ciclo)
            
            if ciclos_vacios:
                advertencias.append({
                    "tipo": "ciclos_saltados",
                    "mensaje": f"⚠️ Has marcado cursos del ciclo {ciclo_max} pero no hay cursos aprobados en los ciclos: {', '.join(map(str, ciclos_vacios))}. "
                              f"Verifica que hayas seleccionado todos los cursos que aprobaste.",
                    "ciclos_faltantes": ciclos_vacios
                })
    
    es_valido = len(errores) == 0
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
    cursos_aprobados = db.query(Curso).filter(
        Curso.malla_id == malla_id,
        Curso.codigo.in_(codigos_aprobados)
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
