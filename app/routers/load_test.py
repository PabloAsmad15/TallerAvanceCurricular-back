"""
Endpoints para pruebas de carga (Load Testing)
ADVERTENCIA: Estos endpoints NO tienen autenticación.
Solo usar en ambiente de desarrollo/testing.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..models import Curso, Malla, Usuario
from ..routers.recommendations import (
    obtener_cursos_disponibles,
    ConstraintProgrammingSolver,
    BacktrackingSolver,
    prolog_service,
    association_service,
    cargar_malla_completa,
    cargar_todas_las_mallas,
    obtener_mapa_convalidaciones,
    ai_agent
)
import time

router = APIRouter(tags=["Load Testing"])


class LoadTestRecommendationRequest(BaseModel):
    """Request para pruebas de carga - sin autenticación"""
    malla_id: int
    cursos_aprobados: List[str]
    algoritmo: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "malla_id": 1,
                "cursos_aprobados": ["CIEN-397", "HUMA-899", "HUMA-900", "ICSI-401"]
            }
        }


class LoadTestMultiMallaRequest(BaseModel):
    """Request para pruebas multi-malla sin autenticación"""
    malla_id: int
    cursos_aprobados_multi_malla: List[dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "malla_id": 3,
                "cursos_aprobados_multi_malla": [
                    {"codigo": "CIEN-397", "malla_origen_anio": "2015"},
                    {"codigo": "HUMA-899", "malla_origen_anio": "2015"},
                    {"codigo": "ICSI-506", "malla_origen_anio": "2019"}
                ]
            }
        }


@router.post("/recommendations/simple")
async def test_create_simple_recommendation(
    request: LoadTestRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de prueba para crear recomendación simple (sin autenticación)
    Usa Constraint Programming por defecto
    """
    print(f"\n[LOAD TEST] Recomendación simple - Malla {request.malla_id}")
    
    # Validar malla
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malla con ID {request.malla_id} no encontrada"
        )
    
    # Obtener cursos
    todos_cursos = db.query(Curso).filter(Curso.malla_id == request.malla_id).all()
    cursos_map = {c.codigo: c for c in todos_cursos}
    
    cursos_aprobados_validados = []
    for codigo in request.cursos_aprobados:
        if codigo in cursos_map:
            cursos_aprobados_validados.append(cursos_map[codigo])
    
    cursos_aprobados_ids = [c.id for c in cursos_aprobados_validados]
    
    # Obtener cursos disponibles
    cursos_disponibles = obtener_cursos_disponibles(
        db, request.malla_id, cursos_aprobados_ids
    )
    
    # Ejecutar algoritmo
    start_time = time.time()
    solver = ConstraintProgrammingSolver(db)
    cursos_rec = solver.recommend_courses(
        malla_id=request.malla_id,
        cursos_aprobados_ids=cursos_aprobados_ids,
        max_cursos=6
    )
    tiempo = time.time() - start_time
    
    # Formatear respuesta
    cursos_recomendados = []
    total_creditos = 0
    for curso_data in cursos_rec:
        if isinstance(curso_data, dict):
            curso_id = curso_data.get('curso_id')
            curso_db = db.query(Curso).filter(Curso.id == curso_id).first()
            if curso_db:
                cursos_recomendados.append({
                    "codigo": curso_db.codigo,
                    "nombre": curso_db.nombre,
                    "ciclo": curso_db.ciclo,
                    "creditos": curso_db.creditos
                })
                total_creditos += curso_db.creditos
    
    return {
        "success": True,
        "algoritmo": "constraint_programming",
        "malla": malla.nombre,
        "cursos_aprobados": len(cursos_aprobados_validados),
        "cursos_recomendados": cursos_recomendados,
        "total_cursos": len(cursos_recomendados),
        "total_creditos": total_creditos,
        "tiempo_ejecucion": round(tiempo, 3),
        "test_mode": True
    }


@router.post("/recommendations/multi-malla")
async def test_create_multimalla_recommendation(
    request: LoadTestMultiMallaRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de prueba para recomendación multi-malla (sin autenticación)
    """
    print(f"\n[LOAD TEST] Recomendación multi-malla - Malla destino {request.malla_id}")
    
    # Validar malla
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malla con ID {request.malla_id} no encontrada"
        )
    
    # Procesar cursos multi-malla
    from ..utils.multi_malla_validator import procesar_cursos_multi_malla
    
    cursos_aprobados_ids, info_convalidacion = procesar_cursos_multi_malla(
        db=db,
        malla_destino_anio=malla.anio,
        cursos_aprobados_multi_malla=request.cursos_aprobados_multi_malla
    )
    
    # Ejecutar algoritmo
    start_time = time.time()
    solver = ConstraintProgrammingSolver(db)
    cursos_rec = solver.recommend_courses(
        malla_id=request.malla_id,
        cursos_aprobados_ids=cursos_aprobados_ids,
        max_cursos=6
    )
    tiempo = time.time() - start_time
    
    # Formatear respuesta
    cursos_recomendados = []
    total_creditos = 0
    for curso_data in cursos_rec:
        if isinstance(curso_data, dict):
            curso_id = curso_data.get('curso_id')
            curso_db = db.query(Curso).filter(Curso.id == curso_id).first()
            if curso_db:
                cursos_recomendados.append({
                    "codigo": curso_db.codigo,
                    "nombre": curso_db.nombre,
                    "ciclo": curso_db.ciclo,
                    "creditos": curso_db.creditos
                })
                total_creditos += curso_db.creditos
    
    return {
        "success": True,
        "algoritmo": "constraint_programming",
        "malla": malla.nombre,
        "cursos_procesados": len(request.cursos_aprobados_multi_malla),
        "cursos_convalidados": len(cursos_aprobados_ids),
        "cursos_recomendados": cursos_recomendados,
        "total_cursos": len(cursos_recomendados),
        "total_creditos": total_creditos,
        "tiempo_ejecucion": round(tiempo, 3),
        "test_mode": True
    }


@router.post("/recommendations/comparar-algoritmos")
async def test_compare_algorithms(
    request: LoadTestMultiMallaRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de prueba para comparar 4 algoritmos (sin autenticación)
    ADVERTENCIA: Este endpoint es pesado y puede tardar varios segundos
    """
    print(f"\n[LOAD TEST] Comparar algoritmos - Malla destino {request.malla_id}")
    
    # Validar malla
    malla = db.query(Malla).filter(Malla.id == request.malla_id).first()
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Malla con ID {request.malla_id} no encontrada"
        )
    
    # Procesar cursos multi-malla
    from ..utils.multi_malla_validator import procesar_cursos_multi_malla
    
    cursos_aprobados_ids, info_convalidacion = procesar_cursos_multi_malla(
        db=db,
        malla_destino_anio=malla.anio,
        cursos_aprobados_multi_malla=request.cursos_aprobados_multi_malla
    )
    
    # Ejecutar los 4 algoritmos
    resultados = []
    algoritmos = [
        ("constraint_programming", "CP-SAT"),
        ("backtracking", "Backtracking"),
        ("prolog", "Prolog"),
        ("association_rules", "Association Rules")
    ]
    
    for algo_key, algo_nombre in algoritmos:
        try:
            start_time = time.time()
            cursos_rec = []
            
            if algo_key == "constraint_programming":
                solver = ConstraintProgrammingSolver(db)
                cursos_rec = solver.recommend_courses(
                    malla_id=request.malla_id,
                    cursos_aprobados_ids=cursos_aprobados_ids,
                    max_cursos=6
                )
            elif algo_key == "backtracking":
                solver = BacktrackingSolver(db)
                cursos_rec = solver.recommend_courses(
                    malla_id=request.malla_id,
                    cursos_aprobados_ids=cursos_aprobados_ids,
                    max_cursos=6
                )
            
            tiempo = time.time() - start_time
            
            # Contar cursos y créditos
            num_cursos = len(cursos_rec)
            total_creditos = 0
            for curso_data in cursos_rec:
                if isinstance(curso_data, dict):
                    curso_id = curso_data.get('curso_id')
                    curso_db = db.query(Curso).filter(Curso.id == curso_id).first()
                    if curso_db:
                        total_creditos += curso_db.creditos
            
            resultados.append({
                "algoritmo": algo_key,
                "nombre": algo_nombre,
                "success": True,
                "num_cursos": num_cursos,
                "total_creditos": total_creditos,
                "tiempo_ejecucion": round(tiempo, 3),
                "error": None
            })
            
        except Exception as e:
            resultados.append({
                "algoritmo": algo_key,
                "nombre": algo_nombre,
                "success": False,
                "num_cursos": 0,
                "total_creditos": 0,
                "tiempo_ejecucion": 0,
                "error": str(e)
            })
    
    # Calcular métricas
    exitosos = [r for r in resultados if r["success"]]
    
    return {
        "success": True,
        "malla": malla.nombre,
        "cursos_procesados": len(request.cursos_aprobados_multi_malla),
        "resultados": resultados,
        "metricas": {
            "algoritmos_exitosos": len(exitosos),
            "algoritmo_mas_rapido": min(exitosos, key=lambda x: x["tiempo_ejecucion"])["algoritmo"] if exitosos else None,
            "tiempo_total": round(sum(r["tiempo_ejecucion"] for r in exitosos), 3)
        },
        "test_mode": True
    }


@router.get("/health")
async def test_health_check():
    """Endpoint simple para verificar que el servidor responde"""
    return {
        "status": "ok",
        "message": "Load testing endpoints disponibles",
        "timestamp": time.time()
    }
