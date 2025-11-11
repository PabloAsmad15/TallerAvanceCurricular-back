from typing import List, Dict, Set
from sqlalchemy.orm import Session
from ..models import Curso, Prerequisito, Malla


class BacktrackingSolver:
    """
    Algoritmo de Backtracking para recomendación de cursos.
    Adaptado del código original con mejoras para base de datos.
    Realiza búsqueda por ramas (ciclos) considerando estado regular/irregular.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mejor_solucion = []
        self.mejor_score = -1
        # Límites de créditos por ciclo (basado en tu código original)
        self.creditos_por_ciclo = {
            1: 20, 2: 21, 3: 22, 4: 20, 5: 21,
            6: 21, 7: 21, 8: 20, 9: 22, 10: 17
        }
    
    def recommend_courses(
        self,
        malla_id: int,
        cursos_aprobados_ids: List[int],
        max_cursos: int = 6
    ) -> List[Dict]:
        """
        Recomienda cursos usando Backtracking por ramas.
        ADAPTADO DEL CÓDIGO ORIGINAL recomendar_por_ramas()
        
        Args:
            malla_id: ID de la malla curricular
            cursos_aprobados_ids: Lista de IDs de cursos ya aprobados
            max_cursos: Máximo de cursos a recomendar
            
        Returns:
            Lista de diccionarios con cursos recomendados y su prioridad
        """
        
        # Obtener malla para saber el año
        malla = self.db.query(Malla).filter(Malla.id == malla_id).first()
        if not malla:
            return []
        
        # Obtener todos los cursos de la malla organizados por ciclo
        todos_cursos = self.db.query(Curso).filter(
            Curso.malla_id == malla_id
        ).order_by(Curso.ciclo, Curso.codigo).all()
        
        # Organizar cursos por ciclo
        cursos_por_ciclo = {}
        for curso in todos_cursos:
            if curso.ciclo not in cursos_por_ciclo:
                cursos_por_ciclo[curso.ciclo] = []
            cursos_por_ciclo[curso.ciclo].append(curso)
        
        cursos_aprobados_set = set(cursos_aprobados_ids)
        
        # Determinar último ciclo completo (lógica de tu código original)
        ultimo_ciclo_completo = 0
        for ciclo in range(1, 11):
            cursos_del_ciclo = cursos_por_ciclo.get(ciclo, [])
            if not cursos_del_ciclo:
                break
            
            codigos_cursos_ciclo = {c.id for c in cursos_del_ciclo}
            cursos_faltantes = codigos_cursos_ciclo - cursos_aprobados_set
            
            if cursos_faltantes:
                # Hay cursos pendientes en este ciclo
                break
            
            ultimo_ciclo_completo = ciclo
        
        # Ciclo de matrícula
        ciclo_de_matricula = ultimo_ciclo_completo + 1
        max_creditos = self.creditos_por_ciclo.get(ciclo_de_matricula, 21)
        
        # Obtener cursos del ciclo de matrícula
        cursos_del_ciclo = cursos_por_ciclo.get(ciclo_de_matricula, [])
        cursos_pendientes_ciclo = {
            c.id for c in cursos_del_ciclo 
            if c.id not in cursos_aprobados_set
        }
        
        # Obtener prerequisitos
        prerequisitos_dict = self._get_prerequisitos_dict(malla_id)
        
        # FASE 1: Agregar cursos pendientes obligatorios del ciclo actual
        recomendacion = []
        creditos_actuales = 0
        
        for curso_id in sorted(list(cursos_pendientes_ciclo)):
            curso = next(c for c in cursos_del_ciclo if c.id == curso_id)
            
            # Verificar prerequisitos
            if not self._cumple_prerequisitos(curso.id, list(cursos_aprobados_set), prerequisitos_dict):
                continue
            
            # Verificar créditos
            if creditos_actuales + curso.creditos <= max_creditos:
                recomendacion.append(curso)
                creditos_actuales += curso.creditos
        
        # FASE 2: Si hay espacio, agregar cursos de la siguiente rama
        siguiente_rama = ciclo_de_matricula + 1
        cursos_siguiente_rama = cursos_por_ciclo.get(siguiente_rama, [])
        
        for curso in sorted(cursos_siguiente_rama, key=lambda x: x.codigo):
            if curso.id in cursos_aprobados_set:
                continue
            
            # Verificar si excede límite de créditos
            if creditos_actuales + curso.creditos > max_creditos:
                continue
            
            # Verificar prerequisitos
            if not self._cumple_prerequisitos(curso.id, list(cursos_aprobados_set), prerequisitos_dict):
                continue
            
            recomendacion.append(curso)
            creditos_actuales += curso.creditos
        
        # Formatear resultados
        recomendados = []
        for curso in recomendacion:
            es_obligatorio = curso.id in cursos_pendientes_ciclo
            prioridad = self._calcular_prioridad(curso, es_obligatorio)
            razon = self._generar_razon(curso, es_obligatorio, ciclo_de_matricula)
            
            recomendados.append({
                'curso_id': curso.id,
                'codigo': curso.codigo,
                'nombre': curso.nombre,
                'creditos': curso.creditos,
                'ciclo': curso.ciclo,
                'prioridad': prioridad,
                'razon': razon
            })
        
        # Ordenar por prioridad (obligatorios primero) y luego por ciclo
        recomendados.sort(key=lambda x: (x['prioridad'], x['ciclo']))
        
        return recomendados[:max_cursos]
    
    def _backtrack(
        self,
        cursos_disponibles: List[Curso],
        solucion_actual: List[Curso],
        indice: int,
        max_cursos: int,
        cursos_aprobados: List[int],
        prerequisitos_dict: Dict[int, List[int]]
    ):
        """Función recursiva de backtracking"""
        
        # Caso base: evaluamos la solución actual
        if len(solucion_actual) > 0:
            score = self._evaluar_solucion(solucion_actual)
            if score > self.mejor_score:
                self.mejor_score = score
                self.mejor_solucion = solucion_actual.copy()
        
        # Poda: si ya tenemos max_cursos, no seguimos
        if len(solucion_actual) >= max_cursos:
            return
        
        # Poda: si no quedan cursos por explorar
        if indice >= len(cursos_disponibles):
            return
        
        # Explorar ramas
        for i in range(indice, len(cursos_disponibles)):
            curso = cursos_disponibles[i]
            
            # Incluir curso en la solución
            solucion_actual.append(curso)
            
            # Recursión
            self._backtrack(
                cursos_disponibles,
                solucion_actual,
                i + 1,
                max_cursos,
                cursos_aprobados,
                prerequisitos_dict
            )
            
            # Backtrack: quitar curso
            solucion_actual.pop()
    
    def _evaluar_solucion(self, solucion: List[Curso]) -> float:
        """
        Evalúa qué tan buena es una solución.
        Mayor score = mejor solución
        """
        if not solucion:
            return 0
        
        score = 0
        
        # Factor 1: Número de cursos (más es mejor, hasta cierto límite)
        score += len(solucion) * 10
        
        # Factor 2: Priorizar ciclos inferiores
        ciclo_promedio = sum(c.ciclo for c in solucion) / len(solucion)
        score += (11 - ciclo_promedio) * 5  # Ciclos bajos dan más puntos
        
        # Factor 3: Balance de créditos (preferir 15-18 créditos totales)
        creditos_totales = sum(c.creditos for c in solucion)
        if 15 <= creditos_totales <= 18:
            score += 20
        elif creditos_totales < 15:
            score += creditos_totales
        else:
            score -= (creditos_totales - 18)  # Penalizar sobrecarga
        
        return score
    
    def _get_prerequisitos_dict(self, malla_id: int) -> Dict[int, List[int]]:
        """Obtiene diccionario de prerequisitos"""
        prerequisitos = self.db.query(Prerequisito).join(
            Curso, Prerequisito.curso_id == Curso.id
        ).filter(
            Curso.malla_id == malla_id
        ).all()
        
        prereq_dict = {}
        for prereq in prerequisitos:
            if prereq.curso_id not in prereq_dict:
                prereq_dict[prereq.curso_id] = []
            prereq_dict[prereq.curso_id].append(prereq.prerequisito_id)
        
        return prereq_dict
    
    def _cumple_prerequisitos(
        self,
        curso_id: int,
        cursos_aprobados: List[int],
        prerequisitos_dict: Dict[int, List[int]]
    ) -> bool:
        """Verifica si se cumplen los prerequisitos de un curso"""
        prerequisitos = prerequisitos_dict.get(curso_id, [])
        return all(prereq_id in cursos_aprobados for prereq_id in prerequisitos)
    
    def _calcular_prioridad(self, curso: Curso, es_obligatorio: bool) -> int:
        """
        Calcula prioridad del curso (1: Alta, 2: Media, 3: Baja)
        Obligatorios siempre tienen alta prioridad
        """
        if es_obligatorio:
            return 1  # Alta prioridad para cursos pendientes del ciclo actual
        elif curso.ciclo <= 3:
            return 1
        elif curso.ciclo <= 6:
            return 2
        else:
            return 3
    
    def _generar_razon(self, curso: Curso, es_obligatorio: bool, ciclo_matricula: int) -> str:
        """Genera razón de recomendación basada en lógica de ramas"""
        if es_obligatorio:
            return (f"Curso pendiente obligatorio del ciclo {ciclo_matricula}. "
                   f"Debes aprobar este curso para regularizar tu avance.")
        elif curso.ciclo == ciclo_matricula + 1:
            return (f"Curso de avance del ciclo {curso.ciclo}. "
                   f"Puedes adelantar este curso ya que cumples los prerequisitos.")
        elif curso.ciclo <= 3:
            return f"Curso fundamental del ciclo {curso.ciclo}. Alta prioridad para avance base."
        elif curso.ciclo <= 6:
            return f"Curso de especialización del ciclo {curso.ciclo}. Importante para tu formación."
        else:
            return f"Curso avanzado del ciclo {curso.ciclo}. Necesario para completar tu malla."
