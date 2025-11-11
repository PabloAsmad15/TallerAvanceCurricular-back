# Guía de Despliegue - Railway (GRATIS)

## 🚀 Despliegue Completo en Railway

Railway ofrece $5 USD de crédito gratis cada mes, suficiente para:
- ✅ Base de datos PostgreSQL 16
- ✅ Backend FastAPI
- ✅ Frontend React (como servicio estático)

---

## 📋 Paso 1: Configurar Base de Datos PostgreSQL

### 1.1 Crear cuenta en Railway
1. Ve a https://railway.app
2. Haz clic en "Start a New Project"
3. Conecta tu cuenta de GitHub
4. Autoriza el acceso

### 1.2 Crear Base de Datos
1. En Railway Dashboard → "New Project"
2. Selecciona "Provision PostgreSQL"
3. Railway creará automáticamente una instancia PostgreSQL 16
4. Ve a la pestaña "Variables"
5. Copia estas variables:
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`
   - `DATABASE_URL` (conexión completa)

---

## 📋 Paso 2: Desplegar Backend (FastAPI)

### 2.1 Preparar Repositorio
Tu backend ya está en GitHub: https://github.com/PabloAsmad15/TallerAvanceCurricular-back.git

### 2.2 Conectar con Railway
1. En Railway Dashboard → "New" → "GitHub Repo"
2. Busca y selecciona `TallerAvanceCurricular-back`
3. Railway detectará automáticamente que es Python

### 2.3 Configurar Variables de Entorno
En la pestaña "Variables" del servicio backend, agrega:

```env
# Database (usa la DATABASE_URL del PostgreSQL de Railway)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway

# Security
SECRET_KEY=genera_una_clave_super_segura_aqui_con_64_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Resend)
RESEND_API_KEY=re_tu_api_key_de_resend
DEV_EMAIL_OVERRIDE=tu_email@upao.edu.pe

# Google AI
GOOGLE_API_KEY=tu_google_gemini_api_key

# CORS - Actualizarás esto después de desplegar el frontend
ALLOWED_ORIGINS=https://tu-frontend.vercel.app
```

### 2.4 Verificar Despliegue
1. Railway construirá e instalará dependencias automáticamente
2. Ejecutará: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Obtendrás una URL como: `https://tu-backend.up.railway.app`
4. Prueba: `https://tu-backend.up.railway.app/docs`

---

## 📋 Paso 3: Cargar Datos Iniciales

### 3.1 Conectar a la Base de Datos desde Local
```bash
# Instala psql si no lo tienes
# En el backend local, crea un archivo .env.production

DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway

# Ejecuta el script de carga
python scripts/load_data.py
```

O usa Railway CLI:
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link al proyecto
railway link

# Ejecutar comando remoto
railway run python scripts/load_data.py
```

---

## 📋 Paso 4: Desplegar Frontend (Vercel - RECOMENDADO)

### 4.1 Por qué Vercel para Frontend
- ✅ Especializado en React/Vite
- ✅ GRATIS para siempre (no créditos)
- ✅ CDN global ultra rápido
- ✅ Despliegue automático desde GitHub

### 4.2 Desplegar en Vercel
1. Ve a https://vercel.com
2. "Import Project" → Conecta GitHub
3. Selecciona `TallerAvanceCurricular-front`
4. Configura:
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### 4.3 Variables de Entorno (Vercel)
```env
VITE_API_URL=https://tu-backend.up.railway.app/api
```

### 4.4 Actualizar CORS en Backend
1. Ve a Railway → Backend → Variables
2. Actualiza `ALLOWED_ORIGINS`:
```env
ALLOWED_ORIGINS=https://tu-frontend.vercel.app,http://localhost:5173
```

---

## 📋 Paso 5: Crear Usuario Administrador

### Opción A: Desde Railway CLI
```bash
railway run python -c "
from app.database import SessionLocal
from app.models import Usuario
from app.utils.security import get_password_hash

db = SessionLocal()
admin = Usuario(
    email='admin1502@upao.edu.pe',
    password_hash=get_password_hash('12345678'),
    nombre='Administrador',
    apellido='Sistema',
    is_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
print('✅ Admin creado')
"
```

### Opción B: Desde pgAdmin/DBeaver
1. Conecta a la base de datos de Railway
2. Ejecuta:
```sql
-- Primero obtén el hash de la contraseña desde tu local
-- Luego inserta:
INSERT INTO usuarios (email, password_hash, nombre, apellido, is_admin, is_active, created_at)
VALUES (
    'admin1502@upao.edu.pe',
    '$2b$12$[TU_HASH_AQUI]',
    'Administrador',
    'Sistema',
    true,
    true,
    NOW()
);
```

---

## 🎯 Resumen de URLs Finales

```
Base de Datos:  railway.app (PostgreSQL 16)
Backend API:    https://tu-backend.up.railway.app
Frontend:       https://tu-frontend.vercel.app
Documentación:  https://tu-backend.up.railway.app/docs
```

---

## 💰 Costos (TODO GRATIS)

### Railway
- ✅ $5 USD grédito/mes GRATIS
- PostgreSQL + Backend = ~$3/mes
- Sobran $2 para otros servicios

### Vercel
- ✅ GRATIS ilimitado
- No usa créditos de Railway

### Total: $0 USD/mes

---

## 🔧 Alternativa: TODO en Railway

Si prefieres TODO en Railway (incluido frontend):

### Frontend en Railway
1. Railway → New → GitHub Repo → `TallerAvanceCurricular-front`
2. Variables:
```env
VITE_API_URL=https://tu-backend.up.railway.app/api
```
3. Railway generará URL para el frontend
4. Actualiza CORS en backend con esa URL

**Nota:** Esto consumirá más créditos (~$4-5/mes total)

---

## 📊 Monitoreo

### Railway Dashboard
- CPU, RAM, Bandwidth
- Logs en tiempo real
- Métricas de base de datos

### Vercel Dashboard
- Tráfico
- Build status
- Analytics

---

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError"
✅ Asegúrate que `requirements.txt` esté completo
✅ Railway reconstruirá automáticamente

### Error: "Connection refused"
✅ Verifica DATABASE_URL en variables de Railway
✅ Usa la URL interna de PostgreSQL (no localhost)

### Error: "CORS"
✅ Agrega la URL de Vercel a ALLOWED_ORIGINS
✅ Incluye https:// completo

### Frontend no carga datos
✅ Verifica VITE_API_URL apunta a Railway
✅ Revisa logs en Railway del backend

---

## 🎓 Créditos Extra (Opcional)

### GitHub Student Pack
Si eres estudiante:
1. https://education.github.com/pack
2. Obtienes créditos extra en Railway, Vercel, etc.
3. Railway: +$20 USD adicionales

---

## 📝 Siguiente Paso

Una vez desplegado, prueba:

1. **Frontend**: `https://tu-frontend.vercel.app`
2. **Login**: admin1502@upao.edu.pe / 12345678
3. **Dashboard Admin**: Debería mostrar gráficos
4. **Crear usuario**: Registra uno nuevo
5. **Generar recomendación**: Prueba el flujo completo

---

**¿Necesitas ayuda con algún paso específico?**
