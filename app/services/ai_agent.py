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
    - Prolog: Para validación estricta de reglas académicas con lógica declarativa
    - Association Rules: Para aprendizaje de patrones históricos de éxito
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
                - algoritmo: "constraint_programming", "backtracking", "prolog", o "association_rules"
                - razon: Explicación de por qué se eligió ese algoritmo
        """
        
        # Calcular métricas clave
        porcentaje_avance = (cursos_aprobados / total_cursos) * 100
        complejidad_prerequisitos = num_prerequisitos / total_cursos
        
        # Determinar si es alumno regular o irregular
        ciclos_completos = cursos_aprobados // 6  # Aproximación
        es_irregular = (ciclo_actual > ciclos_completos + 1)
        
        # Prompt mejorado para Gemini con más contexto - AHORA CON 4 ALGORITMOS
        prompt = f"""
Eres un experto en algoritmos de optimización, inteligencia artificial y planificación académica universitaria. 
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

ALGORITMOS DISPONIBLES (4 opciones):

1. **Constraint Programming (CP)** - OR-Tools CP-SAT
   - Tipo: Optimización con restricciones
   - Ideal para: Problemas complejos con múltiples restricciones interdependientes
   - Ventajas: 
     * Encuentra soluciones óptimas globales
     * Maneja restricciones de créditos, prerequisitos, ciclos
     * Optimiza para maximizar avance académico
     * Excelente para situaciones irregulares complejas
   - Usa cuando:
     * Cursos pendientes > 15 (espacio grande)
     * Complejidad prerequisitos > 0.3 (alta interdependencia)
     * Alumno irregular con muchas opciones
     * Necesitas LA MEJOR combinación posible
     * Porcentaje de avance < 60%

2. **Backtracking por Ramas**
   - Tipo: Búsqueda por exploración de árbol
   - Ideal para: Búsquedas dirigidas por ciclos con lógica secuencial
   - Ventajas: 
     * MUY rápido y eficiente
     * Sigue lógica natural de avance por ciclos
     * Prioriza cursos obligatorios del ciclo actual
     * Simple y directo
   - Usa cuando:
     * Cursos pendientes < 15 (espacio pequeño)
     * Porcentaje avance > 70% (cerca de graduarse)
     * Ciclo >= 7 (últimos ciclos)
     * Alumno regular con avance normal
     * Prerequisitos simples y lineales

3. **Prolog** - Lógica Declarativa
   - Tipo: Motor de inferencia lógica
   - Ideal para: Validación estricta de reglas académicas
   - Ventajas:
     * Garantiza cumplimiento exacto de todas las reglas
     * Identifica automáticamente último ciclo completo
     * Diagnóstico académico detallado (estado regular/irregular)
     * Razonamiento lógico sobre prerequisitos
     * No requiere entrenamiento
   - Usa cuando:
     * Necesitas GARANTÍA de cumplimiento de reglas
     * Situación académica compleja que requiere análisis lógico
     * Quieres diagnóstico detallado del estado académico
     * Prerequisitos complejos con dependencias cruzadas
     * Primera recomendación (sin historial previo)

4. **Association Rules (Reglas de Asociación)** - Machine Learning
   - Tipo: Aprendizaje de patrones históricos
   - Ideal para: Descubrir relaciones no obvias entre cursos
   - Ventajas:
     * Aprende de patrones de éxito de miles de estudiantes
     * Descubre qué cursos suelen aprobarse juntos
     * Recomendaciones basadas en casos similares exitosos
     * Usa métricas de confianza, soporte y lift
     * Personalizado según tu historial
   - Usa cuando:
     * Tienes historial académico (cursos_aprobados > 10)
     * Quieres recomendación basada en patrones de éxito
     * Situación académica tiene casos similares históricos
     * Deseas descubrir combinaciones exitosas no obvias
     * Porcentaje avance 30-80% (rango medio)

CRITERIOS DE DECISIÓN MEJORADOS:

**Alta Prioridad:**
1. Si cursos_aprobados < 6 → PROLOG (poco historial, necesita reglas)
2. Si es_irregular Y cursos_pendientes > 20 → CP (optimización compleja)
3. Si porcentaje_avance > 80% → BACKTRACKING (casi graduado, directo)
4. Si 15 < cursos_aprobados < 40 Y porcentaje_avance 30-70% → ASSOCIATION_RULES (rango ideal para ML)

**Media Prioridad:**
5. Si complejidad_prerequisitos > 0.4 → PROLOG (muchas dependencias lógicas)
6. Si ciclo_actual >= 8 Y es_regular → BACKTRACKING (últimos ciclos, simple)
7. Si malla antigua (2015, 2019) → CP o PROLOG (convalidaciones)
8. Si cursos_aprobados > 30 → ASSOCIATION_RULES (mucho historial para aprender)

**Baja Prioridad:**
9. Si cursos_pendientes < 10 → BACKTRACKING (pocas opciones)
10. Si necesita diagnóstico detallado → PROLOG (mejor análisis)

MATRIZ DE DECISIÓN RÁPIDA:
- Poco avance (0-25%) + Irregular → CP
- Poco avance (0-25%) + Regular → PROLOG
- Avance medio (25-70%) + Muchos aprobados → ASSOCIATION_RULES
- Avance medio (25-70%) + Pocos aprobados → PROLOG
- Alto avance (70-100%) + Regular → BACKTRACKING
- Alto avance (70-100%) + Irregular → CP

INSTRUCCIONES:
1. Analiza el contexto del estudiante
2. Aplica la matriz de decisión y los criterios
3. Elige EL MEJOR algoritmo para esta situación específica
4. Responde SOLO con JSON (sin markdown):

{{
  "algoritmo": "constraint_programming" | "backtracking" | "prolog" | "association_rules",
  "razon": "Explicación de 150-250 palabras justificando tu decisión"
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
            
            # Validar algoritmo (ahora 4 opciones)
            if algoritmo not in ["constraint_programming", "backtracking", "prolog", "association_rules"]:
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
                malla_anio,
                cursos_aprobados
            )
    
    def _fallback_decision(
        self,
        cursos_pendientes: int,
        complejidad_prerequisitos: float,
        porcentaje_avance: float,
        es_irregular: bool,
        ciclo_actual: int,
        malla_anio: int,
        cursos_aprobados: int = 0
    ) -> Tuple[str, str]:
        """
        Lógica de fallback MEJORADA si Gemini no está disponible.
        Ahora con 4 algoritmos disponibles.
        """
        
        # Scoring system para decidir entre 4 algoritmos
        score_cp = 0
        score_backtracking = 0
        score_prolog = 0
        score_association = 0
        razones = []
        
        # FACTOR 1: Poco historial → PROLOG (necesita reglas claras)
        if cursos_aprobados < 6:
            score_prolog += 50
            razones.append("pocos cursos aprobados, necesita análisis lógico de reglas")
        
        # FACTOR 2: Rango ideal para ML → ASSOCIATION RULES
        if 15 <= cursos_aprobados <= 40 and 30 <= porcentaje_avance <= 70:
            score_association += 45
            razones.append(f"{cursos_aprobados} cursos aprobados en rango ideal para aprendizaje de patrones")
        
        # FACTOR 3: Regularidad del alumno
        if es_irregular:
            if cursos_pendientes > 20:
                score_cp += 40
                razones.append("alumno irregular con muchas opciones (requiere optimización)")
            else:
                score_prolog += 30
                razones.append("alumno irregular (necesita validación de reglas)")
        else:
            if porcentaje_avance > 70:
                score_backtracking += 35
                razones.append("alumno regular cerca de graduarse")
            else:
                score_association += 25
                razones.append("alumno regular con historial para aprender patrones")
        
        # FACTOR 4: Cantidad de cursos pendientes
        if cursos_pendientes > 20:
            score_cp += 30
            razones.append(f"{cursos_pendientes} cursos pendientes (espacio grande)")
        elif cursos_pendientes < 10:
            score_backtracking += 25
            razones.append(f"{cursos_pendientes} cursos pendientes (búsqueda simple)")
        
        # FACTOR 5: Porcentaje de avance
        if porcentaje_avance > 80:
            score_backtracking += 40
            razones.append(f"avance {porcentaje_avance:.1f}% (casi graduado)")
        elif porcentaje_avance < 25:
            if cursos_aprobados > 8:
                score_cp += 25
            else:
                score_prolog += 30
            razones.append(f"avance {porcentaje_avance:.1f}% (ciclos iniciales)")
        elif 30 <= porcentaje_avance <= 70:
            score_association += 30
            razones.append(f"avance {porcentaje_avance:.1f}% (rango medio ideal para ML)")
        
        # FACTOR 6: Ciclo actual
        if ciclo_actual >= 8:
            score_backtracking += 25
            razones.append(f"ciclo {ciclo_actual} (últimos ciclos, directo)")
        elif ciclo_actual <= 3:
            score_prolog += 20
            razones.append(f"ciclo {ciclo_actual} (ciclos iniciales, reglas)")
        
        # FACTOR 7: Complejidad de prerequisitos
        if complejidad_prerequisitos > 0.4:
            score_prolog += 30
            razones.append(f"complejidad {complejidad_prerequisitos:.2f} (alta dependencia lógica)")
        elif complejidad_prerequisitos > 0.3:
            score_cp += 20
        
        # FACTOR 8: Malla antigua
        if malla_anio in [2015, 2019]:
            score_cp += 15
            score_prolog += 15
            razones.append(f"malla {malla_anio} (puede tener convalidaciones)")
        
        # FACTOR 9: Mucho historial académico
        if cursos_aprobados > 30:
            score_association += 35
            razones.append(f"{cursos_aprobados} cursos aprobados (mucho historial para ML)")
        
        # Determinar ganador
        scores = {
            "constraint_programming": score_cp,
            "backtracking": score_backtracking,
            "prolog": score_prolog,
            "association_rules": score_association
        }
        
        algoritmo_elegido = max(scores, key=scores.get)
        score_elegido = scores[algoritmo_elegido]
        
        # Mensajes personalizados por algoritmo
        mensajes = {
            "constraint_programming": (
                f"Fallback: Constraint Programming (score: {score_elegido}) es óptimo para tu situación. "
                f"Considerando: {', '.join(razones)}. CP encuentra la MEJOR combinación de cursos "
                f"optimizando múltiples restricciones simultáneamente."
            ),
            "backtracking": (
                f"Fallback: Backtracking (score: {score_elegido}) es ideal para ti. "
                f"Considerando: {', '.join(razones)}. Este algoritmo es rápido y eficiente, "
                f"siguiendo la lógica natural de avance por ciclos."
            ),
            "prolog": (
                f"Fallback: Prolog (score: {score_elegido}) es el más adecuado. "
                f"Considerando: {', '.join(razones)}. Usa lógica declarativa para GARANTIZAR "
                f"el cumplimiento exacto de todas las reglas académicas y prerequisitos."
            ),
            "association_rules": (
                f"Fallback: Association Rules (score: {score_elegido}) es perfecto para tu caso. "
                f"Considerando: {', '.join(razones)}. Aprende de patrones históricos de éxito "
                f"para recomendarte cursos basándose en casos similares exitosos."
            )
        }
        
        return (algoritmo_elegido, mensajes[algoritmo_elegido])


# Instancia global del agente
ai_agent = AIAgent()
