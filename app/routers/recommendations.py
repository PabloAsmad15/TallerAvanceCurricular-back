from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import time
from pydantic import BaseModel
from ..database import get_db
from ..schemas import RecomendacionRequest, RecomendacionResponse, CursoRecomendado
from ..models import Usuario, Recomendacion, Curso, Malla, Prerequisito
from ..utils.security import get_current_active_user
from ..utils.course_validator import validar_cursos_aprobados, obtener_cursos_disponibles
from ..services.ai_agent import ai_agent
from ..algorithms.constraint_programming import ConstraintProgrammingSolver
from ..algorithms.backtracking import BacktrackingSolver
from ..algorithms import PrologRecommendationService, AssociationRulesService

router = APIRouter()

# Servicios globales de los nuevos algoritmos
prolog_service = PrologRecommendationService()
association_service = AssociationRulesService()


# Schemas para los nuevos endpoints
class AlgoritmoRequest(BaseModel):
    """Request para algoritmos avanzados"""
    entrenar: bool = False  # Para association_rules


class AlgoritmoResponse(BaseModel):
    """Response de algoritmos avanzados"""
    success: bool
    algoritmo: str
    disponible: bool
    entrenado: Optional[bool] = None
    completado: Optional[bool] = None
    diagnostico: Optional[dict] = None
    recomendacion: Optional[dict] = None
    reglas_asociacion: Optional[dict] = None
    mensaje: Optional[str] = None
    error: Optional[str] = None


@router.post("/", response_model=RecomendacionResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    request: RecomendacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear recomendación curricular usando el agente de IA.
    El agente decide automáticamente qué algoritmo usar.
    """
    
    # Verificar que la malla existe
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Malla no encontrada"
        )
    
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
    cursos_ids = []
    for codigo in request.cursos_aprobados:
        curso = db.query(Curso).filter(
            Curso.codigo == codigo,
            Curso.malla_id == request.malla_id
        ).first()
        if curso:
            cursos_ids.append(curso.id)
    
    if not cursos_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron cursos válidos con los códigos proporcionados"
        )
    
    # Obtener estadísticas para el agente
    total_cursos = db.query(Curso).filter(Curso.malla_id == request.malla_id).count()
    cursos_aprobados = len(cursos_ids)
    cursos_pendientes = total_cursos - cursos_aprobados
    
    # Contar prerequisitos
    num_prerequisitos = db.query(Prerequisito).join(
        Curso, Prerequisito.curso_id == Curso.id
    ).filter(
        Curso.malla_id == request.malla_id
    ).count()
    
    # Determinar ciclo actual (aproximado por cursos aprobados)
    ciclo_actual = min(10, max(1, (cursos_aprobados // 6) + 1))
    
    # 🤖 EL AGENTE DECIDE QUÉ ALGORITMO USAR
    print(f"🤖 Consultando al agente de IA...")
    algoritmo_elegido, razon_algoritmo = ai_agent.decide_algorithm(
        total_cursos=total_cursos,
        cursos_aprobados=cursos_aprobados,
        cursos_pendientes=cursos_pendientes,
        num_prerequisitos=num_prerequisitos,
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
                # Convertir formato de Prolog a formato estándar
                cursos_recomendados_raw = [
                    {
                        "codigo": curso['codigo'],
                        "nombre": curso['nombre'],
                        "ciclo": curso['ciclo'],
                        "creditos": curso['creditos']
                    }
                    for curso in resultado_prolog['recomendacion']['cursos']
                ]
    
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
                # Convertir formato de Association Rules a formato estándar
                cursos_recomendados_raw = [
                    {
                        "codigo": curso['codigo'],
                        "nombre": curso['nombre'],
                        "ciclo": curso['ciclo'],
                        "creditos": curso['creditos']
                    }
                    for curso in resultado_association['recomendacion']['cursos']
                ]
    
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
        # Parsear prerrequisitos
        prerrequisitos = []
        if curso.prerrequisitos:
            prerrequisitos = [p.strip() for p in curso.prerrequisitos.split(',')]
        
        info_curso = {
            'codigo': curso.codigo,
            'nombre': curso.nombre,
            'ciclo': curso.ciclo,
            'creditos': curso.creditos,
            'prerrequisitos': prerrequisitos
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


def obtener_cursos_aprobados_usuario(db: Session, usuario_id: int) -> List[str]:
    """
    Obtiene los cursos aprobados del usuario desde su última recomendación
    Si no tiene recomendaciones, retorna lista vacía
    """
    ultima_recomendacion = db.query(Recomendacion).filter(
        Recomendacion.usuario_id == usuario_id
    ).order_by(Recomendacion.created_at.desc()).first()
    
    if not ultima_recomendacion or not ultima_recomendacion.cursos_aprobados:
        return []
    
    try:
        return json.loads(ultima_recomendacion.cursos_aprobados)
    except:
        return []


@router.post("/prolog", response_model=AlgoritmoResponse)
async def recomendar_con_prolog(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    🧠 Genera recomendaciones usando el algoritmo de **Prolog**
    
    **Características:**
    - Usa lógica declarativa para analizar prerrequisitos
    - Identifica el último ciclo completado automáticamente
    - Prioriza cursos obligatorios sobre cursos de avance
    - Garantiza que se cumplan todas las reglas académicas
    
    **Ventajas:**
    - Muy preciso con las reglas de prerrequisitos
    - Rápido para mallas pequeñas y medianas
    - No requiere entrenamiento previo
    """
    try:
        # Obtener malla del usuario
        if not current_user.malla_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene malla asignada"
            )
        
        # Cargar malla completa
        malla_completa, _ = cargar_malla_completa(db, current_user.malla_id)
        
        if not malla_completa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Malla no encontrada"
            )
        
        # Obtener cursos aprobados del usuario
        cursos_aprobados = obtener_cursos_aprobados_usuario(db, current_user.id)
        
        # Generar recomendación
        resultado = prolog_service.recomendar(
            malla=malla_completa,
            cursos_aprobados=cursos_aprobados
        )
        
        return AlgoritmoResponse(
            success=resultado.get('disponible', False),
            **resultado
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en recomendación Prolog: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar recomendación: {str(e)}"
        )


@router.post("/association-rules", response_model=AlgoritmoResponse)
async def recomendar_con_reglas_asociacion(
    request: AlgoritmoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    📊 Genera recomendaciones usando **Reglas de Asociación**
    
    **Características:**
    - Analiza patrones históricos de aprobación de miles de estudiantes
    - Aprende relaciones entre cursos que suelen aprobarse juntos
    - Prioriza cursos basándose en patrones de éxito comprobados
    - Usa métricas de confianza, soporte y lift
    
    **Parámetros:**
    - `entrenar`: Si es `true`, re-entrena el modelo con datos históricos sintéticos
    
    **Ventajas:**
    - Descubre patrones no obvios entre cursos
    - Mejora con más datos históricos
    - Recomendaciones personalizadas basadas en historial similar
    
    **Nota:** La primera vez debe entrenar (puede tomar unos segundos)
    """
    try:
        # Obtener malla del usuario
        if not current_user.malla_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene malla asignada"
            )
        
        # Cargar malla completa
        malla_completa, malla_por_ciclo = cargar_malla_completa(db, current_user.malla_id)
        
        if not malla_completa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Malla no encontrada"
            )
        
        # Entrenar si se solicita o no está entrenado
        if request.entrenar or not association_service.trained:
            print("\n📚 Entrenando modelo de reglas de asociación...")
            
            # Cargar todas las mallas
            todas_mallas = cargar_todas_las_mallas(db)
            mapa_conval = obtener_mapa_convalidaciones(db)
            
            # Generar datos históricos
            datos_historicos = association_service.generar_datos_historicos(
                todas_mallas, 
                mapa_conval
            )
            
            # Entrenar
            exito_entrenamiento = association_service.entrenar(datos_historicos)
            
            if not exito_entrenamiento:
                print("⚠️ No se pudo entrenar el modelo, continuando sin reglas...")
        
        # Obtener cursos aprobados del usuario
        cursos_aprobados = obtener_cursos_aprobados_usuario(db, current_user.id)
        
        # Generar recomendación
        resultado = association_service.recomendar(
            malla=malla_completa,
            cursos_aprobados=cursos_aprobados,
            malla_por_ciclo=malla_por_ciclo
        )
        
        return AlgoritmoResponse(
            success=resultado.get('disponible', False),
            **resultado
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en recomendación con reglas de asociación: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar recomendación: {str(e)}"
        )


@router.get("/comparar")
async def comparar_algoritmos(
    entrenar: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    🔬 Compara los resultados de ambos algoritmos lado a lado
    
    Ejecuta tanto **Prolog** como **Reglas de Asociación** y retorna:
    - Las recomendaciones de cada algoritmo
    - Diagnóstico académico de cada uno
    - Comparación de créditos y cantidad de cursos
    - Cursos comunes entre ambas recomendaciones
    
    Útil para:
    - Validar consistencia entre algoritmos
    - Elegir qué algoritmo se adapta mejor a tu caso
    - Análisis comparativo de estrategias de matrícula
    """
    try:
        # Obtener malla del usuario
        if not current_user.malla_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene malla asignada"
            )
        
        # Cargar malla completa
        malla_completa, malla_por_ciclo = cargar_malla_completa(db, current_user.malla_id)
        
        if not malla_completa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Malla no encontrada"
            )
        
        # Obtener cursos aprobados
        cursos_aprobados = obtener_cursos_aprobados_usuario(db, current_user.id)
        
        # Recomendación con Prolog
        resultado_prolog = prolog_service.recomendar(
            malla=malla_completa,
            cursos_aprobados=cursos_aprobados
        )
        
        # Entrenar association rules si es necesario
        if entrenar or not association_service.trained:
            todas_mallas = cargar_todas_las_mallas(db)
            mapa_conval = obtener_mapa_convalidaciones(db)
            datos_historicos = association_service.generar_datos_historicos(
                todas_mallas, 
                mapa_conval
            )
            association_service.entrenar(datos_historicos)
        
        # Recomendación con Reglas de Asociación
        resultado_association = association_service.recomendar(
            malla=malla_completa,
            cursos_aprobados=cursos_aprobados,
            malla_por_ciclo=malla_por_ciclo
        )
        
        # Extraer cursos recomendados
        cursos_prolog = set()
        if resultado_prolog.get('recomendacion'):
            cursos_prolog = {c['codigo'] for c in resultado_prolog['recomendacion'].get('cursos', [])}
        
        cursos_association = set()
        if resultado_association.get('recomendacion'):
            cursos_association = {c['codigo'] for c in resultado_association['recomendacion'].get('cursos', [])}
        
        # Cursos en común
        cursos_comunes = cursos_prolog & cursos_association
        
        return {
            "success": True,
            "prolog": resultado_prolog,
            "association_rules": resultado_association,
            "comparacion": {
                "total_cursos_prolog": len(resultado_prolog.get('recomendacion', {}).get('cursos', [])),
                "total_cursos_association": len(resultado_association.get('recomendacion', {}).get('cursos', [])),
                "creditos_prolog": resultado_prolog.get('recomendacion', {}).get('creditos_totales', 0),
                "creditos_association": resultado_association.get('recomendacion', {}).get('creditos_totales', 0),
                "cursos_comunes": list(cursos_comunes),
                "total_comunes": len(cursos_comunes),
                "similitud": len(cursos_comunes) / max(len(cursos_prolog), len(cursos_association), 1) * 100
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al comparar algoritmos: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al comparar algoritmos: {str(e)}"
        )


@router.get("/status")
async def obtener_estado_servicios():
    """
    ℹ️ Obtiene el estado de los servicios de recomendación
    
    Retorna información sobre:
    - Disponibilidad de Prolog (requiere SWI-Prolog instalado)
    - Estado del modelo de Reglas de Asociación (entrenado o no)
    - Total de reglas aprendidas
    - Rutas de archivos de configuración
    """
    return {
        "prolog": {
            "disponible": prolog_service.prolog is not None,
            "archivo_reglas": str(prolog_service.prolog_file) if prolog_service.prolog_file else None,
            "descripcion": "Motor de inferencia lógica para recomendaciones basadas en reglas"
        },
        "association_rules": {
            "disponible": association_service is not None,
            "entrenado": association_service.trained,
            "total_reglas": len(association_service.rules) if association_service.trained else 0,
            "descripcion": "Aprendizaje automático de patrones históricos de aprobación"
        },
        "algoritmos_clasicos": {
            "constraint_programming": "Disponible",
            "backtracking": "Disponible",
            "descripcion": "Algoritmos clásicos de búsqueda y optimización"
        }
    }
