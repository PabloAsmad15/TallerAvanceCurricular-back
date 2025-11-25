# 🧪 Testing Suite - Reorganizado

## 📁 Nueva Estructura

```
backend/tests/
├── integration/          # 🎯 FLUJO COMPLETO EXITOSO (Happy Path)
│   └── test_happy_path_complete_flow.py
│
├── black_box/           # 🔲 TESTS DE CAJA NEGRA (4 Algoritmos)
│   └── test_algorithms_black_box.py
│
├── unit/                # 🧩 TESTS UNITARIOS (Endpoints específicos)
│   ├── test_auth_endpoints.py
│   ├── test_mallas_endpoints.py
│   ├── test_cursos_endpoints.py
│   └── test_recommendations_endpoints.py
│
└── concurrency/         # ⚡ TESTS DE CONCURRENCIA
    └── test_concurrent_operations.py
```

---

## 🎯 1. Tests de Integración (Happy Path)

**Archivo:** `tests/integration/test_happy_path_complete_flow.py`

### ¿Qué prueban?
El flujo COMPLETO y EXITOSO del usuario:

```
Registro → Login → Seleccionar Malla → Marcar Cursos → Solicitar Recomendación → Validar Resultado
```

### Tests incluidos:
- `test_complete_happy_path_flow()` - Flujo completo desde registro hasta recomendación
- `test_user_requests_multiple_recommendations()` - Usuario solicitando múltiples recomendaciones

### Características:
✅ Crea datos de prueba en BD (mallas, cursos, prerequisitos)
✅ Simula usuario real desde el inicio
✅ Valida cada paso del proceso
✅ Verifica que la recomendación sea correcta
✅ Comprueba que se guarde en historial

### Ejecutar:
```powershell
pytest tests/integration/ -v -s
```

---

## 🔲 2. Tests de Caja Negra (Black Box)

**Archivo:** `tests/black_box/test_algorithms_black_box.py`

### ¿Qué prueban?
Los **4 ALGORITMOS** SIN conocer su implementación interna:
- Constraint Programming (CP-SAT)
- Backtracking
- Prolog
- Association Rules

### Principio de Caja Negra:
```
❌ NO sabemos CÓMO funciona el algoritmo internamente
✅ SOLO validamos: ENTRADA → SALIDA
```

### Tests por Algoritmo:

#### **Constraint Programming** 📊
- `test_cp_respects_credit_limit()` - Respeta límite de créditos
- `test_cp_respects_prerequisites()` - Respeta prerequisitos
- `test_cp_prioritizes_lower_cycles()` - Prioriza ciclos inferiores

#### **Backtracking** 🔍
- `test_backtracking_finds_valid_solution()` - Encuentra solución válida
- `test_backtracking_respects_credit_limit()` - Respeta límite de créditos

#### **Prolog** 📖
- `test_prolog_handles_no_completed_courses()` - Maneja estudiantes nuevos
- `test_prolog_respects_credit_limit()` - Respeta límite de créditos

#### **Association Rules** 🎓
- `test_association_rules_with_history()` - Funciona con historial
- `test_association_rules_respects_credit_limit()` - Respeta límite de créditos

#### **AI Agent (Selector)** 🤖
- `test_ai_agent_selects_valid_algorithm()` - Selecciona algoritmo válido (1 de 4)
- `test_ai_agent_adapts_to_different_scenarios()` - Se adapta a diferentes escenarios

### Ejecutar:
```powershell
pytest tests/black_box/ -v -s
```

---

## 🧩 3. Tests Unitarios (Unit Tests)

**Archivos:** `tests/unit/*.py`

### ¿Qué prueban?
Endpoints ESPECÍFICOS y casos de uso individuales.

### Archivos:
- `test_auth_endpoints.py` - Autenticación (registro, login, tokens, reset password)
- `test_mallas_endpoints.py` - CRUD de mallas (crear, listar, filtrar, permisos)
- `test_cursos_endpoints.py` - CRUD de cursos (crear, listar, prerequisitos, validaciones)
- `test_recommendations_endpoints.py` - Recomendaciones (generación, historial, validaciones)

### Total: ~65 tests unitarios

### Ejecutar:
```powershell
pytest tests/unit/ -v
```

---

## ⚡ 4. Tests de Concurrencia

**Archivo:** `tests/concurrency/test_concurrent_operations.py`

### ¿Qué prueban?
Comportamiento del sistema bajo carga y requests simultáneas.

### Escenarios:
- 10 usuarios registrándose simultáneamente
- Race condition: mismo email múltiples veces
- 20 logins concurrentes del mismo usuario
- Generación simultánea de recomendaciones
- Modificaciones concurrentes de datos
- 50+ requests de lectura simultáneas

### Ejecutar:
```powershell
pytest tests/concurrency/ -v
```

---

## 🚀 Comandos Rápidos

```powershell
# Todos los tests
pytest

# Con salida detallada y prints
pytest -v -s

# Solo Happy Path (integración)
pytest tests/integration/ -v -s

# Solo Caja Negra (4 algoritmos)
pytest tests/black_box/ -v -s

# Solo Unitarios (endpoints)
pytest tests/unit/ -v

# Solo Concurrencia
pytest tests/concurrency/ -v

# Con cobertura
pytest --cov=app --cov-report=html

# Ver reporte HTML
start htmlcov/index.html
```

---

## 📊 Resumen de Tests

| Categoría | Archivos | Tests | Propósito |
|-----------|----------|-------|-----------|
| **Integración** | 1 | ~2 | Flujo completo exitoso del usuario |
| **Caja Negra** | 1 | ~11 | Validar 4 algoritmos sin conocer implementación |
| **Unitarios** | 4 | ~65 | Tests específicos de endpoints |
| **Concurrencia** | 1 | ~11 | Validar bajo carga y requests simultáneas |
| **TOTAL** | **7** | **~89** | **Suite completa de testing** |

---

## 💡 Diferencias Clave

### Integration (Happy Path) vs Black Box

**Integration (Happy Path):**
- ✅ Flujo COMPLETO del usuario (end-to-end)
- ✅ Desde registro hasta recomendación
- ✅ Valida integración entre componentes
- ✅ Enfocado en el "camino feliz"

**Black Box (4 Algoritmos):**
- ✅ Prueba CADA algoritmo individualmente
- ✅ NO conoce implementación interna
- ✅ Solo valida entrada → salida
- ✅ Valida comportamiento observable

### Ejemplo:

**Integration Test:**
```python
# Flujo completo
1. Usuario se registra
2. Usuario hace login
3. Usuario selecciona malla
4. Usuario marca cursos
5. Usuario pide recomendación
6. Sistema valida TODO el flujo
```

**Black Box Test:**
```python
# Solo el algoritmo
Input: malla_id=1, cursos_aprobados=[], max_creditos=22, algorithm="constraint_programming"
Output: cursos_recomendados=[...], total_creditos=20
Validación: total_creditos <= 22 ✅
```

---

## 🎯 Cuándo Usar Cada Tipo

### Usar Integration (Happy Path) cuando:
- Quieres probar el flujo completo del usuario
- Necesitas validar que todos los componentes funcionen juntos
- Estás probando un escenario real de uso

### Usar Black Box cuando:
- Quieres probar un algoritmo específico
- No te importa CÓMO funciona internamente
- Solo validas que la salida sea correcta
- Quieres tests independientes de la implementación

### Usar Unit Tests cuando:
- Quieres probar un endpoint específico
- Necesitas validar casos edge
- Pruebas de validación y permisos

### Usar Concurrency cuando:
- Necesitas validar performance
- Pruebas de carga
- Race conditions
- Comportamiento bajo estrés

---

## 📚 Documentación Completa

Para más detalles, consulta: `TESTING.md`
