from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import CursoResponse, CursoPorCiclo
from ..models import Curso
from ..utils.security import get_current_active_user, Usuario

router = APIRouter()


@router.get("/malla/{malla_id}", response_model=List[CursoResponse])
async def get_cursos_by_malla(
    malla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener todos los cursos de una malla"""
    cursos = db.query(Curso).filter(
        Curso.malla_id == malla_id
    ).order_by(Curso.ciclo, Curso.codigo).all()
    
    return cursos


@router.get("/malla/{malla_id}/por-ciclo", response_model=List[CursoPorCiclo])
async def get_cursos_by_ciclo(
    malla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener cursos agrupados por ciclo"""
    cursos = db.query(Curso).filter(
        Curso.malla_id == malla_id
    ).order_by(Curso.ciclo, Curso.codigo).all()
    
    # Agrupar por ciclo
    cursos_por_ciclo = {}
    for curso in cursos:
        if curso.ciclo not in cursos_por_ciclo:
            cursos_por_ciclo[curso.ciclo] = []
        cursos_por_ciclo[curso.ciclo].append(curso)
    
    # Formatear respuesta
    resultado = [
        CursoPorCiclo(ciclo=ciclo, cursos=cursos)
        for ciclo, cursos in sorted(cursos_por_ciclo.items())
    ]
    
    return resultado


@router.get("/{curso_id}", response_model=CursoResponse)
async def get_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener un curso específico"""
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    
    if not curso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )
    
    return curso
