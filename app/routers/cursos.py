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
            print(f"⚠️  Malla {malla_id} no encontrada")
            return {"prerequisitos": {}, "convalidaciones": {}}
        
        print(f"✓ Malla {malla_id} encontrada: {malla.nombre}")
        
        # Obtener todos los cursos de la malla
        cursos_malla = db.query(Curso).filter(Curso.malla_id == malla_id).all()
        curso_ids = [c.id for c in cursos_malla]
        
        print(f"✓ Encontrados {len(cursos_malla)} cursos en la malla")
        
        # Obtener prerequisitos directos
        prerequisitos = db.query(Prerequisito).filter(
            Prerequisito.curso_id.in_(curso_ids)
        ).all()
        
        print(f"✓ Encontrados {len(prerequisitos)} prerequisitos")
        
        # Construir mapa de prerequisitos
        prerequisitos_map = {}
        for prereq in prerequisitos:
            try:
                curso = db.query(Curso).filter(Curso.id == prereq.curso_id).first()
                curso_prereq = db.query(Curso).filter(Curso.id == prereq.prerequisito_id).first()
                
                if curso and curso_prereq:
                    if curso.codigo not in prerequisitos_map:
                        prerequisitos_map[curso.codigo] = []
                    prerequisitos_map[curso.codigo].append(curso_prereq.codigo)
            except Exception as e:
                print(f"⚠️  Error procesando prerequisito: {e}")
                continue
        
        # Agregar convalidaciones (cursos equivalentes de otras mallas)
        convalidaciones_map = {}
        try:
            # Obtener el año de la malla destino
            malla_anio = malla.anio
            print(f"  → Buscando convalidaciones hacia malla {malla_anio}")
            
            # Buscar convalidaciones donde esta malla es el destino
            convalidaciones = db.query(Convalidacion).filter(
                Convalidacion.malla_destino_anio == malla_anio
            ).all()
            
            print(f"✓ Encontradas {len(convalidaciones)} convalidaciones hacia malla {malla_anio}")
            
            for conv in convalidaciones:
                try:
                    curso_origen = db.query(Curso).filter(Curso.id == conv.curso_origen_id).first()
                    curso_destino = db.query(Curso).filter(Curso.id == conv.curso_destino_id).first()
                    
                    if curso_origen and curso_destino:
                        if curso_destino.codigo not in convalidaciones_map:
                            convalidaciones_map[curso_destino.codigo] = []
                        convalidaciones_map[curso_destino.codigo].append({
                            "codigo": curso_origen.codigo,
                            "nombre": curso_origen.nombre,
                            "malla_origen": conv.malla_origen_anio
                        })
                        print(f"  → {curso_origen.codigo} (malla {conv.malla_origen_anio}) → {curso_destino.codigo}")
                except Exception as e:
                    print(f"⚠️  Error procesando convalidación: {e}")
                    continue
        except Exception as e:
            print(f"⚠️  Error consultando convalidaciones: {e}")
        
        print(f"✓ Devolviendo {len(prerequisitos_map)} prerequisitos y {len(convalidaciones_map)} convalidaciones")
        
        return {
            "prerequisitos": prerequisitos_map,
            "convalidaciones": convalidaciones_map
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error crítico en get_prerequisitos_malla: {str(e)}")
        import traceback
        traceback.print_exc()
        # Devolver respuesta vacía en lugar de error 500
        return {"prerequisitos": {}, "convalidaciones": {}}
