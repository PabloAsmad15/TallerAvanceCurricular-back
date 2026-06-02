from __future__ import annotations

from typing import List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..config import settings
from ..models import Curso


class AssistantService:
    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
            max_output_tokens=512,
        )
        self.system_prompt = (
            "Eres un asistente academico de la UPAO. Ayudas con reglas curriculares, prerequisitos, "
            "planeamiento de cursos y lectura de normativa interna. Cumples estas reglas:\n"
            "- Nunca pides contrasenas, tokens ni credenciales.\n"
            "- No realizas acciones de administrador ni cambias permisos.\n"
            "- Si falta informacion, preguntas por datos academicos, no por credenciales.\n"
            "- Respondes en espanol, claro y directo, con respuestas breves y accionables.\n"
            "- Si no hay evidencia suficiente, pide una aclaracion concreta.\n"
            "- No inventes cursos. Si un curso no esta en la malla, dilo explicitamente.\n"
        )

    def chat(
        self,
        db: Session,
        message: str,
        malla_id: Optional[int],
        cursos_aprobados: Optional[List[str]],
        cursos_aprobados_multi_malla: Optional[List[dict]] = None
    ) -> Tuple[str, List[dict]]:
        cleaned_message = message.strip()
        if not cleaned_message:
            return "Escribe una consulta para poder ayudarte.", []

        if self._is_blocked_request(cleaned_message):
            return (
                "Lo siento, no puedo solicitar ni procesar credenciales, tokens ni acciones de administrador. "
                "Puedo ayudarte con consultas academicas y recomendaciones curriculares.",
                []
            )

        rules_context = self._get_malla_rules(db, malla_id)
        resumen_malla = self._get_malla_summary(db, malla_id)
        cursos_malla = self._get_malla_courses(db, malla_id)
        rag_sources = self._retrieve_rag(db, cleaned_message, settings.RAG_TOP_K)

        prompt = self._build_prompt(
            message=cleaned_message,
            rules_context=rules_context,
            resumen_malla=resumen_malla,
            cursos_malla=cursos_malla,
            cursos_aprobados=cursos_aprobados or [],
            cursos_aprobados_multi_malla=cursos_aprobados_multi_malla or [],
            rag_sources=rag_sources,
        )

        try:
            response = self.model.invoke(
                [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt),
                ]
            )
            answer = response.content.strip() if response and response.content else "No pude generar una respuesta."
        except Exception as exc:
            print(f"⚠️  Error en el modelo Gemini: {exc}")
            answer = (
                "El servicio de IA no esta disponible por ahora. "
                "Verifica que la configuracion de Gemini este activa e intenta de nuevo."
            )
            rag_sources = []

        return answer, rag_sources

    def _is_blocked_request(self, message: str) -> bool:
        lowered = message.lower()
        blocked_terms = [
            "password",
            "contrasena",
            "contraseña",
            "token",
            "api key",
            "service role",
            "admin",
            "administrador",
            "credenciales",
        ]
        return any(term in lowered for term in blocked_terms)

    def _get_malla_rules(self, db: Session, malla_id: Optional[int]) -> dict:
        if not malla_id:
            return {}

        query = text(
            """
            SELECT creditos_graduacion,
                   max_electivo_1,
                   max_electivo_2,
                   require_practicas_all_aprobado,
                   require_tesis_ciclo8_aprobado,
                   require_tesis_investigacion_aprobado
            FROM public.malla_reglas
            WHERE malla_id = :malla_id
            """
        )
        row = db.execute(query, {"malla_id": malla_id}).first()
        if not row:
            return {}

        return {
            "creditos_graduacion": row.creditos_graduacion,
            "max_electivo_1": row.max_electivo_1,
            "max_electivo_2": row.max_electivo_2,
            "require_practicas_all_aprobado": row.require_practicas_all_aprobado,
            "require_tesis_ciclo8_aprobado": row.require_tesis_ciclo8_aprobado,
            "require_tesis_investigacion_aprobado": row.require_tesis_investigacion_aprobado,
        }

    def _get_malla_summary(self, db: Session, malla_id: Optional[int]) -> dict:
        if not malla_id:
            return {}

        query = text(
            """
            SELECT COUNT(*) AS total_cursos,
                   COALESCE(SUM(creditos), 0) AS total_creditos
            FROM public.cursos
            WHERE malla_id = :malla_id
            """
        )
        row = db.execute(query, {"malla_id": malla_id}).first()
        if not row:
            return {}

        return {
            "total_cursos": row.total_cursos,
            "total_creditos": row.total_creditos,
        }

    def _get_malla_courses(self, db: Session, malla_id: Optional[int]) -> List[str]:
        if not malla_id:
            return []

        cursos = db.query(Curso).filter(Curso.malla_id == malla_id).order_by(Curso.ciclo, Curso.codigo).all()
        return [f"{curso.codigo} - {curso.nombre}" for curso in cursos]

    def _retrieve_rag(self, db: Session, query: str, top_k: int) -> List[dict]:
        if top_k <= 0:
            return []

        count_query = text("SELECT COUNT(*) FROM public.document_chunks WHERE embedding IS NOT NULL")
        with_embeddings = db.execute(count_query).scalar() or 0
        if with_embeddings == 0:
            return []

        embedding = self._embed_query(query)
        if not embedding:
            return []

        emb_str = "[" + ",".join(str(v) for v in embedding) + "]"
        rag_query = text(
            """
            SELECT dc.content,
                   dc.chunk_index,
                   d.source,
                   d.title
            FROM public.document_chunks dc
            JOIN public.documents d ON d.id = dc.document_id
            WHERE dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> :query_embedding::vector
            LIMIT :top_k
            """
        )
        rows = db.execute(
            rag_query,
            {"query_embedding": emb_str, "top_k": top_k}
        ).fetchall()

        sources = []
        for row in rows:
            content = (row.content or "").strip()
            sources.append({
                "source": row.source,
                "title": row.title,
                "chunk_index": row.chunk_index,
                "content": content[:600],
            })

        return sources

    def _embed_query(self, text_value: str) -> Optional[List[float]]:
        try:
            result = genai.embed_content(
                model=settings.GEMINI_EMBED_MODEL,
                content=text_value,
                task_type="retrieval_query",
            )
            return result["embedding"]
        except Exception:
            try:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text_value,
                    task_type="retrieval_query",
                )
                return result["embedding"]
            except Exception:
                return None

    def _build_prompt(
        self,
        message: str,
        rules_context: dict,
        resumen_malla: dict,
        cursos_malla: List[str],
        cursos_aprobados: List[str],
        cursos_aprobados_multi_malla: List[dict],
        rag_sources: List[dict],
    ) -> str:
        rules_lines = []
        if rules_context:
            rules_lines = [
                f"- Creditos de graduacion: {rules_context.get('creditos_graduacion')}",
                f"- Max electivo 1: {rules_context.get('max_electivo_1')}",
                f"- Max electivo 2: {rules_context.get('max_electivo_2')}",
                f"- Practicas requiere todo aprobado: {rules_context.get('require_practicas_all_aprobado')}",
                f"- Tesis I requiere ciclo 8 aprobado: {rules_context.get('require_tesis_ciclo8_aprobado')}",
                f"- Tesis I requiere investigacion aprobada: {rules_context.get('require_tesis_investigacion_aprobado')}",
            ]

        resumen_lines = []
        if resumen_malla:
            resumen_lines = [
                f"- Total cursos malla: {resumen_malla.get('total_cursos')}",
                f"- Total creditos malla: {resumen_malla.get('total_creditos')}",
            ]

        approved_count = len(cursos_aprobados)
        cursos_list = ", ".join(cursos_aprobados[:30]) if cursos_aprobados else "(no proporcionado)"

        multi_malla_count = len(cursos_aprobados_multi_malla)
        multi_malla_preview = ", ".join(
            f"{item.get('codigo')}({item.get('malla_origen_anio')})"
            for item in cursos_aprobados_multi_malla[:20]
        ) if cursos_aprobados_multi_malla else "(no proporcionado)"

        rag_text = "\n".join(
            f"[Fuente {idx + 1}] {src.get('title') or src.get('source') or 'Documento'}\n{src.get('content', '')}"
            for idx, src in enumerate(rag_sources)
        )

        cursos_malla_text = "\n".join(cursos_malla) if cursos_malla else "(sin cursos de malla)"

        prompt = f"""
    Contexto del estudiante:
- Cursos aprobados (malla actual): {approved_count}
- Lista de cursos aprobados: {cursos_list}
- Cursos aprobados multi-malla: {multi_malla_count}
- Lista multi-malla: {multi_malla_preview}

Reglas de malla:
{chr(10).join(rules_lines) if rules_lines else '- (sin reglas cargadas)'}

Resumen de malla:
{chr(10).join(resumen_lines) if resumen_lines else '- (sin resumen)'}

Cursos de la malla (usa solo estos para recomendaciones):
{cursos_malla_text}

Fuentes RAG (si existen):
{rag_text if rag_text else '(sin fuentes)'}

Pregunta del estudiante:
{message}

Instrucciones de respuesta:
- Usa las fuentes RAG si existen. Si no hay fuentes, responde con reglas conocidas y pide confirmacion puntual.
- Si la consulta pide credenciales o admin, rechaza y redirige a temas academicos.
- Responde en 4-8 lineas maximo, directo y con pasos accionables cuando aplique.
- Si no puedes concluir, pide 1 dato especifico.
"""
        return prompt.strip()


assistant_service = AssistantService()
