from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import CursoResponse, CursoPorCiclo
from ..models import Curso, Prerequisito, Convalidacion, Malla
from ..utils.security import get_current_active_user, Usuario

router = APIRouter()


@router.get("/malla/{malla_id}", response_model=List[CursoResponse])
async def get_cursos_by_malla(
    malla_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todos los cursos de una malla"""
    cursos = db.query(Curso).filter(
        Curso.malla_id == malla_id
    ).order_by(Curso.ciclo, Curso.codigo).all()
    
    return cursos


@router.get("/malla/{malla_id}/por-ciclo", response_model=List[CursoPorCiclo])
async def get_cursos_by_ciclo(
    malla_id: int,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """Obtener un curso específico"""
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    
    if not curso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso no encontrado"
        )
    
    return curso


@router.get("/malla/{malla_id}/prerequisitos")
async def get_prerequisitos_malla(
    malla_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todos los prerequisitos de una malla (incluye convalidaciones)"""
    
    try:
        # Verificar que la malla existe
        malla = db.query(Malla).filter(Malla.id == malla_id).first()
        if not malla:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Malla con ID {malla_id} no encontrada"
            )
        
        # Obtener prerequisitos directos
        prerequisitos = db.query(Prerequisito).join(
            Curso, Prerequisito.curso_id == Curso.id
        ).filter(Curso.malla_id == malla_id).all()
        
        # Construir mapa de prerequisitos
        prerequisitos_map = {}
        for prereq in prerequisitos:
            curso = db.query(Curso).filter(Curso.id == prereq.curso_id).first()
            curso_prereq = db.query(Curso).filter(Curso.id == prereq.prerequisito_id).first()
            
            if curso and curso_prereq:
                if curso.codigo not in prerequisitos_map:
                    prerequisitos_map[curso.codigo] = []
                prerequisitos_map[curso.codigo].append(curso_prereq.codigo)
        
        # Agregar convalidaciones (cursos equivalentes de otras mallas)
        convalidaciones = db.query(Convalidacion).filter(
            Convalidacion.malla_destino_id == malla_id
        ).all()
        
        convalidaciones_map = {}
        for conv in convalidaciones:
            curso_origen = db.query(Curso).filter(Curso.id == conv.curso_origen_id).first()
            curso_destino = db.query(Curso).filter(Curso.id == conv.curso_destino_id).first()
            
            if curso_origen and curso_destino:
                if curso_destino.codigo not in convalidaciones_map:
                    convalidaciones_map[curso_destino.codigo] = []
                convalidaciones_map[curso_destino.codigo].append(curso_origen.codigo)
        
        return {
            "prerequisitos": prerequisitos_map,
            "convalidaciones": convalidaciones_map
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en get_prerequisitos_malla: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener prerequisitos: {str(e)}"
        )
