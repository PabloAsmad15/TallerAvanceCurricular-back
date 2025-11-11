# 📊 Guía para Preparar y Cargar tus Datos CSV

## 📁 Estructura de Archivos Requerida

Coloca tus archivos CSV en: `backend/data/mallas/`

```
backend/
└── data/
    └── mallas/
        ├── malla_2015.csv
        ├── malla_2019.csv
        ├── malla_2022.csv
        ├── malla_2025.csv
        └── convalidaciones.csv
```

## 📋 Formato de Archivos CSV

### 1. Mallas Curriculares (`malla_XXXX.csv`)

**Separador:** Punto y coma (`;`)
**Encoding:** UTF-8 con BOM (`utf-8-sig`)

**Columnas requeridas:**
```csv
Código;Nombre de la asignatura;Creditos;Ciclo;Prerrequisitos
```

**Ejemplo:**
```csv
Código;Nombre de la asignatura;Creditos;Ciclo;Prerrequisitos
ICSI-506;Introducción a la Programación;4;I;NINGUNO
ICSI-509;Programación Orientada a Objetos;4;II;ICSI-506
ICSI-510;Estructura de Datos;4;III;ICSI-509
CIEN-752;Matemática Básica;4;I;NINGUNO
CIEN-768;Cálculo I;4;II;CIEN-752
ICSI-671;Base de Datos;4;III;ICSI-509,ICSI-510
```

**Notas importantes:**
- **Ciclos**: Usar números romanos: I, II, III, IV, V, VI, VII, VIII, IX, X
- **Prerequisitos**: 
  - Si no hay: escribir `NINGUNO`
  - Si hay varios: separarlos con comas (`,`)
  - Ejemplo: `ICSI-509,ICSI-510`
- **Espacios**: El sistema los normaliza automáticamente, pero mejor evitarlos en códigos

### 2. Convalidaciones (`convalidaciones.csv`)

**Separador:** Punto y coma (`;`)
**Encoding:** UTF-8 con BOM

**Columnas requeridas:**
```csv
Malla_Origen;Codigo_Origen;Codigo_Destino_2025
```

**Ejemplo:**
```csv
Malla_Origen;Codigo_Origen;Codigo_Destino_2025
2015;ICSI-401;ICSI-506
2015;ICSI-402;ICSI-509
2015;CIEN-397;CIEN-752
2019;ICSI-506;ICSI-506
2019;ICSI-507;ICSI-509
2022;ICSI-506;ICSI-506
```

**Notas importantes:**
- **Malla_Origen**: Número del año (2015, 2019, 2022)
- **Codigo_Origen**: Código del curso en la malla antigua
- **Codigo_Destino_2025**: Código equivalente en la malla 2025
- Si un curso se mantiene igual, igual debes ponerlo en el CSV

## 🔧 Script de Carga Modificado

El script `load_data.py` ya está adaptado para trabajar con tu formato. Características:

✅ **Normalización automática de códigos** (quita espacios)
✅ **Conversión de ciclos romanos a números**
✅ **Manejo robusto de prerequisitos**
✅ **Validación de datos**
✅ **Mensajes de debug detallados**

## 🚀 Cómo Cargar los Datos

### Opción 1: Usando el Script (Recomendado)

```bash
# Activar entorno virtual
cd backend
.\venv\Scripts\activate

# Cargar datos
python scripts/load_data.py
```

**Salida esperada:**
```
🚀 Iniciando carga de datos...

📚 Cargando mallas...
✅ Malla 2015 creada
✅ Malla 2019 creada
✅ Malla 2022 creada
✅ Malla 2025 creada

📖 Cargando cursos...
   Procesando malla 2015...
   ✅ Curso creado: ICSI-401 - Introducción a la Programación
   ...

🔄 Cargando convalidaciones...
   ✅ Convalidación: ICSI-401 → ICSI-506
   ...

✅ ¡Datos cargados exitosamente!

📊 Resumen:
   - Mallas: 4
   - Cursos: 205
   - Prerequisitos: 180
   - Convalidaciones: 150
```

### Opción 2: Desde la API

Una vez el servidor esté corriendo, puedes crear un endpoint para cargar datos:

```python
# En app/routers/admin.py (crear si no existe)
@router.post("/load-data")
async def load_data_from_csv(db: Session = Depends(get_db)):
    # Llamar a las funciones de carga
    # ...
```

## ⚠️ Problemas Comunes y Soluciones

### Error: "No se encontró la columna"
**Causa:** Nombres de columnas incorrectos
**Solución:** Verifica que los encabezados sean EXACTOS (mayúsculas, acentos, espacios)

### Error: "Encoding issue"
**Causa:** Archivo no está en UTF-8
**Solución:** 
- Abrir CSV en Excel
- Guardar como → CSV UTF-8 (delimitado por comas)
- Cambiar comas por punto y coma

### Error: "ciclo_entero = 0"
**Causa:** Ciclos no están en formato romano
**Solución:** Usar I, II, III, IV, V, VI, VII, VIII, IX, X

### Cursos sin convalidación
**Info:** Es normal si hay cursos nuevos en malla 2025
**Acción:** El sistema lo maneja automáticamente

## 🧪 Validar Datos Cargados

Después de cargar, verifica en PostgreSQL:

```sql
-- Ver mallas
SELECT * FROM mallas;

-- Ver cursos por malla
SELECT COUNT(*), malla_id FROM cursos GROUP BY malla_id;

-- Ver prerequisitos
SELECT COUNT(*) FROM prerequisitos;

-- Ver convalidaciones
SELECT COUNT(*), malla_origen_anio FROM convalidaciones GROUP BY malla_origen_anio;

-- Verificar un curso específico
SELECT c.codigo, c.nombre, c.ciclo, c.creditos
FROM cursos c
WHERE c.codigo = 'ICSI-506';

-- Ver prerequisitos de un curso
SELECT 
    c1.codigo AS curso,
    c2.codigo AS prerequisito
FROM prerequisitos p
JOIN cursos c1 ON p.curso_id = c1.id
JOIN cursos c2 ON p.prerequisito_id = c2.id
WHERE c1.codigo = 'ICSI-671';
```

## 📝 Template CSV para Comenzar

Si quieres empezar de cero, usa estos templates:

**malla_2025_template.csv:**
```csv
Código;Nombre de la asignatura;Creditos;Ciclo;Prerrequisitos
ICSI-506;Introducción a la Programación;4;I;NINGUNO
CIEN-752;Matemática Básica;4;I;NINGUNO
HUMA-900;Comunicación;3;I;NINGUNO
```

**convalidaciones_template.csv:**
```csv
Malla_Origen;Codigo_Origen;Codigo_Destino_2025
2015;ICSI-401;ICSI-506
2019;ICSI-506;ICSI-506
2022;ICSI-506;ICSI-506
```

## 🔄 Re-cargar Datos

Si necesitas re-cargar datos:

```bash
# Opción 1: Borrar y re-crear base de datos
DROP DATABASE "avance-curricular";
CREATE DATABASE "avance-curricular";
python scripts/load_data.py

# Opción 2: Borrar solo las tablas
python
>>> from app.database import engine, Base
>>> Base.metadata.drop_all(bind=engine)
>>> Base.metadata.create_all(bind=engine)
>>> exit()
python scripts/load_data.py
```

## ✅ Checklist Final

Antes de cargar datos, verifica:

- [ ] Archivos están en `backend/data/mallas/`
- [ ] Nombres de archivos son correctos (`malla_2015.csv`, etc.)
- [ ] Separador es punto y coma (`;`)
- [ ] Encoding es UTF-8 con BOM
- [ ] Columnas tienen nombres exactos
- [ ] Ciclos están en números romanos
- [ ] Base de datos PostgreSQL está corriendo
- [ ] `.env` tiene credenciales correctas
- [ ] Entorno virtual está activado

## 🆘 Soporte

Si tienes problemas:

1. **Revisar logs del script** - Muestra errores detallados
2. **Verificar formato CSV** - Usar Excel o VSCode
3. **Probar con datos de ejemplo** - Usar los templates
4. **Verificar base de datos** - Ejecutar queries SQL de validación

---

**Tip Pro:** 💡 Mantén una copia de backup de tus CSVs antes de modificarlos.
