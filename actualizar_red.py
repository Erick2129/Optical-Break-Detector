import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
from shapely.geometry import LineString, MultiLineString

# 1. Tu conexión a BD
usuario = "postgres"
contrasena = "Chris0229"
servidor = "localhost"
puerto = "5432"
base_datos = "fibra_optica"

motor = create_engine(f"postgresql+psycopg2://{usuario}:{contrasena}@{servidor}:{puerto}/{base_datos}")

print("Actualizando KML y fusionando tramos abiertos ...")

with open("tramos.kml", "r", encoding="utf-8") as f:
    sopa = BeautifulSoup(f, "xml")

placemarks = sopa.find_all("Placemark")
lista_datos = []

# 2. Extracción profunda
for pm in placemarks:
    nombre_tag = pm.find("name")
    desc_tag = pm.find("description")
    
    nombre = nombre_tag.text.strip() if nombre_tag else "Sin Nombre"
    descripcion = desc_tag.text.strip() if desc_tag else ""
    
    # Buscamos TODAS las coordenadas dentro de este cliente, no solo la primera
    coords_tags = pm.find_all("coordinates")
    lineas_del_tramo = []
    
    for ct in coords_tags:
        texto_coords = ct.text.strip()
        puntos = []
        for pt in texto_coords.split():
            partes = pt.split(',')
            if len(partes) >= 2:
                puntos.append((float(partes[0]), float(partes[1])))
        
        # Filtramos puntos inválidos
        if len(puntos) >= 2:
            lineas_del_tramo.append(LineString(puntos))
            
    # Empaquetamos y soldamos los pedazos
    if len(lineas_del_tramo) == 1:
        geometria = lineas_del_tramo[0] # Tramo continuo normal
        lista_datos.append({"Name": nombre, "description": descripcion, "geometry": geometria})
    elif len(lineas_del_tramo) > 1:
        geometria = MultiLineString(lineas_del_tramo) # Tramo hecho de varios pedazos soldados
        lista_datos.append({"Name": nombre, "description": descripcion, "geometry": geometria})

# 3. Convertimos y empujamos a la BD
print("Convirtiendo datos para enviar a la base de datos...")
gdf_maestro = gpd.GeoDataFrame(lista_datos, geometry="geometry", crs="EPSG:4326")

nombre_tabla = "tramos_fibra"
print(f"Inyectando {len(gdf_maestro)} rutas completas a PostgreSQL...")
gdf_maestro.to_postgis(name=nombre_tabla, con=motor, if_exists="replace", index=False)

print("¡KML nuevo actualizado!")