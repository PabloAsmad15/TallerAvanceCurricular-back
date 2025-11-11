# 🎓 Sistema de Recomendación Curricular UPAO - Backend

API REST desarrollada con FastAPI para el sistema de recomendación de avance curricular con IA para la Universidad Privada Antenor Orrego.

## 🚀 Características

- **Autenticación JWT**: Sistema seguro de login con tokens
- **Gestión de Mallas Curriculares**: Soporte para múltiples planes de estudio (2015, 2019, 2022, 2025)
- **Recomendaciones con IA**: Integración con Gemini AI para sugerencias personalizadas
- **Panel de Administración**: Dashboard con estadísticas y visualizaciones
- **Base de Datos**: PostgreSQL con SQLAlchemy ORM
- **CORS Configurado**: Listo para producción

## 📋 Requisitos Previos

- Python 3.10+
- PostgreSQL 14+
- pip

## 🛠️ Instalación Local

1. **Clonar el repositorio**
```bash
git clone https://github.com/PabloAsmad15/TallerAvanceCurricular-back.git
cd TallerAvanceCurricular-back
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

Copia `.env.example` a `.env` y configura:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=tu-secret-key-segura
RESEND_API_KEY=tu-resend-api-key
GEMINI_API_KEY=tu-gemini-api-key
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
```

5. **Inicializar base de datos**
```bash
python scripts/init_db.py
python scripts/load_data.py
```

6. **Ejecutar servidor**
```bash
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en: `http://localhost:8000`
Documentación: `http://localhost:8000/docs`

## 🐳 Docker

```bash
docker-compose up -d
```

## 📦 Estructura del Proyecto

```
backend/
├── app/
│   ├── routers/          # Endpoints de la API
│   ├── models.py         # Modelos SQLAlchemy
│   ├── schemas.py        # Schemas Pydantic
│   ├── database.py       # Configuración DB
│   ├── config.py         # Variables de entorno
│   └── main.py           # Aplicación FastAPI
├── scripts/              # Scripts de inicialización
├── .env.example          # Template de variables
├── requirements.txt      # Dependencias Python
└── Dockerfile           # Imagen Docker

```

## 🌐 Deployment

### Fly.io (Recomendado)

```bash
fly launch
fly secrets set DATABASE_URL="..." SECRET_KEY="..." GEMINI_API_KEY="..."
fly deploy
```

### Railway

1. Conectar repo de GitHub
2. Agregar variables de entorno
3. Deploy automático

## 🔐 Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `DATABASE_URL` | URL de PostgreSQL | ✅ |
| `SECRET_KEY` | Clave JWT | ✅ |
| `GEMINI_API_KEY` | API Key de Google Gemini | ✅ |
| `RESEND_API_KEY` | API Key de Resend (emails) | ⚠️ |
| `FRONTEND_URL` | URL del frontend | ✅ |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | ✅ |

## 📚 API Endpoints

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Usuario actual

### Mallas Curriculares
- `GET /api/mallas` - Listar mallas
- `GET /api/mallas/{id}` - Detalle de malla

### Cursos
- `GET /api/cursos` - Listar cursos
- `GET /api/cursos/{id}` - Detalle de curso

### Recomendaciones
- `POST /api/recommendations/generate` - Generar recomendación con IA

### Admin
- `GET /api/admin/dashboard` - Estadísticas del sistema
- `GET /api/admin/users` - Listar usuarios

Ver documentación completa en `/docs` (Swagger UI)

## 👥 Usuarios de Prueba

```
Admin:
Email: admin1502@upao.edu.pe
Password: 12345678

Usuario:
Email: pasmadm1@upao.edu.pe
Password: 87654321
```

## 🧪 Testing

```bash
pytest
```

## 📄 Licencia

Este proyecto es privado y de uso exclusivo para la Universidad Privada Antenor Orrego.

## 👨‍💻 Autor

**Pablo Enrique Asmad Morgado**
- GitHub: [@PabloAsmad15](https://github.com/PabloAsmad15)

## 🔗 Enlaces

- **Backend Producción**: https://taller-avance-curricular-upao.fly.dev
- **Frontend Producción**: https://taller-avance-curricular-front.vercel.app
- **Repositorio Frontend**: https://github.com/PabloAsmad15/TallerAvanceCurricular-front

---

Desarrollado con ❤️ para mejorar la experiencia académica en UPAO UPAO

> 🚀 **Backend API REST** con FastAPI y PostgreSQL que implementa un agente de IA para recomendar avance curricular utilizando Constraint Programming o Backtracking.

## � Tabla de Contenidos

- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [API Endpoints](#-api-endpoints)
- [Algoritmos](#-algoritmos)
- [Base de Datos](#-base-de-datos)

## �🚀 Características

- **Autenticación JWT** con validación de correos @upao.edu.pe
- **Recuperación de contraseña** por email
- **Agente de IA** con Gemini que decide el algoritmo óptimo
- **Dos algoritmos de recomendación**:
  - Constraint Programming (OR-Tools CP-SAT)
  - Backtracking por ramas
- **Base de datos PostgreSQL** con SQLAlchemy ORM
- **Soporte para 4 mallas curriculares**: 2015, 2019, 2022, 2025
- **Sistema de convalidaciones** entre mallas
- **Detección de estudiantes regulares/irregulares**
- **Límites de créditos por ciclo** (20-22 créditos)

## 📋 Requisitos Previos

- **Python** 3.10 o superior
- **PostgreSQL** 14 o superior
- **Cuenta de Google Cloud** con Gemini API activada
- **Cuenta de Resend** para envío de correos (más simple que SMTP)

## 🔧 Instalación

1. **Clonar el repositorio**:
```bash
git clone <url-repositorio-backend>
cd backend
```

2. **Crear entorno virtual**:
```bash
python -m venv venv
```

3. **Activar entorno virtual**:

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

1. **Crear base de datos PostgreSQL**:
```sql
CREATE DATABASE "avance-curricular";
```

2. **Copiar archivo de configuración**:
```bash
cp .env.example .env
```

3. **Editar `.env` con tus credenciales**:
```env
# Database
DATABASE_URL=postgresql://tu_usuario:tu_password@localhost:5432/avance-curricular

# JWT
SECRET_KEY=genera_una_clave_segura_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Resend)
RESEND_API_KEY=re_tu_api_key_de_resend
DEV_EMAIL_OVERRIDE=tu_email@upao.edu.pe

# Gemini API
GEMINI_API_KEY=tu_gemini_api_key

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

4. **Generar SECRET_KEY segura** (opcional pero recomendado):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. **Obtener Gemini API Key**:
   - Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Crea un proyecto y genera una API key
   - Copia la key al archivo `.env`

6. **Obtener Resend API Key** (para envío de correos):
   - Regístrate en [Resend](https://resend.com)
   - Crea una API key
   - Verifica tu dominio o usa el dominio de prueba
   - Copia la key al archivo `.env`

7. **Preparar datos de mallas** (ver `GUIA_CARGA_DATOS.md` para más detalles):
   - Coloca tus archivos CSV en `data/mallas/`
   - Formato: `malla_2015.csv`, `malla_2019.csv`, `malla_2022.csv`, `malla_2025.csv`, `convalidaciones.csv`

8. **Cargar datos iniciales**:
```bash
python scripts/load_data.py
```

## 🏃 Ejecución

### Desarrollo

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación interactiva**: http://localhost:8000/docs
- **Documentación alternativa**: http://localhost:8000/redoc

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── config.py                  # Configuración y variables de entorno
│   ├── database.py                # Conexión a PostgreSQL
│   ├── models/                    # Modelos SQLAlchemy
│   │   └── __init__.py           # Usuario, Malla, Curso, etc.
│   ├── schemas/                   # Esquemas Pydantic
│   │   └── __init__.py           # Validación de datos
│   ├── routers/                   # Endpoints de la API
│   │   ├── auth.py               # Autenticación y recuperación
│   │   ├── mallas.py             # Gestión de mallas
│   │   ├── cursos.py             # Gestión de cursos
│   │   └── recommendations.py    # Recomendaciones
│   ├── services/                  # Lógica de negocio
│   │   └── ai_agent.py           # Agente de IA con Gemini
│   ├── algorithms/                # Algoritmos de recomendación
│   │   ├── constraint_programming.py  # OR-Tools CP-SAT
│   │   └── backtracking.py            # Backtracking por ramas
│   └── utils/                     # Utilidades
│       ├── security.py           # JWT, hash de passwords
│       └── email.py              # Envío de correos
├── alembic/                       # Migraciones de base de datos
├── data/
│   └── mallas/                    # Archivos CSV de mallas
├── scripts/
│   └── load_data.py              # Script de carga de datos
├── tests/                         # Tests unitarios
├── requirements.txt               # Dependencias Python
├── .env.example                   # Plantilla de configuración
├── .gitignore                     # Archivos ignorados por Git
├── GUIA_CARGA_DATOS.md           # Guía para cargar datos CSV
└── README.md                      # Este archivo
```

## 🔐 API Endpoints

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/register` | Registro de nuevo usuario |
| POST | `/api/auth/login-json` | Inicio de sesión (retorna JWT + datos de usuario) |
| GET | `/api/auth/me` | Obtener datos del usuario actual |
| POST | `/api/auth/forgot-password` | Solicitar recuperación de contraseña |
| POST | `/api/auth/reset-password` | Cambiar contraseña con token |

### Mallas y Cursos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/mallas` | Listar todas las mallas |
| GET | `/api/mallas/{id}` | Obtener malla específica |
| GET | `/api/cursos/malla/{malla_id}` | Obtener cursos por malla |
| GET | `/api/cursos/malla/{malla_id}/por-ciclo` | Cursos agrupados por ciclo |

### Recomendaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/recommendations/` | Generar nueva recomendación |
| GET | `/api/recommendations/history` | Historial de recomendaciones del usuario |
| GET | `/api/recommendations/{id}` | Detalle de recomendación específica |
| GET | `/api/recommendations/stats/algorithms` | Estadísticas de uso de algoritmos |

### Administración (requiere is_admin=true)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/admin/stats/general` | Estadísticas generales del sistema |
| GET | `/api/admin/stats/recomendaciones` | Estadísticas de recomendaciones (tendencias) |
| GET | `/api/admin/usuarios` | Lista de usuarios con paginación |
| GET | `/api/admin/recomendaciones/recientes` | Últimas recomendaciones realizadas |

## 🤖 Algoritmos

### 1. Agente de IA (Gemini)

El agente analiza múltiples factores para decidir qué algoritmo usar:

- **Número de cursos pendientes**: CP para >20 cursos
- **Complejidad de prerequisitos**: CP para dependencias complejas
- **Porcentaje de avance**: Backtracking para >70%
- **Ciclo actual**: CP para ciclos iniciales (1-4)
- **Estudiante regular/irregular**: Backtracking para irregulares
- **Año de malla**: CP para mallas nuevas (2022, 2025)

### 2. Constraint Programming (OR-Tools CP-SAT)

**Cuándo se usa:**
- Muchas restricciones simultáneas
- Estudiantes con bajo avance (<50%)
- Necesidad de optimización global
- Prerequisitos complejos

**Características:**
- Límites de créditos: 12-22 por ciclo
- Universo reducido: ciclo actual + 2 siguientes
- Prioriza cursos obligatorios
- Optimiza usando pesos por ciclo

### 3. Backtracking por Ramas

**Cuándo se usa:**
- Estudiantes con alto avance (>70%)
- Situaciones irregulares
- Menos cursos pendientes (<20)
- Necesidad de recomendación directa

**Características:**
- Detección de último ciclo completo
- Recomendación en dos fases:
  1. Cursos obligatorios pendientes
  2. Siguiente rama/área temática
- Límites específicos por ciclo: {1:20, 2:21, 3:22, 4:20, ...}

## 📊 Base de Datos

### Tablas Principales

```sql
-- Usuarios
usuarios (id, email, password_hash, nombre, apellido)

-- Mallas curriculares
mallas (id, nombre, anio, descripcion)

-- Cursos
cursos (id, malla_id, codigo, nombre, ciclo, creditos)

-- Prerequisitos
prerequisitos (id, curso_id, prerequisito_id)

-- Convalidaciones
convalidaciones (id, curso_origen_id, curso_destino_id, malla_origen_anio)

-- Recomendaciones
recomendaciones (id, usuario_id, malla_id, algoritmo_usado, cursos_recomendados, razon)

-- Password Reset
password_reset (id, usuario_id, token, expira_en)
```

### Consultas Útiles

```sql
-- Ver todas las mallas
SELECT * FROM mallas;

-- Cursos por ciclo
SELECT ciclo, COUNT(*) FROM cursos GROUP BY ciclo ORDER BY ciclo;

-- Prerequisitos de un curso
SELECT c2.codigo, c2.nombre
FROM prerequisitos p
JOIN cursos c1 ON p.curso_id = c1.id
JOIN cursos c2 ON p.prerequisito_id = c2.id
WHERE c1.codigo = 'ICSI-506';

-- Historial de recomendaciones
SELECT u.email, r.algoritmo_usado, r.fecha_creacion
FROM recomendaciones r
JOIN usuarios u ON r.usuario_id = u.id
ORDER BY r.fecha_creacion DESC;
```

## 🧪 Testing

Ejecutar tests:
```bash
pytest
```

Con cobertura:
```bash
pytest --cov=app tests/
```

## 🐳 Docker (Opcional)

```bash
# Construir imagen
docker build -t upao-backend .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env upao-backend
```

## 📝 Notas Importantes

1. **Correos @upao.edu.pe**: Solo se permiten registros con email institucional
2. **Gemini API**: Requiere conexión a internet para el agente de IA
3. **Límite de créditos**: El sistema respeta los límites de 12-22 créditos por ciclo
4. **Convalidaciones**: Se aplican automáticamente al cambiar de malla
5. **Tokens JWT**: Expiran en 30 minutos (configurable)

## 🔒 Seguridad

- Passwords hasheados con bcrypt
- JWT con algoritmo HS256
- Validación de email institucional
- Rate limiting en endpoints de autenticación (recomendado en producción)
- CORS configurado para frontend específico

## 🚀 Deployment

### Variables de entorno en producción:

```env
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
SECRET_KEY=clave_muy_segura_y_larga_en_produccion
GEMINI_API_KEY=tu_api_key_real
FRONTEND_URL=https://tu-dominio-frontend.com
```

### Servicios recomendados:

- **Backend**: Railway, Render, Fly.io, AWS EC2
- **Base de datos**: Railway PostgreSQL, Supabase, AWS RDS
- **Logs**: Sentry, LogDNA

## 📚 Recursos

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
- [Gemini API](https://ai.google.dev/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 📧 Soporte

Para problemas o preguntas:
1. Revisa la documentación en `/docs`
2. Consulta `GUIA_CARGA_DATOS.md` para problemas con datos
3. Verifica logs en consola
4. Revisa que todas las variables de entorno estén configuradas

## � Licencia

MIT

---

**Desarrollado para la Universidad Privada Antenor Orrego (UPAO)**