from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import time
from ..database import get_db
from ..schemas import (
    RecomendacionRequest, RecomendacionResponse, CursoRecomendado,
    ComparacionAlgoritmosResponse, ResultadoAlgoritmo
)
from ..models import Usuario, Recomendacion, Curso, Malla, Prerequisito
from ..utils.security import get_current_active_user
from ..utils.course_validator import validar_cursos_aprobados, obtener_cursos_disponibles
from ..utils.multi_malla_validator import procesar_cursos_multi_malla, validar_cursos_multi_malla
from ..services.ai_agent import ai_agent
from ..algorithms.constraint_programming import ConstraintProgrammingSolver
from ..algorithms.backtracking import BacktrackingSolver
from ..algorithms import PrologRecommendationService, AssociationRulesService

router = APIRouter()

# Servicios globales de los nuevos algoritmos
prolog_service = PrologRecommendationService()
association_service = AssociationRulesService()


@router.post("/", response_model=RecomendacionResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    request: RecomendacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear recomendación curricular usando el agente de IA.
    El agente decide automáticamente qué algoritmo usar.
    
    SOPORTA MÚLTIPLES MALLAS:
    - Si cursos_aprobados_multi_malla está presente, se procesan cursos de varias mallas
    - Los cursos se convalidan automáticamente hacia la malla_id (objetivo)
    - Ejemplo: Cursos de malla 2019 y 2022 se convalidan a malla 2025
    """
    
    # Verificar que la malla existe
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Malla no encontrada"
        )
    
    # 🆕 NUEVA FUNCIONALIDAD: MÚLTIPLES MALLAS
    cursos_ids = []
    info_convalidacion = None
    
    if request.cursos_aprobados_multi_malla:
        print(f"\n{'='*60}")
        print(f"MODO: MÚLTIPLES MALLAS")
        print(f"{'='*60}\n")
        
        # Convertir de Pydantic a dict
        cursos_multi_dict = [
            {
                "codigo": curso.codigo,
                "malla_origen_anio": curso.malla_origen_anio
            }
            for curso in request.cursos_aprobados_multi_malla
        ]
        
        # Procesar y convalidar cursos de múltiples mallas
        cursos_ids, info_convalidacion = procesar_cursos_multi_malla(
            db=db,
            malla_destino_anio=malla.anio,
            cursos_aprobados_multi_malla=cursos_multi_dict
        )
        
        if info_convalidacion["cursos_sin_convalidacion"] > 0:
            print(f"⚠️ Advertencia: {info_convalidacion['cursos_sin_convalidacion']} cursos sin convalidación")
        
        # Actualizar request.cursos_aprobados con los códigos convalidados para logging
        cursos_convalidados = db.query(Curso).filter(Curso.id.in_(cursos_ids)).all()
        request.cursos_aprobados = [c.codigo for c in cursos_convalidados]
        
    else:
        # MODO TRADICIONAL: Una sola malla
        print(f"\n{'='*60}")
        print(f"MODO: UNA SOLA MALLA")
        print(f"{'='*60}\n")
        
        # ✅ VALIDAR PREREQUISITOS ANTES DE GENERAR RECOMENDACIÓN
        print(f"🔍 Validando cursos aprobados...")
        es_valido, errores, advertencias = validar_cursos_aprobados(
            db=db,
            malla_id=request.malla_id,
            codigos_aprobados=request.cursos_aprobados
        )
        
        if not es_valido:
            error_detail = {
                "mensaje": "Los cursos seleccionados no cumplen con los prerequisitos",
                "errores": errores,
                "advertencias": advertencias
            }
            print(f"❌ Validación fallida: {len(errores)} errores")
            for error in errores:
                print(f"  - {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
        
        if advertencias:
            print(f"⚠️ {len(advertencias)} advertencias encontradas")
            for adv in advertencias:
                print(f"  - {adv['mensaje']}")
        
        print(f"✅ Validación exitosa")
        
        # Convertir códigos de cursos a IDs
        for codigo in request.cursos_aprobados:
            curso = db.query(Curso).filter(
                Curso.codigo == codigo,
                Curso.malla_id == request.malla_id
            ).first()
            if curso:
                cursos_ids.append(curso.id)
        
        # Validar solo si se proporcionaron códigos pero no se encontraron
        if request.cursos_aprobados and not cursos_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontraron cursos válidos con los códigos proporcionados"
            )
    
    # 📊 OBTENER ESTADÍSTICAS DETALLADAS PARA EL AGENTE
    total_cursos = db.query(Curso).filter(Curso.malla_id == request.malla_id).count()
    cursos_aprobados_count = len(cursos_ids)
    cursos_pendientes = total_cursos - cursos_aprobados_count
    
    # Obtener cursos aprobados reales para análisis
    cursos_aprobados_objs = db.query(Curso).filter(
        Curso.id.in_(cursos_ids)
    ).all()
    
    # Analizar distribución por ciclos
    ciclos_completados = set()
    ciclos_parciales = set()
    cursos_por_ciclo_aprobados = {}
    
    for curso in cursos_aprobados_objs:
        ciclo = curso.ciclo
        if ciclo not in cursos_por_ciclo_aprobados:
            cursos_por_ciclo_aprobados[ciclo] = 0
        cursos_por_ciclo_aprobados[ciclo] += 1
    
    # Identificar ciclos completos (aproximadamente 6 cursos por ciclo)
    for ciclo, count in cursos_por_ciclo_aprobados.items():
        if count >= 5:  # Casi completo
            ciclos_completados.add(ciclo)
        else:
            ciclos_parciales.add(ciclo)
    
    # Determinar ciclo actual más preciso
    if ciclos_completados:
        ciclo_actual = max(ciclos_completados) + 1
    elif cursos_por_ciclo_aprobados:
        ciclo_actual = max(cursos_por_ciclo_aprobados.keys())
    else:
        ciclo_actual = 1
    
    ciclo_actual = min(10, max(1, ciclo_actual))
    
    # Contar prerequisitos TOTALES de la malla
    num_prerequisitos_totales = db.query(Prerequisito).join(
        Curso, Prerequisito.curso_id == Curso.id
    ).filter(
        Curso.malla_id == request.malla_id
    ).count()
    
    # Contar prerequisitos CUMPLIDOS (cursos pendientes que pueden cursarse YA)
    cursos_disponibles = obtener_cursos_disponibles(
        db=db,
        malla_id=request.malla_id,
        codigos_aprobados=request.cursos_aprobados
    )
    num_cursos_disponibles = len(cursos_disponibles)
    
    # Detectar si es alumno irregular (tiene ciclos incompletos)
    es_irregular = len(ciclos_parciales) > 1
    
    print(f"📊 Métricas del estudiante:")
    print(f"   - Total cursos: {total_cursos}")
    print(f"   - Aprobados: {cursos_aprobados_count}")
    print(f"   - Pendientes: {cursos_pendientes}")
    print(f"   - Disponibles ahora: {num_cursos_disponibles}")
    print(f"   - Ciclos completos: {sorted(ciclos_completados)}")
    print(f"   - Ciclos parciales: {sorted(ciclos_parciales)}")
    print(f"   - Ciclo actual: {ciclo_actual}")
    print(f"   - Estado: {'IRREGULAR' if es_irregular else 'REGULAR'}")
    
    # 🤖 EL AGENTE DECIDE QUÉ ALGORITMO USAR CON DATOS REALES
    print(f"🤖 Consultando al agente de IA con métricas reales...")
    algoritmo_elegido, razon_algoritmo = ai_agent.decide_algorithm(
        total_cursos=total_cursos,
        cursos_aprobados=cursos_aprobados_count,
        cursos_pendientes=cursos_pendientes,
        num_prerequisitos=num_prerequisitos_totales,
        ciclo_actual=ciclo_actual,
        malla_anio=malla.anio
    )
    
    print(f"✅ Agente decidió usar: {algoritmo_elegido}")
    print(f"📝 Razón: {razon_algoritmo[:100]}...")
    
    # Ejecutar el algoritmo elegido (AHORA CON 4 OPCIONES)
    start_time = time.time()
    cursos_recomendados_raw = []
    
    if algoritmo_elegido == "constraint_programming":
        solver = ConstraintProgrammingSolver(db)
        cursos_recomendados_raw = solver.recommend_courses(
            malla_id=request.malla_id,
            cursos_aprobados_ids=cursos_ids,
            max_cursos=6
        )
    
    elif algoritmo_elegido == "backtracking":
        solver = BacktrackingSolver(db)
        cursos_recomendados_raw = solver.recommend_courses(
            malla_id=request.malla_id,
            cursos_aprobados_ids=cursos_ids,
            max_cursos=6
        )
    
    elif algoritmo_elegido == "prolog":
        # Cargar malla completa para Prolog
        malla_completa, _ = cargar_malla_completa(db, request.malla_id)
        if malla_completa:
            resultado_prolog = prolog_service.recomendar(
                malla=malla_completa,
                cursos_aprobados=request.cursos_aprobados
            )
            
            if resultado_prolog.get('disponible') and resultado_prolog.get('recomendacion'):
                # Convertir formato de Prolog a formato estándar con campos completos
                cursos_recomendados_raw = []
                for idx, curso in enumerate(resultado_prolog['recomendacion']['cursos'], 1):
                    # Buscar el curso en la BD para obtener el curso_id
                    curso_db = db.query(Curso).filter(
                        Curso.codigo == curso['codigo'],
                        Curso.malla_id == request.malla_id
                    ).first()
                    
                    if curso_db:
                        cursos_recomendados_raw.append({
                            "curso_id": curso_db.id,
                            "codigo": curso['codigo'],
                            "nombre": curso['nombre'],
                            "ciclo": curso['ciclo'],
                            "creditos": curso['creditos'],
                            "prioridad": idx,  # Orden de recomendación
                            "razon": "Recomendado por análisis lógico de prerequisitos"
                        })
    
    elif algoritmo_elegido == "association_rules":
        # Cargar malla completa para Association Rules
        malla_completa, malla_por_ciclo = cargar_malla_completa(db, request.malla_id)
        if malla_completa:
            # Entrenar si no está entrenado
            if not association_service.trained:
                todas_mallas = cargar_todas_las_mallas(db)
                mapa_conval = obtener_mapa_convalidaciones(db)
                datos_historicos = association_service.generar_datos_historicos(todas_mallas, mapa_conval)
                association_service.entrenar(datos_historicos)
            
            resultado_association = association_service.recomendar(
                malla=malla_completa,
                cursos_aprobados=request.cursos_aprobados,
                malla_por_ciclo=malla_por_ciclo
            )
            
            if resultado_association.get('disponible') and resultado_association.get('recomendacion'):
                # Convertir formato de Association Rules a formato estándar con campos completos
                cursos_recomendados_raw = []
                for idx, curso in enumerate(resultado_association['recomendacion']['cursos'], 1):
                    # Buscar el curso en la BD para obtener el curso_id
                    curso_db = db.query(Curso).filter(
                        Curso.codigo == curso['codigo'],
                        Curso.malla_id == request.malla_id
                    ).first()
                    
                    if curso_db:
                        cursos_recomendados_raw.append({
                            "curso_id": curso_db.id,
                            "codigo": curso['codigo'],
                            "nombre": curso['nombre'],
                            "ciclo": curso['ciclo'],
                            "creditos": curso['creditos'],
                            "prioridad": idx,  # Orden de recomendación
                            "razon": "Recomendado por patrones de aprobación históricos"
                        })
    
    tiempo_ejecucion = time.time() - start_time
    
    # Validar que hay recomendaciones
    if not cursos_recomendados_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron cursos disponibles para recomendar. "
                   "Verifica que hayas aprobado los prerequisitos necesarios."
        )
    
    # Guardar en base de datos
    db_recomendacion = Recomendacion(
        usuario_id=current_user.id,
        malla_id=request.malla_id,
        algoritmo_usado=algoritmo_elegido,
        cursos_aprobados=json.dumps(request.cursos_aprobados),
        cursos_recomendados=json.dumps(cursos_recomendados_raw),
        razon_algoritmo=razon_algoritmo,
        tiempo_ejecucion=tiempo_ejecucion
    )
    
    db.add(db_recomendacion)
    db.commit()
    db.refresh(db_recomendacion)
    
    # Formatear respuesta
    cursos_recomendados = [
        CursoRecomendado(**curso) for curso in cursos_recomendados_raw
    ]
    
    return RecomendacionResponse(
        id=db_recomendacion.id,
        algoritmo_usado=algoritmo_elegido,
        razon_algoritmo=razon_algoritmo,
        cursos_recomendados=cursos_recomendados,
        tiempo_ejecucion=tiempo_ejecucion,
        created_at=db_recomendacion.created_at
    )


@router.post("/validate")
async def validate_approved_courses(
    request: RecomendacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Validar que los cursos marcados como aprobados cumplan con prerequisitos.
    Este endpoint se puede llamar antes de generar la recomendación para validar.
    """
    # Verificar que la malla existe
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Malla no encontrada"
        )
    
    # Validar cursos aprobados
    es_valido, errores, advertencias = validar_cursos_aprobados(
        db=db,
        malla_id=request.malla_id,
        codigos_aprobados=request.cursos_aprobados
    )
    
    # Obtener cursos disponibles
    cursos_disponibles = obtener_cursos_disponibles(
        db=db,
        malla_id=request.malla_id,
        codigos_aprobados=request.cursos_aprobados
    )
    
    return {
        "valido": es_valido,
        "errores": errores,
        "advertencias": advertencias,
        "total_aprobados": len(request.cursos_aprobados),
        "cursos_disponibles": len(cursos_disponibles),
        "mensaje": "Validación exitosa" if es_valido else "Se encontraron errores en la selección de cursos"
    }


@router.get("/history", response_model=List[RecomendacionResponse])
async def get_recommendation_history(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener historial de recomendaciones del usuario"""
    
    recomendaciones = db.query(Recomendacion).filter(
        Recomendacion.usuario_id == current_user.id
    ).order_by(
        Recomendacion.created_at.desc()
    ).all()
    
    resultado = []
    for rec in recomendaciones:
        cursos_recomendados_raw = json.loads(rec.cursos_recomendados)
        cursos_recomendados = [
            CursoRecomendado(**curso) for curso in cursos_recomendados_raw
        ]
        
        resultado.append(RecomendacionResponse(
            id=rec.id,
            algoritmo_usado=rec.algoritmo_usado,
            razon_algoritmo=rec.razon_algoritmo,
            cursos_recomendados=cursos_recomendados,
            tiempo_ejecucion=rec.tiempo_ejecucion,
            created_at=rec.created_at
        ))
    
    return resultado


@router.get("/{recomendacion_id}", response_model=RecomendacionResponse)
async def get_recommendation(
    recomendacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener una recomendación específica"""
    
    recomendacion = db.query(Recomendacion).filter(
        Recomendacion.id == recomendacion_id,
        Recomendacion.usuario_id == current_user.id
    ).first()
    
    if not recomendacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada"
        )
    
    cursos_recomendados_raw = json.loads(recomendacion.cursos_recomendados)
    cursos_recomendados = [
        CursoRecomendado(**curso) for curso in cursos_recomendados_raw
    ]
    
    return RecomendacionResponse(
        id=recomendacion.id,
        algoritmo_usado=recomendacion.algoritmo_usado,
        razon_algoritmo=recomendacion.razon_algoritmo,
        cursos_recomendados=cursos_recomendados,
        tiempo_ejecucion=recomendacion.tiempo_ejecucion,
        created_at=recomendacion.created_at
    )


@router.get("/stats/algorithms")
async def get_algorithm_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener estadísticas de uso de algoritmos"""
    
    from sqlalchemy import func
    
    stats = db.query(
        Recomendacion.algoritmo_usado,
        func.count(Recomendacion.id).label('count'),
        func.avg(Recomendacion.tiempo_ejecucion).label('avg_time')
    ).filter(
        Recomendacion.usuario_id == current_user.id
    ).group_by(
        Recomendacion.algoritmo_usado
    ).all()
    
    return [
        {
            "algoritmo": stat.algoritmo_usado,
            "total_usos": stat.count,
            "tiempo_promedio": round(stat.avg_time, 3) if stat.avg_time else 0
        }
        for stat in stats
    ]


# ============================================================================
# NUEVOS ENDPOINTS PARA ALGORITMOS AVANZADOS (PROLOG Y REGLAS DE ASOCIACIÓN)
# ============================================================================

def cargar_malla_completa(db: Session, malla_id: int) -> tuple:
    """Carga la malla completa con todos sus cursos"""
    malla = db.query(Malla).filter(Malla.id == malla_id).first()
    if not malla:
        return None, None
    
    cursos = db.query(Curso).filter(Curso.malla_id == malla_id).all()
    
    # Crear diccionario completo de la malla
    malla_completa = {}
    malla_por_ciclo = {i: [] for i in range(1, 11)}
    
    for curso in cursos:
        # Parsear prerequisitos desde la relación
        prerequisitos_list = []
        if curso.prerequisitos:
            for prereq in curso.prerequisitos:
                if prereq.prerequisito_curso:
                    prerequisitos_list.append(prereq.prerequisito_curso.codigo)
        
        info_curso = {
            'codigo': curso.codigo,
            'nombre': curso.nombre,
            'ciclo': curso.ciclo,
            'creditos': curso.creditos,
            'prerrequisitos': prerequisitos_list
        }
        
        malla_completa[curso.codigo] = info_curso
        malla_por_ciclo[curso.ciclo].append(info_curso)
    
    return malla_completa, malla_por_ciclo


def cargar_todas_las_mallas(db: Session) -> dict:
    """Carga todas las mallas disponibles"""
    todas_mallas = {}
    
    mallas = db.query(Malla).all()
    for malla in mallas:
        año = malla.anio
        malla_completa, malla_por_ciclo = cargar_malla_completa(db, malla.id)
        todas_mallas[año] = (malla_completa, malla_por_ciclo)
    
    return todas_mallas


def obtener_mapa_convalidaciones(db: Session) -> dict:
    """
    Obtiene el mapa de convalidaciones
    NOTA: Por ahora retorna un diccionario vacío
    TODO: Implementar cuando exista tabla de convalidaciones
    """
    return {}


@router.post("/comparar-algoritmos", response_model=ComparacionAlgoritmosResponse)
async def comparar_algoritmos(
    request: RecomendacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Ejecuta los 4 algoritmos y compara sus resultados para que el estudiante vea
    cuál fue más efectivo en su caso específico.
    
    Devuelve:
    - Resultados de cada algoritmo (cursos recomendados, tiempo, créditos)
    - El algoritmo que el agente de IA seleccionó
    - Métricas de comparación (eficiencia, diversidad, optimización)
    """
    
    print(f"\n{'='*60}")
    print(f"COMPARACIÓN DE ALGORITMOS PARA USUARIO: {current_user.email}")
    print(f"{'='*60}\n")
    
    # 1. Validar malla
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malla con ID {request.malla_id} no encontrada"
        )
    
    # SOPORTA MÚLTIPLES MALLAS (igual que create_recommendation)
    cursos_aprobados_ids = []
    info_convalidacion = None
    if getattr(request, 'cursos_aprobados_multi_malla', None):
        print(f"\n{'='*60}")
        print(f"MODO: MÚLTIPLES MALLAS (COMPARAR)")
        print(f"{'='*60}\n")
        cursos_multi_dict = [
            {
                "codigo": curso.codigo,
                "malla_origen_anio": curso.malla_origen_anio
            }
            for curso in request.cursos_aprobados_multi_malla
        ]
        from ..utils.multi_malla_validator import procesar_cursos_multi_malla
        cursos_aprobados_ids, info_convalidacion = procesar_cursos_multi_malla(
            db=db,
            malla_destino_anio=malla.anio,
            cursos_aprobados_multi_malla=cursos_multi_dict
        )
        # Para logging y métricas
        cursos_convalidados = db.query(Curso).filter(Curso.id.in_(cursos_aprobados_ids)).all()
        request.cursos_aprobados = [c.codigo for c in cursos_convalidados]
    else:
        # MODO TRADICIONAL
        todos_cursos = db.query(Curso).filter(Curso.malla_id == request.malla_id).all()
        cursos_map = {c.codigo: c for c in todos_cursos}
        print(f"📚 Malla: {malla.nombre}")
        print(f"📝 Cursos aprobados enviados: {request.cursos_aprobados}")
        print(f"🎯 Máximo créditos: 22\n")
        cursos_aprobados_validados = []
        for codigo in request.cursos_aprobados:
            if codigo in cursos_map:
                cursos_aprobados_validados.append(cursos_map[codigo])
        cursos_aprobados_ids = [c.id for c in cursos_aprobados_validados]

    # 3. Obtener cursos disponibles
    cursos_disponibles = obtener_cursos_disponibles(
        db, request.malla_id, cursos_aprobados_ids
    )
    
    max_creditos = 22
    resultados = []
    
    # 4. Ejecutar cada algoritmo
    algoritmos = [
        ("constraint_programming", "Constraint Programming (CP-SAT)"),
        ("backtracking", "Backtracking"),
        ("prolog", "Prolog"),
        ("association_rules", "Association Rules")
    ]
    
    for algo_key, algo_nombre in algoritmos:
        print(f"\n🔍 Ejecutando: {algo_nombre}")
        print(f"{'='*60}")
        
        try:
            start_time = time.time()
            
            if algo_key == "constraint_programming":
                solver = ConstraintProgrammingSolver()
                cursos_rec = solver.recomendar_cursos(
                    cursos_disponibles, cursos_aprobados_ids, max_creditos
                )
            
            elif algo_key == "backtracking":
                solver = BacktrackingSolver()
                cursos_rec = solver.recomendar_cursos(
                    cursos_disponibles, cursos_aprobados_ids, max_creditos
                )
            
            elif algo_key == "prolog":
                if prolog_service.prolog is None:
                    raise Exception("Servicio Prolog no disponible")
                cursos_rec = prolog_service.recomendar_cursos(
                    db, request.malla_id, cursos_aprobados_ids, max_creditos
                )
            
            elif algo_key == "association_rules":
                if association_service is None or not association_service.trained:
                    raise Exception("Servicio de Reglas de Asociación no entrenado")
                cursos_rec = association_service.recomendar_cursos(
                    cursos_aprobados_ids, cursos_disponibles, max_creditos
                )
            
            tiempo = time.time() - start_time
            
            # Convertir a formato CursoRecomendado
            cursos_recomendados = []
            total_creditos = 0
            
            for curso_data in cursos_rec:
                if isinstance(curso_data, dict):
                    curso_id = curso_data.get('curso_id')
                    curso = db.query(Curso).filter(Curso.id == curso_id).first()
                    if curso:
                        cursos_recomendados.append(CursoRecomendado(
                            curso_id=curso.id,
                            codigo=curso.codigo,
                            nombre=curso.nombre,
                            creditos=curso.creditos,
                            ciclo=curso.ciclo,
                            prioridad=curso_data.get('prioridad', 1),
                            razon=curso_data.get('razon', f'Recomendado por {algo_nombre}')
                        ))
                        total_creditos += curso.creditos
            
            cumple_limite = total_creditos <= max_creditos
            
            print(f"✅ {algo_nombre} completado")
            print(f"   Cursos: {len(cursos_recomendados)}")
            print(f"   Créditos: {total_creditos}/{max_creditos}")
            print(f"   Tiempo: {tiempo:.3f}s")
            print(f"   Cumple límite: {'✓' if cumple_limite else '✗'}")
            
            resultados.append(ResultadoAlgoritmo(
                algoritmo=algo_key,
                cursos_recomendados=cursos_recomendados,
                tiempo_ejecucion=round(tiempo, 3),
                total_creditos=total_creditos,
                numero_cursos=len(cursos_recomendados),
                cumple_limite_creditos=cumple_limite,
                error=None
            ))
            
        except Exception as e:
            print(f"❌ Error en {algo_nombre}: {str(e)}")
            resultados.append(ResultadoAlgoritmo(
                algoritmo=algo_key,
                cursos_recomendados=[],
                tiempo_ejecucion=0.0,
                total_creditos=0,
                numero_cursos=0,
                cumple_limite_creditos=False,
                error=str(e)
            ))
    
    # 5. Dejar que el agente de IA seleccione el mejor
    print(f"\n{'='*60}")
    print(f"🤖 AGENTE DE IA SELECCIONANDO ALGORITMO ÓPTIMO")
    print(f"{'='*60}\n")
    
    # Calcular métricas del estudiante
    total_cursos = len(todos_cursos)
    num_aprobados = len(cursos_aprobados_validados)
    num_disponibles = len(cursos_disponibles)
    
    # Llamar al agente de IA
    decision = await ai_agent(
        cursos_disponibles=cursos_disponibles,
        cursos_aprobados=cursos_aprobados_ids,
        total_cursos=total_cursos,
        num_aprobados=num_aprobados,
        num_disponibles=num_disponibles,
        max_creditos=max_creditos
    )
    
    algoritmo_seleccionado = decision.get("algoritmo", "prolog")
    razon_seleccion = decision.get("razon", "Selección por defecto")
    
    # 6. Calcular métricas de comparación
    resultados_validos = [r for r in resultados if not r.error]
    
    metricas = {
        "algoritmos_exitosos": len(resultados_validos),
        "algoritmos_con_error": len([r for r in resultados if r.error]),
        "tiempo_promedio": round(sum(r.tiempo_ejecucion for r in resultados_validos) / len(resultados_validos), 3) if resultados_validos else 0,
        "tiempo_minimo": round(min(r.tiempo_ejecucion for r in resultados_validos), 3) if resultados_validos else 0,
        "tiempo_maximo": round(max(r.tiempo_ejecucion for r in resultados_validos), 3) if resultados_validos else 0,
        "algoritmo_mas_rapido": min(resultados_validos, key=lambda r: r.tiempo_ejecucion).algoritmo if resultados_validos else None,
        "algoritmo_mas_cursos": max(resultados_validos, key=lambda r: r.numero_cursos).algoritmo if resultados_validos else None,
        "algoritmo_mas_creditos": max(resultados_validos, key=lambda r: r.total_creditos).algoritmo if resultados_validos else None,
        "consenso_cursos": _calcular_consenso([r.cursos_recomendados for r in resultados_validos]) if resultados_validos else []
    }
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN DE COMPARACIÓN")
    print(f"{'='*60}")
    print(f"Algoritmo seleccionado: {algoritmo_seleccionado}")
    print(f"Razón: {razon_seleccion}")
    print(f"Algoritmos exitosos: {metricas['algoritmos_exitosos']}/4")
    print(f"Más rápido: {metricas['algoritmo_mas_rapido']}")
    print(f"Más cursos: {metricas['algoritmo_mas_cursos']}")
    print(f"Más créditos: {metricas['algoritmo_mas_creditos']}")
    print(f"{'='*60}\n")
    
    return ComparacionAlgoritmosResponse(
        malla_id=request.malla_id,
        cursos_aprobados=request.cursos_aprobados,
        max_creditos=max_creditos,
        resultados=resultados,
        algoritmo_seleccionado=algoritmo_seleccionado,
        razon_seleccion=razon_seleccion,
        metricas_comparacion=metricas
    )


def _calcular_consenso(listas_cursos: List[List[CursoRecomendado]]) -> List[Dict[str, Any]]:
    """
    Calcula qué cursos fueron recomendados por múltiples algoritmos (consenso).
    """
    if not listas_cursos:
        return []
    
    # Contar cuántos algoritmos recomendaron cada curso
    contador = {}
    for lista in listas_cursos:
        for curso in lista:
            if curso.curso_id not in contador:
                contador[curso.curso_id] = {
                    "curso_id": curso.curso_id,
                    "codigo": curso.codigo,
                    "nombre": curso.nombre,
                    "veces_recomendado": 0
                }
            contador[curso.curso_id]["veces_recomendado"] += 1
    
    # Ordenar por consenso (más recomendados primero)
    consenso = sorted(
        contador.values(),
        key=lambda x: x["veces_recomendado"],
        reverse=True
    )
    
    return consenso[:10]  # Top 10 cursos con más consenso

