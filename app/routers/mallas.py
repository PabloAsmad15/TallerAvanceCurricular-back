from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import MallaResponse
from ..models import Malla
from ..utils.security import get_current_active_user, Usuario

router = APIRouter()


@router.get("/{malla_id}", response_model=MallaResponse)
async def get_malla(
    malla_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener una malla específica"""
    malla = db.query(Malla).filter(Malla.id == malla_id).first()
    
    if not malla:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Malla no encontrada"
        )
    
    return malla
