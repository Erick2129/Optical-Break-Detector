#  Fiber Optic Fault Radar (QGIS + Full-Stack)

Sistema web para el diagnóstico automatizado y localización geoespacial de fallas en redes de fibra óptica, integrando mediciones de reflectometría en el dominio del tiempo (OTDR) con análisis topológico en bases de datos espaciales.

## Tecnologías

- **Backend:** Python, FastAPI, Uvicorn
- **Base de Datos Espacial:** PostgreSQL + PostGIS (ST_LineLocatePoint, ST_DWithin)
- **Frontend:** HTML5, CSS3 (Glassmorphism UI), JavaScript ES6 (Fetch API asíncrona)
- **Formatos:** KML / GeoJSON para interoperabilidad con Google Earth y QGIS

## Arquitectura y Funcionamiento

1. **Ingesta de Medición:** El operador introduce el ID del enlace/cliente y la distancia óptica reportada por el OTDR.
2. **Reconstrucción Topológica:** El motor backend consulta la secuencia de tramos (FOCR) y unifica la geometría de la ruta.
3. **Cálculo Geoespacial:** Se proyecta la distancia sobre la línea continua mediante referenciación lineal, determinando la coordenada exacta (Lat/Lng) del corte o macrocurvatura.
4. **Exportación Dinámica:** Generación y descarga asíncrona de archivos KML listos para visualización en campo.

## Instalación Local

```bash
# 1. Clonar el repositorio
git clone [https://github.com/tu-usuario/fiber-fault-radar.git](https://github.com/tu-usuario/fiber-fault-radar.git)
cd fiber-fault-radar

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (.env) a partir de .env.example

# 4. Iniciar servidor
uvicorn api:app --reload