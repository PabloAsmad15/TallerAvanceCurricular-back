from ortools.sat.python import cp_model
from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session
from ..models import Curso, Prerequisito, Malla


class ConstraintProgrammingSolver:
    """
    Algoritmo de Constraint Programming usando OR-Tools CP-SAT.
    Adaptado del código original para trabajar con base de datos.
    Resuelve el problema de recomendación como un CSP (Constraint Satisfaction Problem).
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # Límites de créditos por ciclo (de tu código original)
        self.creditos_por_ciclo = {
            1: 20, 2: 21, 3: 22, 4: 20, 5: 21,
            6: 21, 7: 21, 8: 20, 9: 22, 10: 17
        }
        self.min_creditos_ciclo = 12
    
    def recommend_courses(
        self,
        malla_id: int,
        cursos_aprobados_ids: List[int],
        max_cursos: int = 6
    ) -> List[Dict]:
        """
        Recomienda cursos usando Constraint Programming.
        ADAPTADO DEL CÓDIGO ORIGINAL recomendar_cursos()
        
        Args:
            malla_id: ID de la malla curricular
            cursos_aprobados_ids: Lista de IDs de cursos ya aprobados
            max_cursos: Máximo de cursos a recomendar
            
        Returns:
            Lista de diccionarios con cursos recomendados y su prioridad
        """
        
        # Obtener malla
        malla = self.db.query(Malla).filter(Malla.id == malla_id).first()
        if not malla:
            return []
        
        # Obtener todos los cursos de la malla
        todos_cursos = self.db.query(Curso).filter(
            Curso.malla_id == malla_id
        ).all()
        
        # Cursos pendientes
        cursos_pendientes_dict = {
            c.id: c for c in todos_cursos 
            if c.id not in cursos_aprobados_ids
        }
        
        if not cursos_pendientes_dict:
            return []
        
        # Determinar ciclo de matrícula (curso pendiente de menor ciclo)
        ciclo_de_matricula = min(c.ciclo for c in cursos_pendientes_dict.values())
        max_creditos_ciclo = self.creditos_por_ciclo.get(ciclo_de_matricula, 21)
        
        # Encontrar curso obligatorio (el de menor ciclo pendiente)
        curso_obligatorio = min(cursos_pendientes_dict.values(), key=lambda x: x.ciclo)
        curso_obligatorio_id = curso_obligatorio.id
        
        # Obtener prerequisitos
        prerequisitos_dict = self._get_prerequisitos_dict(malla_id)
        
        # OPTIMIZACIÓN: Reducir universo de búsqueda a ciclos relevantes
        # (igual que tu código: ciclo actual + 2 siguientes)
        universo_reducido = {
            c_id: c for c_id, c in cursos_pendientes_dict.items()
            if ciclo_de_matricula <= c.ciclo <= ciclo_de_matricula + 2
        }
        
        # Filtrar cursos que cumplen prerequisitos
        cursos_candidatos_dict = {}
        for c_id, curso in universo_reducido.items():
            if self._cumple_prerequisitos(c_id, cursos_aprobados_ids, prerequisitos_dict):
                cursos_candidatos_dict[c_id] = curso
        
        if not cursos_candidatos_dict:
            return []
        
        # Crear modelo CP-SAT
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()
        
        # Variables: cada curso puede ser 0 (no seleccionado) o 1 (seleccionado)
        curso_vars = {}
        for c_id in cursos_candidatos_dict:
            curso_vars[c_id] = model.NewBoolVar(f'curso_{c_id}')
        
        # RESTRICCIÓN 1: Curso obligatorio DEBE estar
        if curso_obligatorio_id in curso_vars:
            model.Add(curso_vars[curso_obligatorio_id] == 1)
        
        # RESTRICCIÓN 2: Límite de créditos
        creditos_expresion = sum(
            curso_vars[c_id] * cursos_candidatos_dict[c_id].creditos
            for c_id in cursos_candidatos_dict
        )
        model.Add(creditos_expresion >= self.min_creditos_ciclo)
        model.Add(creditos_expresion <= max_creditos_ciclo)
        
        # RESTRICCIÓN 3: No exceder número máximo de cursos
        model.Add(sum(curso_vars.values()) <= max_cursos)
        
        # OBJETIVO: Maximizar créditos (prioridad) y preferir ciclos bajos
        objetivo = []
        for c_id, curso in cursos_candidatos_dict.items():
            # Peso: más alto para ciclos inferiores y más créditos
            peso_ciclo = 100 - (curso.ciclo * 5)  # Ciclo 1=95, Ciclo 10=50
            peso_creditos = curso.creditos * 10
            peso_total = peso_ciclo + peso_creditos
            objetivo.append(curso_vars[c_id] * peso_total)
        
        model.Maximize(sum(objetivo))
        
        # Resolver
        status = solver.Solve(model)
        
        # Procesar resultados
        recomendados = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for c_id, var in curso_vars.items():
                if solver.Value(var) == 1:
                    curso = cursos_candidatos_dict[c_id]
                    es_obligatorio = (c_id == curso_obligatorio_id)
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
            
            # Ordenar por prioridad y ciclo
            recomendados.sort(key=lambda x: (x['prioridad'], x['ciclo']))
        
        return recomendados[:max_cursos]
    
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
            return 1
        elif curso.ciclo <= 3:
            return 1
        elif curso.ciclo <= 6:
            return 2
        else:
            return 3
    
    def _generar_razon(self, curso: Curso, es_obligatorio: bool, ciclo_matricula: int) -> str:
        """Genera razón de recomendación"""
        if es_obligatorio:
            return (f"Curso pendiente obligatorio del ciclo {ciclo_matricula}. "
                   f"El sistema de CP lo identificó como crítico para tu avance.")
        elif curso.ciclo == ciclo_matricula:
            return (f"Curso del ciclo {curso.ciclo}. "
                   f"Constraint Programming lo optimizó para cumplir límite de créditos.")
        elif curso.ciclo <= 3:
            return f"Curso fundamental del ciclo {curso.ciclo}. CP lo priorizó por su importancia."
        elif curso.ciclo <= 6:
            return f"Curso de especialización del ciclo {curso.ciclo}. Seleccionado por el optimizador."
        else:
            return f"Curso avanzado del ciclo {curso.ciclo}. Incluido en la solución óptima."
