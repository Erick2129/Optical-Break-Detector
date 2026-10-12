import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from fastapi import FastAPI
import pyogrio
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# 1. Iniciamos el servidor de FastAPI (La ventanilla)
app = FastAPI()

# EL HACK: Le decimos al mesero que todo lo que esté en la carpeta "static" (CSS, Imágenes) lo entregue sin hacer preguntas.
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. La conexión a BD se queda afuera porque solo necesitamos conectarnos una vez al prender el servidor
usuario = "postgres"
contrasena = "Chris0229"
servidor = "localhost"
puerto = "5432"
base_datos = "fibra_optica"
motor = create_engine(f"postgresql+psycopg2://{usuario}:{contrasena}@{servidor}:{puerto}/{base_datos}")

# 3. Envolvemos todo tu script en una función que reacciona a internet y definimos las variables a usar
@app.get("/generar_kml")
def calcular_falla_api(cliente: str, distancia_otdr: float, invertir: bool = False):
    
    # Calculos usando las variables de arriba
    distancia_real_falla = distancia_otdr * 0.75 
    
    consulta_sql = text("""
        SELECT MAX("Name") as nombre_tramo,
               ST_LineMerge(ST_Union(ST_SnapToGrid(geometry, 0.00005))) as geometria_corregida,
               ST_Length(ST_LineMerge(ST_Union(ST_SnapToGrid(geometry, 0.00005)))::geography) as distancia_mapa_metros
        FROM tramos_fibra 
        WHERE "Name" ILIKE :palabra_clave OR description ILIKE :palabra_clave
    """)
    
    parametros = {"palabra_clave": f"%{cliente}%"}
    gdf_ruta = gpd.read_postgis(consulta_sql, con=motor, geom_col='geometria_corregida', params=parametros)
    
    if gdf_ruta.empty or gdf_ruta.iloc[0]['nombre_tramo'] is None:
        # En caso de que el nombre del cliente no exista o esté mas escrito
        return {"error": f"Alerta: El tramo '{cliente}' no existe en la base de datos o está mal escrito."}
        
    nombre_bd = gdf_ruta.iloc[0]['nombre_tramo']
    distancia_total = round(gdf_ruta.iloc[0]['distancia_mapa_metros'], 2)
    linea_fisica = gdf_ruta.iloc[0]['geometria_corregida']
    
    if distancia_real_falla > distancia_total:
        porcentaje_recorrido = 1.0 
    else:
        porcentaje_recorrido = distancia_real_falla / distancia_total
        if invertir:
            porcentaje_recorrido = 1.0 - porcentaje_recorrido
            
    # Creamos el KML
    punto_falla = linea_fisica.interpolate(porcentaje_recorrido, normalized=True)
    datos_kml = pd.DataFrame({
        "Name": [f"Ruta: {nombre_bd}", f"🔥 CORTE ({distancia_real_falla}m)"],
        "Description": [f"Total: {distancia_total}m", f"OTDR: {distancia_real_falla}m"]
    })
    
    gdf_kml = gpd.GeoDataFrame(datos_kml, geometry=[linea_fisica, punto_falla], crs="EPSG:4326")
    nombre_archivo = f"Cliente_{cliente}.kml"
    # Guardamos el archivo como lo hacíamos antes
    gdf_kml.to_file(nombre_archivo, driver="KML", engine="pyogrio")
    
    # EL HACK: En vez de texto, disparamos el archivo directo al navegador
    return FileResponse(path=nombre_archivo, filename=nombre_archivo)

@app.get("/", response_class=HTMLResponse)
def mostrar_interfaz():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()