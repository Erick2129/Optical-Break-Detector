import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================
# 1. TU PANEL DE INGRESO DIARIO
# ==========================================
nombre_cliente = "Reservado INFINERA Riomar - Santa Marta"
distancia_otdr_metros = 10000      

# Cambia a True si notas que el KML se dibujó desde el cliente hacia el nodo
invertir_direccion = True

# Descuento del 25% por reservas/cocas
distancia_real_falla = distancia_otdr_metros * 0.75 

# 2. Conexión a la base de datos
usuario = "postgres"
contrasena = "Chris0229"
servidor = "localhost"
puerto = "5432"
base_datos = "fibra_optica"

motor = create_engine(f"postgresql+psycopg2://{usuario}:{contrasena}@{servidor}:{puerto}/{base_datos}")

# ==========================================
# 3. EL CEREBRO ESPACIAL
# ==========================================
consulta_sql = text("""
    SELECT 
        MAX("Name") as nombre_tramo,
        -- ST_Union atrapa todos los 'rows' del cliente y los funde en una sola ruta verde
        ST_LineMerge(ST_Union(ST_SnapToGrid(geometry, 0.00005))) as geometria_corregida,
        ST_Length(ST_LineMerge(ST_Union(ST_SnapToGrid(geometry, 0.00005)))::geography) as distancia_mapa_metros
    FROM 
        tramos_fibra 
    WHERE 
        "Name" ILIKE :palabra_clave 
        OR description ILIKE :palabra_clave
""")

parametros = {"palabra_clave": f"%{nombre_cliente}%"}

# Traemos el cable de la base de datos
gdf_ruta = gpd.read_postgis(consulta_sql, con=motor, geom_col='geometria_corregida', params=parametros)

if gdf_ruta.empty:
    print(f"❌ No se encontró ningún tramo asociado a '{nombre_cliente}'.")
else:
    # Extraemos los datos exactos
    nombre_bd = gdf_ruta.iloc[0]['nombre_tramo']
    distancia_total = round(gdf_ruta.iloc[0]['distancia_mapa_metros'], 2)
    linea_fisica = gdf_ruta.iloc[0]['geometria_corregida']
    
    print("\n" + "="*50)
    print("🎯 REPORTE DE CÁLCULO DE FALLA - PANDO SAS 🎯")
    print("="*50)
    print(f"📍 Cliente/Ruta: {nombre_bd} (Búsqueda: {nombre_cliente})")
    print(f"📏 Distancia TOTAL de la ruta en el mapa: {distancia_total} metros")
    print(f"📡 Distancia OTDR bruta: {distancia_otdr_metros} metros")
    print(f"✂️ Distancia a buscar (descontando reservas): {distancia_real_falla} metros")
    
    if distancia_real_falla > distancia_total:
        print("\n⚠️ ALERTA: La falla calculada supera el largo total del cable en el mapa.")
        porcentaje_recorrido = 1.0 
    else:
        # Regla de 3 normal
        porcentaje_recorrido = distancia_real_falla / distancia_total
        
        # EL HACK MATEMÁTICO DE INVERSIÓN
        if invertir_direccion:
            print("\n🔄 MODO INVERTIDO ACTIVADO: Midiendo desde el final de la línea hacia atrás.")
            # Si la línea mide 100%, y el daño está al 20%, al invertirlo le decimos que marque el 80%
            porcentaje_recorrido = 1.0 - porcentaje_recorrido
        else:
            print(f"\n✅ Análisis: El corte está al {round(porcentaje_recorrido*100, 1)}% del recorrido.")
    
    print("="*50)

    # ==========================================
    # 4. CLAVAR EL PUNTO Y CREAR EL KML
    # ==========================================
    print("\nGenerando mapa exportable para Google Earth...")
    
    punto_falla = linea_fisica.interpolate(porcentaje_recorrido, normalized=True)
    
    datos_kml = pd.DataFrame({
        "Name": [f"Ruta completa: {nombre_bd}", f" PUNTO POSIBLE DE CORTE ({distancia_real_falla}m)"],
        "Description": [f"Distancia total: {distancia_total}m", f"Distancia OTDR real: {distancia_real_falla}m"]
    })
    
    gdf_kml = gpd.GeoDataFrame(datos_kml, geometry=[linea_fisica, punto_falla], crs="EPSG:4326")
    
    nombre_archivo_salida = f"Prueba-{nombre_cliente}.kml"
    
    # EL HACK: Le decimos que exporte usando nuestro motor turbo (engine="pyogrio")
    gdf_kml.to_file(nombre_archivo_salida, driver="KML", engine="pyogrio")
    
    print(f"\n ¡LISTO! Se acaba de crear el archivo '{nombre_archivo_salida}' en tu carpeta.")
    print("Ábrelo en Google Earth, saca tu regla manual, y verifica la precisión. ¡A medir la FO!")