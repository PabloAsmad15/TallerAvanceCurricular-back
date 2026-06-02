# 🧪 Guía de Testing - Taller Avance Curricular Backend

Esta guía documenta la suite completa de pruebas para el backend de Taller Avance Curricular.

## 📋 Tabla de Contenidos

- [Estructura de Tests](#estructura-de-tests)
- [Configuración](#configuración)
- [Ejecución de Tests](#ejecución-de-tests)
- [Tipos de Tests](#tipos-de-tests)
- [Cobertura de Código](#cobertura-de-código)
- [Buenas Prácticas](#buenas-prácticas)

## 🗂️ Estructura de Tests

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                          # Fixtures y configuración compartida
│   │
│   ├── integration/                         # 🎯 TESTS DE INTEGRACIÓN
│   │   ├── __init__.py
│   │   └── test_happy_path_complete_flow.py # Flujo completo exitoso del usuario
│   │
│   ├── black_box/                           # 🔲 TESTS DE CAJA NEGRA
│   │   ├── __init__.py
│   │   └── test_algorithms_black_box.py     # Tests de los 4 algoritmos sin conocer implementación
│   │
│   ├── unit/                                # 🧩 TESTS UNITARIOS
│   │   ├── __init__.py
│   │   ├── test_auth_endpoints.py           # Tests específicos de autenticación
│   │   ├── test_mallas_endpoints.py         # Tests específicos de mallas
│   │   ├── test_cursos_endpoints.py         # Tests específicos de cursos
│   │   └── test_recommendations_endpoints.py # Tests específicos de recomendaciones
│   │
│   └── concurrency/                         # ⚡ TESTS DE CONCURRENCIA
│       ├── __init__.py
│       └── test_concurrent_operations.py    # Tests de carga y concurrencia
```

## ⚙️ Configuración

### Instalación de Dependencias

```powershell
cd backend
pip install -r requirements.txt
```

Las dependencias de testing incluidas son:
- `pytest`: Framework de testing
- `pytest-asyncio`: Soporte para tests asíncronos
- `pytest-cov`: Reportes de cobertura de código
- `httpx`: Cliente HTTP para tests asíncronos
- `faker`: Generación de datos de prueba

### Configuración de Base de Datos de Prueba

Los tests utilizan una base de datos SQLite en memoria (`test.db`) que se crea y destruye automáticamente para cada test. No es necesario configurar una base de datos separada.

## 🚀 Ejecución de Tests

### Ejecutar Todos los Tests

```powershell
pytest
```

### Ejecutar Tests con Salida Detallada

```powershell
pytest -v
```

### Ejecutar Tests por Categoría

**Solo tests de integración:**
```powershell
pytest tests/integration/
```

**Solo tests de concurrencia:**
```powershell
pytest tests/concurrency/
```

**Un archivo específico:**
```powershell
pytest tests/integration/test_auth_endpoints.py
```

**Una clase específica:**
```powershell
pytest tests/integration/test_auth_endpoints.py::TestAuthenticationFlow
```

**Un test específico:**
```powershell
pytest tests/integration/test_auth_endpoints.py::TestAuthenticationFlow::test_user_registration_success
```

### Ejecutar Tests en Paralelo (más rápido)

```powershell
pip install pytest-xdist
pytest -n auto
```

### Ejecutar con Salida en Tiempo Real

```powershell
pytest -s
```

## 📊 Tipos de Tests

### 1. **Tests de Integración (Black Box)**

**Ubicación:** `tests/integration/`

**Propósito:** Validar endpoints completos de la API sin conocer la implementación interna.

**Características:**
- Prueban el flujo completo de requests HTTP
- Validan respuestas, códigos de estado y formato de datos
- No acceden directamente a la lógica interna
- Simulan el comportamiento de clientes reales

**Áreas cubiertas:**
- ✅ Autenticación (registro, login, tokens)
- ✅ CRUD de Mallas
- ✅ CRUD de Cursos
- ✅ Generación de Recomendaciones
- ✅ Validaciones de datos
- ✅ Permisos y autorización

**Ejemplo de ejecución:**
```powershell
pytest tests/integration/ -v
```

### 2. **Tests de Concurrencia**

**Ubicación:** `tests/concurrency/`

**Propósito:** Validar el comportamiento del sistema bajo múltiples requests simultáneas.

**Características:**
- Tests asíncronos con `pytest-asyncio`
- Simulan race conditions
- Validan integridad de datos bajo concurrencia
- Prueban comportamiento bajo carga

**Escenarios probados:**
- ✅ Registros simultáneos de múltiples usuarios
- ✅ Race condition: mismo email registrado múltiples veces
- ✅ Logins concurrentes del mismo usuario
- ✅ Generación simultánea de recomendaciones
- ✅ Modificaciones concurrentes de datos
- ✅ Carga alta de requests de lectura
- ✅ Operaciones mixtas bajo carga

**Ejemplo de ejecución:**
```powershell
pytest tests/concurrency/ -v
```

## 📈 Cobertura de Código

### Generar Reporte de Cobertura

```powershell
pytest --cov=app --cov-report=html
```

Esto genera:
- Reporte en consola con porcentajes
- Carpeta `htmlcov/` con reporte HTML interactivo

### Ver Reporte HTML

```powershell
# Abrir en navegador
start htmlcov/index.html
```

### Cobertura por Módulo

```powershell
pytest --cov=app --cov-report=term-missing
```

Muestra líneas específicas que faltan por cubrir.

### Objetivo de Cobertura

Se recomienda mantener:
- **≥ 80%** de cobertura total
- **≥ 90%** en routers (endpoints)
- **≥ 85%** en utils y validators
- **≥ 70%** en algorithms (más complejos)

## 🎯 Fixtures Disponibles

El archivo `conftest.py` proporciona fixtures reutilizables:

### `client` - Cliente de prueba sincrónico
```python
def test_example(client: TestClient):
    response = client.get("/api/mallas/")
    assert response.status_code == 200
```

### `async_client` - Cliente de prueba asíncrono
```python
@pytest.mark.asyncio
async def test_example(async_client: AsyncClient):
    response = await async_client.get("/api/mallas/")
    assert response.status_code == 200
```

### `auth_headers` - Headers con token de usuario autenticado
```python
def test_example(client: TestClient, auth_headers: dict):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
```

### `admin_headers` - Headers con token de administrador
```python
def test_example(client: TestClient, admin_headers: dict):
    response = client.post("/api/mallas/", json=data, headers=admin_headers)
    assert response.status_code == 201
```

### `db_session` - Sesión de base de datos de prueba
```python
def test_example(db_session: Session):
    from app.models import Usuario
    user = Usuario(email="test@upao.edu.pe", ...)
    db_session.add(user)
    db_session.commit()
```

### Datos de prueba
- `test_user_data` - Datos de usuario de prueba
- `test_admin_data` - Datos de admin de prueba
- `sample_malla_data` - Datos de malla de ejemplo
- `sample_curso_data` - Datos de curso de ejemplo

## ✅ Buenas Prácticas

### 1. **Nombres Descriptivos**
```python
# ❌ Mal
def test_1():
    ...

# ✅ Bien
def test_user_registration_with_valid_data_succeeds():
    ...
```

### 2. **Arrange-Act-Assert (AAA)**
```python
def test_user_login():
    # Arrange
    user_data = {"email": "test@upao.edu.pe", "password": "Pass123"}
    client.post("/api/auth/register", json=user_data)
    
    # Act
    response = client.post("/api/auth/login", data={...})
    
    # Assert
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 3. **Tests Independientes**
- Cada test debe poder ejecutarse solo
- No depender del orden de ejecución
- Limpiar datos después de cada test (automático con fixtures)

### 4. **Validar Múltiples Aspectos**
```python
def test_create_malla():
    response = client.post("/api/mallas/", json=data)
    
    # Validar código de estado
    assert response.status_code == 201
    
    # Validar estructura de datos
    data = response.json()
    assert "id" in data
    assert data["nombre"] == expected_name
    
    # Validar que se guarda en BD
    get_response = client.get(f"/api/mallas/{data['id']}")
    assert get_response.status_code == 200
```

### 5. **Manejo de Errores**
```python
def test_create_malla_without_auth_fails():
    response = client.post("/api/mallas/", json=data)
    assert response.status_code == 401
    assert "authentication" in response.json()["detail"].lower()
```

## 🔍 Depuración de Tests

### Ver prints durante tests
```powershell
pytest -s
```

### Detener en el primer fallo
```powershell
pytest -x
```

### Modo de depuración con pdb
```powershell
pytest --pdb
```

### Ver logs
```powershell
pytest --log-cli-level=DEBUG
```

## 📊 Métricas de Tests

### Ver tiempo de ejecución
```powershell
pytest --durations=10
```

Muestra los 10 tests más lentos.

### Estadísticas completas
```powershell
pytest --tb=line --co
```

## 🚨 CI/CD

Para integración continua, se recomienda ejecutar:

```powershell
# Tests + cobertura + salida para CI
pytest --cov=app --cov-report=xml --cov-report=term -v
```

## 📝 Agregar Nuevos Tests

### 1. Tests de Integración
```python
# tests/integration/test_nuevo_modulo.py
import pytest
from fastapi.testclient import TestClient

class TestNuevoModulo:
    def test_operacion(self, client: TestClient):
        response = client.get("/api/nuevo/")
        assert response.status_code == 200
```

### 2. Tests de Concurrencia
```python
# tests/concurrency/test_nuevo_concurrency.py
import pytest
import asyncio
from httpx import AsyncClient

class TestNuevoConcurrency:
    @pytest.mark.asyncio
    async def test_operacion_concurrente(self, async_client: AsyncClient):
        tasks = [async_client.get("/api/nuevo/") for _ in range(10)]
        results = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in results)
```

## 🎓 Comandos Esenciales

```powershell
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app

# Tests específicos con detalles
pytest tests/integration/test_auth_endpoints.py -v

# Generar reporte HTML
pytest --cov=app --cov-report=html

# Ver tests más lentos
pytest --durations=10

# Tests de concurrencia
pytest tests/concurrency/ -v
```

## 📞 Ayuda

Para más información sobre pytest:
```powershell
pytest --help
```

---

**Última actualización:** 2024
**Versión:** 1.0
