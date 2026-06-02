from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import AssistantChatRequest, AssistantChatResponse, AssistantSource
from ..utils.security import get_current_active_user
from ..models import Usuario
from ..services.assistant_service import assistant_service

router = APIRouter()


@router.post("/chat", response_model=AssistantChatResponse)
async def chat_assistant(
    request: AssistantChatRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Chat del asistente academico con RAG y reglas curriculares."""
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no puede estar vacio"
        )

    answer, sources = assistant_service.chat(
        db=db,
        message=request.message,
        malla_id=request.malla_id,
        cursos_aprobados=request.cursos_aprobados,
        cursos_aprobados_multi_malla=request.cursos_aprobados_multi_malla,
        user_id=current_user.id,
    )

    return AssistantChatResponse(
        answer=answer,
        sources=[AssistantSource(**source) for source in sources]
    )
