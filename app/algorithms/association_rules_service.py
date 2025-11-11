"""
Servicio de recomendación con Reglas de Asociación
Implementa el algoritmo basado en aprendizaje de patrones históricos
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from collections import defaultdict

try:
    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori, association_rules
    MLXTEND_AVAILABLE = True
except ImportError:
    MLXTEND_AVAILABLE = False
    print("⚠️ mlxtend no disponible. El algoritmo de reglas de asociación no funcionará.")


class AssociationRulesService:
    """Servicio de recomendación basado en Reglas de Asociación"""
    
    def __init__(self):
        self.rules = pd.DataFrame()
        self.trained = False
        print(f"✓ Servicio de Reglas de Asociación inicializado (mlxtend: {MLXTEND_AVAILABLE})")
    
    def generar_datos_historicos(
        self, 
        todas_las_mallas: Dict[int, tuple],
        mapa_conval: Dict[int, Dict[str, str]]
    ) -> List[List[str]]:
        """
        Genera datos históricos sintéticos basados en patrones reales
        
        Args:
            todas_las_mallas: Diccionario con todas las mallas curriculares
            mapa_conval: Mapa de convalidaciones entre mallas
        
        Returns:
            Lista de patrones históricos (listas de cursos aprobados)
        """
        try:
            print("\n🔄 Generando datos históricos sintéticos...")
            patrones_historicos = set()
            
            for año_malla, (malla, _) in todas_las_mallas.items():
                if not malla:
                    continue
                
                print(f"Procesando malla {año_malla}:")
                
                # Agrupar cursos por ciclo
                cursos_por_ciclo = defaultdict(list)
                for codigo, info in malla.items():
                    cursos_por_ciclo[info['ciclo']].append(codigo)
                
                # Verificar que hay cursos válidos
                ciclos_validos = [c for c in range(1, 11) if cursos_por_ciclo[c]]
                if not ciclos_validos:
                    print(f"⚠️ No se encontraron cursos válidos en la malla {año_malla}")
                    continue
                
                # Generar patrones de estudiantes
                num_estudiantes = 10
                print(f"  - Generando {num_estudiantes} patrones de estudiantes")
                
                for estudiante in range(num_estudiantes):
                    cursos_aprobados = set()
                    
                    # Simular aprobación progresiva hasta ciclo 5
                    for ciclo_actual in range(1, 6):
                        if cursos_por_ciclo[ciclo_actual]:
                            # Tasa de aprobación variable
                            tasa_aprobacion = np.random.uniform(0.7, 1.0)
                            cursos_ciclo = cursos_por_ciclo[ciclo_actual]
                            num_aprobados = max(1, int(len(cursos_ciclo) * tasa_aprobacion))
                            aprobados = list(np.random.choice(
                                cursos_ciclo, 
                                num_aprobados, 
                                replace=False
                            ))
                            
                            # Convertir a códigos de malla 2025
                            if año_malla != 2025 and mapa_conval.get(año_malla):
                                aprobados = [
                                    mapa_conval[año_malla].get(c, c) 
                                    for c in aprobados
                                ]
                                aprobados = [c for c in aprobados if c is not None]
                            
                            cursos_aprobados.update(aprobados)
                            
                            # Generar subpatrones
                            if len(cursos_aprobados) >= 3:
                                cursos_lista = list(cursos_aprobados)
                                for _ in range(3):
                                    tamaño_patron = min(5, len(cursos_lista))
                                    subpatron = tuple(sorted(np.random.choice(
                                        cursos_lista, 
                                        tamaño_patron, 
                                        replace=False
                                    )))
                                    patrones_historicos.add(subpatron)
                
                print(f"  ✓ Patrones generados para malla {año_malla}")
            
            # Convertir a lista
            patrones_finales = [list(p) for p in patrones_historicos]
            
            if not patrones_finales:
                print("❌ No se pudieron generar patrones históricos")
                return []
            
            print(f"\n✓ Total de patrones históricos generados: {len(patrones_finales)}")
            print(f"  - Promedio de cursos por patrón: {sum(len(p) for p in patrones_finales) / len(patrones_finales):.1f}")
            
            return patrones_finales
            
        except Exception as e:
            print(f"❌ Error al generar datos históricos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def entrenar(self, historial_alumnos: List[List[str]]) -> bool:
        """
        Entrena el modelo con datos históricos
        
        Args:
            historial_alumnos: Lista de patrones históricos
        
        Returns:
            True si el entrenamiento fue exitoso
        """
        if not MLXTEND_AVAILABLE:
            print("⚠️ mlxtend no disponible")
            return False
        
        try:
            print("\n🔄 Iniciando fase de aprendizaje...")
            
            if not historial_alumnos or len(historial_alumnos) < 2:
                print("❌ No hay suficientes datos históricos")
                return False
            
            # Procesar patrones
            historial_procesado = []
            total_cursos = set()
            
            for patron in historial_alumnos:
                total_cursos.update(patron)
            
            print(f"  - Total de cursos únicos: {len(total_cursos)}")
            
            # Generar subpatrones
            for patron in historial_alumnos:
                if len(patron) <= 5:
                    historial_procesado.append(patron)
                else:
                    for i in range(len(patron) - 2):
                        for j in range(i + 2, min(i + 5, len(patron))):
                            subpatron = patron[i:j+1]
                            if len(subpatron) >= 2:
                                historial_procesado.append(subpatron)
            
            print(f"  - Patrones procesados: {len(historial_procesado)}")
            
            # Codificar transacciones
            te = TransactionEncoder()
            te_ary = te.fit(historial_procesado).transform(historial_procesado)
            df = pd.DataFrame(te_ary, columns=te.columns_)
            
            print("✓ Datos históricos procesados")
            
            # Buscar conjuntos frecuentes con diferentes soportes
            soportes = [0.1, 0.05, 0.03, 0.01]
            frequent_itemsets = pd.DataFrame()
            
            for min_support in soportes:
                print(f"\nProbando con soporte mínimo: {min_support}")
                frequent_itemsets = apriori(
                    df, 
                    min_support=min_support, 
                    use_colnames=True, 
                    max_len=4,
                    verbose=0
                )
                
                if not frequent_itemsets.empty and len(frequent_itemsets) >= 10:
                    print(f"✓ Encontrados {len(frequent_itemsets)} conjuntos frecuentes")
                    break
                else:
                    print("⚠️ Insuficientes conjuntos, ajustando...")
            
            if frequent_itemsets.empty:
                print("⚠️ No se encontraron conjuntos frecuentes")
                return False
            
            # Generar reglas
            print("\nGenerando reglas de asociación...")
            rules = association_rules(
                frequent_itemsets, 
                metric="lift",
                min_threshold=1.0
            )
            
            if rules.empty:
                print("⚠️ No se generaron reglas")
                return False
            
            # Filtrar reglas
            rules = rules[
                (rules['confidence'] > 0.3) &
                (rules['lift'] > 1.1) &
                (rules['conviction'] > 1.0)
            ]
            
            if rules.empty:
                print("⚠️ No hay reglas después del filtrado")
                return False
            
            # Ordenar y limitar
            rules = rules.sort_values(['lift', 'confidence'], ascending=[False, False])
            if len(rules) > 200:
                rules = rules.head(200)
            
            self.rules = rules
            self.trained = True
            
            print(f"✓ Entrenamiento completado: {len(rules)} reglas generadas")
            print(f"  - Confianza promedio: {rules['confidence'].mean():.2f}")
            print(f"  - Lift promedio: {rules['lift'].mean():.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en entrenamiento: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def calcular_prioridad(
        self, 
        curso: str, 
        malla: Dict[str, Dict],
        cursos_aprobados: set
    ) -> float:
        """Calcula la prioridad de un curso"""
        if curso not in malla:
            return 0.0
        
        score = 0.0
        info_curso = malla[curso]
        
        # Factor 1: Ciclo (priorizar ciclos bajos)
        ciclo_factor = 1.0 / info_curso['ciclo']
        score += ciclo_factor * 2
        
        # Factor 2: Es prerrequisito de otros
        es_prereq_de = sum(
            1 for _, c in malla.items() 
            if curso in c.get('prerrequisitos', [])
        )
        score += es_prereq_de * 0.5
        
        # Factor 3: Reglas de asociación
        if self.trained and not self.rules.empty:
            for _, rule in self.rules.iterrows():
                antecedentes = set(rule['antecedents'])
                consecuentes = set(rule['consequents'])
                
                if antecedentes.issubset(cursos_aprobados) and curso in consecuentes:
                    score += rule['lift'] * 2
        
        return score
    
    def recomendar(
        self,
        malla: Dict[str, Dict],
        cursos_aprobados: List[str],
        malla_por_ciclo: Dict[int, List[Dict]],
        creditos_por_ciclo: Optional[Dict[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Genera recomendaciones usando reglas de asociación
        
        Args:
            malla: Diccionario con información de todos los cursos
            cursos_aprobados: Lista de códigos de cursos aprobados
            malla_por_ciclo: Cursos organizados por ciclo
            creditos_por_ciclo: Límites de créditos por ciclo
        
        Returns:
            Diccionario con la recomendación y diagnóstico
        """
        if not MLXTEND_AVAILABLE:
            return {
                "error": "mlxtend no disponible",
                "algoritmo": "association_rules",
                "disponible": False
            }
        
        try:
            cursos_aprobados_set = set(cursos_aprobados)
            
            if creditos_por_ciclo is None:
                creditos_por_ciclo = {
                    1: 20, 2: 21, 3: 22, 4: 20, 5: 21,
                    6: 21, 7: 21, 8: 20, 9: 22, 10: 17
                }
            
            # 1. Diagnóstico
            ultimo_ciclo_completo = 0
            for ciclo in range(1, 11):
                cursos_ciclo = {c['codigo'] for c in malla_por_ciclo[ciclo]}
                if not cursos_ciclo or not cursos_ciclo.issubset(cursos_aprobados_set):
                    break
                ultimo_ciclo_completo = ciclo
            
            if ultimo_ciclo_completo >= 10:
                return {
                    "algoritmo": "association_rules",
                    "completado": True,
                    "mensaje": "¡FELICITACIONES! Has completado todos los ciclos.",
                    "ultimo_ciclo_completo": ultimo_ciclo_completo
                }
            
            ciclo_matricula = ultimo_ciclo_completo + 1
            max_creditos = creditos_por_ciclo[ciclo_matricula]
            
            # 2. Cursos disponibles
            cursos_disponibles = {}
            for codigo, info in malla.items():
                if codigo not in cursos_aprobados_set:
                    prereqs = info.get('prerrequisitos', [])
                    if all(p in cursos_aprobados_set for p in prereqs):
                        cursos_disponibles[codigo] = info
            
            # 3. Clasificar cursos
            cursos_pendientes = {
                c['codigo']: c 
                for c in malla_por_ciclo[ciclo_matricula]
                if c['codigo'] not in cursos_aprobados_set
            }
            
            cursos_avance = {
                cod: info 
                for cod, info in cursos_disponibles.items()
                if cod not in cursos_pendientes
            }
            
            # 4. Generar recomendación
            recomendacion = []
            creditos_actuales = 0
            
            # Primero pendientes
            for codigo in sorted(cursos_pendientes.keys()):
                creditos_curso = cursos_pendientes[codigo]['creditos']
                if creditos_actuales + creditos_curso <= max_creditos:
                    recomendacion.append(codigo)
                    creditos_actuales += creditos_curso
            
            # Luego avance priorizados
            cursos_avance_priorizados = sorted(
                cursos_avance.keys(),
                key=lambda c: self.calcular_prioridad(c, malla, cursos_aprobados_set),
                reverse=True
            )
            
            for codigo in cursos_avance_priorizados:
                creditos_curso = cursos_avance[codigo]['creditos']
                if creditos_actuales + creditos_curso <= max_creditos:
                    recomendacion.append(codigo)
                    creditos_actuales += creditos_curso
            
            # 5. Detallar cursos
            cursos_detallados = []
            for codigo in recomendacion:
                if codigo in malla:
                    info = malla[codigo]
                    tipo = "Obligatorio" if codigo in cursos_pendientes else "Avance"
                    cursos_detallados.append({
                        "codigo": codigo,
                        "nombre": info['nombre'],
                        "ciclo": info['ciclo'],
                        "creditos": info['creditos'],
                        "tipo": tipo,
                        "prerrequisitos": info.get('prerrequisitos', []),
                        "prioridad": self.calcular_prioridad(codigo, malla, cursos_aprobados_set)
                    })
            
            # 6. Estado
            estado = "regular" if not cursos_pendientes else "irregular"
            
            # 7. Estadísticas de reglas
            reglas_stats = {}
            if self.trained and not self.rules.empty:
                reglas_stats = {
                    "total_reglas": len(self.rules),
                    "confianza_promedio": float(self.rules['confidence'].mean()),
                    "lift_promedio": float(self.rules['lift'].mean()),
                    "soporte_promedio": float(self.rules['support'].mean())
                }
            
            return {
                "algoritmo": "association_rules",
                "disponible": True,
                "entrenado": self.trained,
                "diagnostico": {
                    "ultimo_ciclo_completo": ultimo_ciclo_completo,
                    "ciclo_matricula": ciclo_matricula,
                    "estado": estado,
                    "cursos_pendientes": list(cursos_pendientes.keys())
                },
                "recomendacion": {
                    "cursos": cursos_detallados,
                    "creditos_totales": creditos_actuales,
                    "creditos_maximos": max_creditos,
                    "total_cursos": len(cursos_detallados)
                },
                "reglas_asociacion": reglas_stats,
                "completado": False
            }
            
        except Exception as e:
            print(f"❌ Error en recomendación con reglas de asociación: {e}")
            import traceback
            traceback.print_exc()
            return {
                "algoritmo": "association_rules",
                "error": str(e),
                "disponible": False
            }
