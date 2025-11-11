from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import time
from ..database import get_db
from ..schemas import RecomendacionRequest, RecomendacionResponse, CursoRecomendado
from ..models import Usuario, Recomendacion, Curso, Malla, Prerequisito
from ..utils.security import get_current_active_user
from ..services.ai_agent import ai_agent
from ..algorithms.constraint_programming import ConstraintProgrammingSolver
from ..algorithms.backtracking import BacktrackingSolver

router = APIRouter()


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
    
    # Ejecutar el algoritmo elegido
    start_time = time.time()
    
    if algoritmo_elegido == "constraint_programming":
        solver = ConstraintProgrammingSolver(db)
        cursos_recomendados_raw = solver.recommend_courses(
            malla_id=request.malla_id,
            cursos_aprobados_ids=cursos_ids,  # Usar IDs convertidos
            max_cursos=6
        )
    else:  # backtracking
        solver = BacktrackingSolver(db)
        cursos_recomendados_raw = solver.recommend_courses(
            malla_id=request.malla_id,
            cursos_aprobados_ids=cursos_ids,  # Usar IDs convertidos
            max_cursos=6
        )
    
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
