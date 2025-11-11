from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Usuario, Recomendacion, Malla, Curso
from ..utils.security import get_current_active_user

router = APIRouter()


def verificar_admin(current_user: Usuario = Depends(get_current_active_user)):
    """Middleware para verificar que el usuario sea administrador"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user


@router.get("/stats/general")
async def get_general_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_admin)
):
    """Obtener estadísticas generales del sistema"""
    
    # Total de usuarios
    total_usuarios = db.query(Usuario).count()
    usuarios_activos = db.query(Usuario).filter(Usuario.is_active == True).count()
    
    # Total de recomendaciones
    total_recomendaciones = db.query(Recomendacion).count()
    
    # Recomendaciones por algoritmo
    recomendaciones_por_algoritmo = db.query(
        Recomendacion.algoritmo_usado,
        func.count(Recomendacion.id).label('count')
    ).group_by(Recomendacion.algoritmo_usado).all()
    
    algoritmos_stats = {
        "constraint_programming": 0,
        "backtracking": 0
    }
    for alg, count in recomendaciones_por_algoritmo:
        if alg:
            algoritmos_stats[alg] = count
    
    # Recomendaciones de los últimos 7 días
    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    recomendaciones_recientes = db.query(Recomendacion).filter(
        Recomendacion.created_at >= hace_7_dias
    ).count()
    
    # Total de mallas y cursos
    total_mallas = db.query(Malla).count()
    total_cursos = db.query(Curso).count()
    
    # Promedio de cursos recomendados - calcular en Python en lugar de SQL
    recomendaciones_list = db.query(Recomendacion).all()
    if recomendaciones_list:
        total_cursos_recomendados = sum(
            len(r.cursos_recomendados) if r.cursos_recomendados else 0 
            for r in recomendaciones_list
        )
        avg_cursos = round(total_cursos_recomendados / len(recomendaciones_list), 1)
    else:
        avg_cursos = 0
    
    # Usuarios más activos (top 5)
    usuarios_activos_top = db.query(
        Usuario.id,
        Usuario.nombre,
        Usuario.apellido,
        Usuario.email,
        func.count(Recomendacion.id).label('recomendaciones_count')
    ).join(Recomendacion).group_by(
        Usuario.id, Usuario.nombre, Usuario.apellido, Usuario.email
    ).order_by(desc('recomendaciones_count')).limit(5).all()
    
    return {
        "usuarios": {
            "total": total_usuarios,
            "activos": usuarios_activos,
            "inactivos": total_usuarios - usuarios_activos
        },
        "recomendaciones": {
            "total": total_recomendaciones,
            "ultimos_7_dias": recomendaciones_recientes,
            "promedio_cursos_por_recomendacion": avg_cursos
        },
        "algoritmos": {
            "constraint_programming": {
                "nombre": "Programación por Restricciones",
                "total": algoritmos_stats["constraint_programming"],
                "porcentaje": round((algoritmos_stats["constraint_programming"] / total_recomendaciones * 100), 1) if total_recomendaciones > 0 else 0
            },
            "backtracking": {
                "nombre": "Backtracking",
                "total": algoritmos_stats["backtracking"],
                "porcentaje": round((algoritmos_stats["backtracking"] / total_recomendaciones * 100), 1) if total_recomendaciones > 0 else 0
            }
        },
        "datos_academicos": {
            "total_mallas": total_mallas,
            "total_cursos": total_cursos
        },
        "usuarios_mas_activos": [
            {
                "id": u.id,
                "nombre_completo": f"{u.nombre} {u.apellido}",
                "email": u.email,
                "recomendaciones": u.recomendaciones_count
            }
            for u in usuarios_activos_top
        ]
    }


@router.get("/stats/recomendaciones")
async def get_recomendaciones_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_admin)
):
    """Estadísticas detalladas de recomendaciones"""
    
    # Recomendaciones por día de los últimos 30 días
    hace_30_dias = datetime.utcnow() - timedelta(days=30)
    
    recomendaciones_diarias = db.query(
        func.date(Recomendacion.created_at).label('fecha'),
        func.count(Recomendacion.id).label('cantidad')
    ).filter(
        Recomendacion.created_at >= hace_30_dias
    ).group_by('fecha').order_by('fecha').all()
    
    # Recomendaciones por malla
    recomendaciones_por_malla = db.query(
        Malla.anio,
        Malla.nombre,
        func.count(Recomendacion.id).label('cantidad')
    ).join(Recomendacion).group_by(
        Malla.id, Malla.anio, Malla.nombre
    ).all()
    
    return {
        "recomendaciones_diarias": [
            {
                "fecha": str(fecha),
                "cantidad": cantidad
            }
            for fecha, cantidad in recomendaciones_diarias
        ],
        "por_malla": [
            {
                "anio": anio,
                "nombre": nombre,
                "cantidad": cantidad
            }
            for anio, nombre, cantidad in recomendaciones_por_malla
        ]
    }


@router.get("/usuarios")
async def get_usuarios_lista(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_admin)
):
    """Listar usuarios del sistema"""
    
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    total = db.query(Usuario).count()
    
    # Obtener conteo de recomendaciones por usuario
    usuarios_data = []
    for usuario in usuarios:
        recomendaciones_count = db.query(Recomendacion).filter(
            Recomendacion.usuario_id == usuario.id
        ).count()
        
        usuarios_data.append({
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "is_active": usuario.is_active,
            "is_admin": usuario.is_admin,
            "created_at": usuario.created_at,
            "total_recomendaciones": recomendaciones_count
        })
    
    return {
        "usuarios": usuarios_data,
        "total": total,
        "pagina": skip // limit + 1,
        "total_paginas": (total + limit - 1) // limit
    }


@router.get("/recomendaciones/recientes")
async def get_recomendaciones_recientes(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(verificar_admin)
):
    """Obtener las recomendaciones más recientes"""
    
    recomendaciones = db.query(Recomendacion).join(Usuario).join(Malla).order_by(
        desc(Recomendacion.created_at)
    ).limit(limit).all()
    
    return {
        "recomendaciones": [
            {
                "id": r.id,
                "usuario": {
                    "nombre": f"{r.usuario.nombre} {r.usuario.apellido}",
                    "email": r.usuario.email
                },
                "malla": {
                    "anio": r.malla.anio,
                    "nombre": r.malla.nombre
                },
                "algoritmo": r.algoritmo_usado,
                "total_cursos_recomendados": len(r.cursos_recomendados) if r.cursos_recomendados else 0,
                "tiempo_ejecucion": r.tiempo_ejecucion,
                "created_at": r.created_at
            }
            for r in recomendaciones
        ]
    }
