import google.generativeai as genai
from typing import Dict, List, Tuple
from ..config import settings

# Configurar Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


class AIAgent:
    """
    Agente de IA que decide qué algoritmo de recomendación usar.
    Utiliza Gemini para analizar el contexto y elegir entre:
    - Constraint Programming: Para problemas complejos con muchas restricciones
    - Backtracking: Para búsquedas más simples y directas
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
    
    def decide_algorithm(
        self,
        total_cursos: int,
        cursos_aprobados: int,
        cursos_pendientes: int,
        num_prerequisitos: int,
        ciclo_actual: int,
        malla_anio: int
    ) -> Tuple[str, str]:
        """
        Decide qué algoritmo usar basado en el contexto del estudiante.
        MEJORADO: Considera más factores como en tu código original.
        
        Args:
            total_cursos: Total de cursos en la malla
            cursos_aprobados: Cursos que ya aprobó
            cursos_pendientes: Cursos que le faltan
            num_prerequisitos: Número total de relaciones de prerequisitos
            ciclo_actual: Ciclo en el que debería estar
            malla_anio: Año de la malla curricular
            
        Returns:
            Tuple[str, str]: (algoritmo, razon)
                - algoritmo: "constraint_programming" o "backtracking"
                - razon: Explicación de por qué se eligió ese algoritmo
        """
        
        # Calcular métricas clave
        porcentaje_avance = (cursos_aprobados / total_cursos) * 100
        complejidad_prerequisitos = num_prerequisitos / total_cursos
        
        # Determinar si es alumno regular o irregular
        ciclos_completos = cursos_aprobados // 6  # Aproximación
        es_irregular = (ciclo_actual > ciclos_completos + 1)
        
        # Prompt mejorado para Gemini con más contexto
        prompt = f"""
Eres un experto en algoritmos de optimización y planificación académica universitaria. 
Debes decidir qué algoritmo usar para recomendar cursos a un estudiante.

CONTEXTO DEL ESTUDIANTE:
- Total de cursos en la malla: {total_cursos}
- Cursos aprobados: {cursos_aprobados}
- Cursos pendientes: {cursos_pendientes}
- Porcentaje de avance: {porcentaje_avance:.1f}%
- Ciclo actual esperado: {ciclo_actual}
- Ciclos completos (aprox): {ciclos_completos}
- Estado académico: {'IRREGULAR - Tiene cursos pendientes de ciclos anteriores' if es_irregular else 'REGULAR - Avanza normalmente'}
- Malla curricular: {malla_anio}
- Número de prerequisitos: {num_prerequisitos}
- Complejidad de prerequisitos: {complejidad_prerequisitos:.2f}

ALGORITMOS DISPONIBLES:

1. **Constraint Programming (CP)** - Usando OR-Tools CP-SAT
   - Ideal para: Problemas complejos con múltiples restricciones interdependientes
   - Ventajas: 
     * Encuentra soluciones óptimas considerando múltiples factores simultáneamente
     * Maneja restricciones de créditos mínimos y máximos por ciclo
     * Optimiza la selección de cursos para maximizar avance
     * Mejor para alumnos irregulares con situaciones complejas
   - Usa cuando:
     * Cursos pendientes > 15 (muchas opciones a evaluar)
     * Complejidad de prerequisitos > 0.3 (alta interdependencia)
     * Alumno irregular que necesita optimización compleja
     * Malla antigua (2015, 2019) con convalidaciones complejas
     * Porcentaje de avance < 60% (aún falta mucho)
   
2. **Backtracking por Ramas**
   - Ideal para: Búsquedas dirigidas por ciclos con lógica de avance secuencial
   - Ventajas: 
     * Muy rápido y eficiente
     * Sigue la lógica natural de avance por ciclos
     * Prioriza cursos pendientes obligatorios del ciclo actual
     * Permite adelantar cursos de ciclos siguientes si hay espacio
     * Mejor para alumnos regulares cerca de graduarse
   - Usa cuando:
     * Cursos pendientes < 15 (espacio de búsqueda pequeño)
     * Porcentaje de avance > 70% (cerca de graduarse)
     * Ciclo actual >= 7 (últimos ciclos)
     * Alumno regular con avance normal
     * Prerequisitos simples y lineales

CRITERIOS DE DECISIÓN (En orden de importancia):
1. Si es_irregular = True → FAVORECE CP (necesita optimización)
2. Si cursos_pendientes > 20 → CP (mucho por analizar)
3. Si porcentaje_avance > 75% → Backtracking (casi graduado, simple)
4. Si ciclo_actual >= 8 → Backtracking (últimos ciclos, directo)
5. Si complejidad_prerequisitos > 0.35 → CP (muchas dependencias)
6. Si malla antigua (2015, 2019) → CP (convalidaciones complejas)
7. Si cursos_pendientes < 12 → Backtracking (pocas opciones)

INSTRUCCIONES:
1. Analiza cuidadosamente el contexto del estudiante
2. Considera TODOS los criterios de decisión
3. Evalúa qué algoritmo se ajusta mejor a su situación específica
4. Responde SOLO con el formato JSON siguiente (sin markdown):

{{
  "algoritmo": "constraint_programming" o "backtracking",
  "razon": "Explicación técnica y detallada de 150-250 palabras justificando tu decisión basada en los criterios mencionados"
}}
"""
        
        try:
            # Llamar a Gemini
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Limpiar respuesta si viene con markdown
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            # Parsear respuesta
            import json
            result = json.loads(result_text)
            
            algoritmo = result.get("algoritmo", "backtracking")
            razon = result.get("razon", "No se proporcionó razón")
            
            # Validar algoritmo
            if algoritmo not in ["constraint_programming", "backtracking"]:
                algoritmo = "backtracking"
                razon = "Fallback por respuesta inválida del agente"
            
            return algoritmo, razon
            
        except Exception as e:
            # Fallback: Usar lógica mejorada si Gemini falla
            print(f"Error en Gemini: {e}")
            return self._fallback_decision(
                cursos_pendientes,
                complejidad_prerequisitos,
                porcentaje_avance,
                es_irregular,
                ciclo_actual,
                malla_anio
            )
    
    def _fallback_decision(
        self,
        cursos_pendientes: int,
        complejidad_prerequisitos: float,
        porcentaje_avance: float,
        es_irregular: bool,
        ciclo_actual: int,
        malla_anio: int
    ) -> Tuple[str, str]:
        """
        Lógica de fallback MEJORADA si Gemini no está disponible.
        Basada en tu experiencia con los algoritmos.
        """
        
        # Scoring system para decidir
        score_cp = 0
        score_backtracking = 0
        razones = []
        
        # Factor 1: Regularidad del alumno (MUY IMPORTANTE)
        if es_irregular:
            score_cp += 40
            razones.append("alumno irregular que requiere optimización compleja")
        else:
            score_backtracking += 30
            razones.append("alumno regular con avance normal")
        
        # Factor 2: Cantidad de cursos pendientes
        if cursos_pendientes > 20:
            score_cp += 30
            razones.append(f"{cursos_pendientes} cursos pendientes (muchas opciones)")
        elif cursos_pendientes < 12:
            score_backtracking += 25
            razones.append(f"{cursos_pendientes} cursos pendientes (espacio pequeño)")
        
        # Factor 3: Porcentaje de avance
        if porcentaje_avance > 75:
            score_backtracking += 35
            razones.append(f"avance del {porcentaje_avance:.1f}% (cerca de graduarse)")
        elif porcentaje_avance < 50:
            score_cp += 25
            razones.append(f"avance del {porcentaje_avance:.1f}% (aún falta mucho)")
        
        # Factor 4: Ciclo actual
        if ciclo_actual >= 8:
            score_backtracking += 20
            razones.append(f"ciclo {ciclo_actual} (últimos ciclos)")
        elif ciclo_actual <= 4:
            score_cp += 15
            razones.append(f"ciclo {ciclo_actual} (ciclos iniciales)")
        
        # Factor 5: Complejidad de prerequisitos
        if complejidad_prerequisitos > 0.35:
            score_cp += 25
            razones.append(f"complejidad {complejidad_prerequisitos:.2f} (alta interdependencia)")
        
        # Factor 6: Malla antigua
        if malla_anio in [2015, 2019]:
            score_cp += 20
            razones.append(f"malla {malla_anio} (puede tener convalidaciones complejas)")
        
        # Decisión final
        if score_cp > score_backtracking:
            return (
                "constraint_programming",
                f"Fallback: Se eligió Constraint Programming (score: {score_cp} vs {score_backtracking}) "
                f"considerando: {', '.join(razones)}. CP es más adecuado para optimizar tu situación "
                f"académica con múltiples restricciones y encontrar la mejor combinación de cursos."
            )
        else:
            return (
                "backtracking",
                f"Fallback: Se eligió Backtracking por Ramas (score: {score_backtracking} vs {score_cp}) "
                f"considerando: {', '.join(razones)}. Este algoritmo es eficiente para tu situación "
                f"siguiendo la lógica natural de avance por ciclos y priorizando cursos obligatorios."
            )


# Instancia global del agente
ai_agent = AIAgent()
