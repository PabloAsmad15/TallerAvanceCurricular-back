"""
Servicio de recomendación con Prolog
Implementa el algoritmo basado en lógica declarativa
"""
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from pyswip import Prolog
    PROLOG_AVAILABLE = True
except ImportError:
    PROLOG_AVAILABLE = False
    print("⚠️ PySwip no disponible. El algoritmo de Prolog no funcionará.")


class PrologRecommendationService:
    """Servicio de recomendación basado en Prolog"""
    
    def __init__(self):
        self.prolog = None
        self.prolog_file = None
        
        if PROLOG_AVAILABLE:
            try:
                self.prolog = Prolog()
                # Ruta al archivo de reglas Prolog
                self.prolog_file = Path(__file__).parent / "logica_malla.pl"
                
                if not self.prolog_file.exists():
                    print(f"⚠️ Archivo Prolog no encontrado: {self.prolog_file}")
                else:
                    print(f"✓ Servicio Prolog inicializado correctamente")
            except Exception as e:
                print(f"⚠️ Error al inicializar Prolog: {e}")
                self.prolog = None
    
    def _limpiar_memoria(self):
        """Limpia la memoria de Prolog antes de una nueva consulta"""
        if not self.prolog:
            return
            
        try:
            self.prolog.retractall("curso(_,_,_,_,_)")
            self.prolog.retractall("aprobado(_)")
            self.prolog.retractall("creditos_maximos(_,_)")
        except Exception as e:
            print(f"⚠️ Error al limpiar memoria Prolog: {e}")
    
    def _cargar_reglas(self):
        """Carga el archivo de reglas Prolog"""
        if not self.prolog or not self.prolog_file:
            return False
            
        try:
            self.prolog.consult(str(self.prolog_file))
            return True
        except Exception as e:
            print(f"❌ Error al cargar reglas Prolog: {e}")
            return False
    
    def _insertar_cursos(self, malla: Dict[str, Dict]):
        """Inserta los cursos de la malla en Prolog"""
        if not self.prolog:
            return
            
        for codigo, info in malla.items():
            try:
                nombre_limpio = info['nombre'].replace("'", "''")
                prereqs_lower = [p.lower() for p in info.get('prerrequisitos', [])]
                prereqs_str = str(prereqs_lower).replace('"', "'")
                
                fact = f"curso('{codigo.lower()}', '{nombre_limpio}', {info['ciclo']}, {info['creditos']}, {prereqs_str})"
                self.prolog.assertz(fact)
            except Exception as e:
                print(f"⚠️ Error al insertar curso {codigo}: {e}")
    
    def _insertar_cursos_aprobados(self, cursos_aprobados: List[str]):
        """Inserta los cursos aprobados en Prolog"""
        if not self.prolog:
            return
            
        for codigo in cursos_aprobados:
            try:
                self.prolog.assertz(f"aprobado('{codigo.lower()}')")
            except Exception as e:
                print(f"⚠️ Error al insertar curso aprobado {codigo}: {e}")
    
    def _insertar_creditos_maximos(self):
        """Inserta los límites de créditos por ciclo"""
        if not self.prolog:
            return
            
        creditos_por_ciclo = {
            1: 20, 2: 21, 3: 22, 4: 20, 5: 21,
            6: 21, 7: 21, 8: 20, 9: 22, 10: 17
        }
        
        for ciclo, creditos in creditos_por_ciclo.items():
            try:
                self.prolog.assertz(f"creditos_maximos({ciclo}, {creditos})")
            except Exception as e:
                print(f"⚠️ Error al insertar créditos máximos: {e}")
    
    def _consultar_prolog(self, query: str) -> List[Dict]:
        """Ejecuta una consulta en Prolog y retorna los resultados"""
        if not self.prolog:
            return []
            
        try:
            return list(self.prolog.query(query))
        except Exception as e:
            print(f"❌ Error en consulta Prolog '{query}': {e}")
            return []
    
    def recomendar(
        self, 
        malla: Dict[str, Dict],
        cursos_aprobados: List[str],
        creditos_por_ciclo: Optional[Dict[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Genera recomendaciones usando Prolog
        
        Args:
            malla: Diccionario con información de todos los cursos
            cursos_aprobados: Lista de códigos de cursos aprobados
            creditos_por_ciclo: Límites de créditos por ciclo (opcional)
        
        Returns:
            Diccionario con la recomendación y diagnóstico
        """
        if not self.prolog or not PROLOG_AVAILABLE:
            return {
                "error": "Servicio Prolog no disponible",
                "algoritmo": "prolog",
                "disponible": False
            }
        
        try:
            # 1. Preparar Prolog
            self._limpiar_memoria()
            if not self._cargar_reglas():
                return {
                    "error": "No se pudieron cargar las reglas Prolog",
                    "algoritmo": "prolog"
                }
            
            # 2. Insertar hechos
            self._insertar_cursos(malla)
            self._insertar_cursos_aprobados(cursos_aprobados)
            self._insertar_creditos_maximos()
            
            # 3. Obtener diagnóstico
            ultimo_ciclo_query = self._consultar_prolog("encontrar_ultimo_ciclo_completo(U)")
            ultimo_ciclo_completo = ultimo_ciclo_query[0]['U'] if ultimo_ciclo_query else 0
            
            # 4. Verificar si completó la carrera
            if ultimo_ciclo_completo >= 10:
                return {
                    "algoritmo": "prolog",
                    "completado": True,
                    "mensaje": "¡FELICITACIONES! Has completado todos los ciclos de la carrera.",
                    "ultimo_ciclo_completo": ultimo_ciclo_completo
                }
            
            ciclo_matricula = ultimo_ciclo_completo + 1
            
            # 5. Obtener estado académico
            estado_query = self._consultar_prolog("estado_academico(Estado)")
            estado = estado_query[0]['Estado'] if estado_query else 'irregular'
            
            # 6. Obtener cursos pendientes en el ciclo
            pendientes_query = self._consultar_prolog(
                f"cursos_pendientes_en_ciclo({ciclo_matricula}, P)"
            )
            cursos_pendientes = pendientes_query[0]['P'] if pendientes_query else []
            cursos_pendientes_upper = [c.upper() for c in cursos_pendientes]
            
            # 7. Obtener recomendación
            rec_query = self._consultar_prolog("recomendar_cursos(Recomendacion)")
            
            if not rec_query:
                return {
                    "algoritmo": "prolog",
                    "error": "No se pudo generar recomendación",
                    "ultimo_ciclo_completo": ultimo_ciclo_completo,
                    "ciclo_matricula": ciclo_matricula
                }
            
            recomendacion_lower = rec_query[0]['Recomendacion']
            recomendacion = [c.upper() for c in recomendacion_lower]
            
            # 8. Calcular créditos
            creditos_totales = sum(
                malla[codigo]['creditos'] 
                for codigo in recomendacion 
                if codigo in malla
            )
            
            creditos_maximos = {
                1: 20, 2: 21, 3: 22, 4: 20, 5: 21,
                6: 21, 7: 21, 8: 20, 9: 22, 10: 17
            }.get(ciclo_matricula, 21)
            
            # 9. Clasificar cursos
            cursos_detallados = []
            for codigo in recomendacion:
                if codigo in malla:
                    info = malla[codigo]
                    tipo = "Obligatorio" if codigo in cursos_pendientes_upper else "Avance"
                    cursos_detallados.append({
                        "codigo": codigo,
                        "nombre": info['nombre'],
                        "ciclo": info['ciclo'],
                        "creditos": info['creditos'],
                        "tipo": tipo,
                        "prerrequisitos": info.get('prerrequisitos', [])
                    })
            
            # 10. Obtener análisis adicional
            porcentaje_query = self._consultar_prolog("porcentaje_avance(P)")
            porcentaje_avance = porcentaje_query[0]['P'] if porcentaje_query else 0
            
            ciclos_restantes_query = self._consultar_prolog("ciclos_para_graduarse(C)")
            ciclos_restantes = ciclos_restantes_query[0]['C'] if ciclos_restantes_query else 0
            
            return {
                "algoritmo": "prolog",
                "disponible": True,
                "diagnostico": {
                    "ultimo_ciclo_completo": ultimo_ciclo_completo,
                    "ciclo_matricula": ciclo_matricula,
                    "estado": estado,
                    "cursos_pendientes": cursos_pendientes_upper,
                    "porcentaje_avance": porcentaje_avance,
                    "ciclos_restantes": ciclos_restantes
                },
                "recomendacion": {
                    "cursos": cursos_detallados,
                    "creditos_totales": creditos_totales,
                    "creditos_maximos": creditos_maximos,
                    "total_cursos": len(cursos_detallados)
                },
                "completado": False
            }
            
        except Exception as e:
            print(f"❌ Error en recomendación Prolog: {e}")
            import traceback
            traceback.print_exc()
            return {
                "algoritmo": "prolog",
                "error": str(e),
                "disponible": False
            }
