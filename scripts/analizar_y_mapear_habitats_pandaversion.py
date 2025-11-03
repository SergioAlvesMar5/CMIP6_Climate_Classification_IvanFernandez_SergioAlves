# -- coding: utf-8 --
"""
IDENTIFICAR CLÚSTERES DE HÁBITATS USANDO EL MAPA K-MEANS MÁS RECIENTE

Instrucciones:
1. Se ejecuta después de 'generar_mapa_kmeans.py'.
2. BUSCA AUTOMÁTICAMENTE el archivo 'mapa_clasificacion_k*.nc' más
   reciente en la carpeta '../data_kmeans'.
3. EXTRAE el valor 'k' del nombre de ese archivo.
4. Carga el archivo .nc e identifica los clústeres usando puntos de muestra.
5. Genera el mapa final de hábitats.
"""

# 1. Importar librerías
import matplotlib
matplotlib.use('Agg') # Modo no interactivo

import xarray as xr
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
import warnings
import re # Para extraer el número del nombre

# =============================================================================
# >> CONFIGURACIÓN DE PUNTOS DE MUESTRA <<
# =============================================================================
PUNTOS_MUESTRA = {
    "Oso Polar": {
        "Svalbard (Noruega)": (78.2, 15.6),
        "Norte de Alaska": (70.5, -150.0),
    },
    "Oso Pardo": {
        # Usamos los puntos de MONTAÑA para identificar el hábitat real
        "Yellowstone (EEUU)": (44.6, -110.5),
        "Pirineos (España/Francia)": (42.7, 1.0), 
        "Montes Cárpatos (Rumanía)": (46.5, 25.0),
    },
    "Oso Perezoso": {
        # Puntos de referencia
        "Parque Chitwan (Nepal)": (27.5, 84.4),
        "India Central": (22.0, 79.0),
        "Sri Lanka": (8.0, 81.0),
    },
    "Oso Panda": {
        # Hábitat muy específico en montañas de China
        "Reserva Wolong (Sichuan)": (31.0, 103.0),
        "Montañas Qinling (Shaanxi)": (33.7, 107.5),
    }
}

# Rutas
RUTA_KMEANS = "../data_kmeans"
RUTA_FIGURES = "../figures"
# =============================================================================

def encontrar_nc_mas_reciente():
    """
    Busca el archivo 'mapa_clasificacion_k*.nc' más reciente
    en la carpeta RUTA_KMEANS.
    """
    # 1. Encontrar todos los archivos que coinciden con el patrón
    patron_busqueda = os.path.join(RUTA_KMEANS, 'mapa_clasificacion_k*.nc')
    lista_archivos_nc = glob.glob(patron_busqueda)
    
    if not lista_archivos_nc:
        print(f"¡ERROR! No se encontró ningún archivo 'mapa_clasificacion_k*.nc' en {RUTA_KMEANS}")
        return None, None

    # 2. Encontrar el más reciente (basado en la fecha de modificación)
    archivo_mas_reciente = max(lista_archivos_nc, key=os.path.getmtime)
    
    # 3. Extraer el número 'k' del nombre del archivo usando expresiones regulares
    nombre_archivo = os.path.basename(archivo_mas_reciente)
    match = re.search(r'mapa_clasificacion_k(\d+)\.nc', nombre_archivo)
    
    if not match:
        print(f"¡ERROR! El nombre del archivo {nombre_archivo} no sigue el patrón esperado '...k[numero].nc'")
        return None, None
        
    k_extraido = int(match.group(1))
    
    return archivo_mas_reciente, k_extraido


def identificar_habitats_reciente():
    """
    Función principal que encuentra el 'k' más reciente, carga el mapa
    e identifica los clústeres de osos.
    """
    print("===========================================================")
    print(f"Identificando Hábitats por Clúster (Archivo más reciente)")
    print("===========================================================")
    os.makedirs(RUTA_FIGURES, exist_ok=True)
    warnings.filterwarnings("ignore", category=FutureWarning)

    # --- 1. Encontrar el archivo .nc y el 'k' automáticamente ---
    archivo_nc, k_automatico = encontrar_nc_mas_reciente()
    
    if not archivo_nc:
        return # El error ya se imprimió en la función anterior
    
    print(f"\n--- Archivo más reciente encontrado ---")
    print(f"  -> Archivo: {os.path.basename(archivo_nc)}")
    print(f"  -> Valor 'k' extraído: {k_automatico}")

    # --- 2. Cargar el mapa de clasificación correspondiente ---
    try:
        ds = xr.open_dataset(archivo_nc)
        mapa_climas = ds['climate_class']
    except Exception as e:
        print(f"¡ERROR! No se pudo abrir el archivo: {archivo_nc}")
        print(f"Detalle: {e}")
        return

    print(f"Mapa '{os.path.basename(archivo_nc)}' cargado con éxito.")

    # --- 3. Identificar clústeres en los puntos de muestra ---
    print("\n--- Extrayendo clústeres de los puntos de muestra ---")
    zonas_por_habitat = {}
    
    for oso, puntos in PUNTOS_MUESTRA.items():
        zonas_encontradas = set()
        print(f"\nProcesando: {oso}")
        
        for nombre_loc, (lat, lon) in puntos.items():
            try:
                data_punto = mapa_climas.sel(lat=lat, lon=lon, method='nearest')
                # 1. Obtenemos el valor como float primero
                cluster_id_float = data_punto.item() 
                
                # 2. Comprobamos si es NaN ANTES de convertir a int
                if not np.isnan(cluster_id_float):
                    cluster_id = int(cluster_id_float)
                    print(f"  -> {nombre_loc} ({lat}N, {lon}E): Clúster {cluster_id}")
                    zonas_encontradas.add(cluster_id)
                else:
                    # 3. Informamos del NaN correctamente
                    print(f"  -> {nombre_loc} ({lat}N, {lon}E): Sin datos (NaN)")
            except Exception as e:
                print(f"  -> Error procesando {nombre_loc}: {e}")
        
        zonas_por_habitat[oso] = sorted(list(zonas_encontradas))
    
    print("\n--- Resumen de Clústeres por Especie ---")
    print(zonas_por_habitat)

    # --- 4. Generar el mapa ---
    print("\n--- Generando mapa de hábitats por clúster ---")
    
    lats = mapa_climas['lat'].values
    data_ciclica, lon_ciclica = add_cyclic_point(mapa_climas.values, coord=mapa_climas['lon'])
    
    # --- Ajustado a 3x2 (6 paneles) para 1 global + 4 especies ---
    fig, axes = plt.subplots(
        nrows=3, ncols=2, 
        figsize=(20, 18),
        subplot_kw={'projection': ccrs.Robinson()}
    )
    
    axes = axes.flatten()
    
    levels = np.arange(-0.5, k_automatico, 1)
    # Usamos tab20 para hasta 20 clústeres
    cmap = plt.get_cmap('tab20', k_automatico) 

    # --- Panel 0: Mapa Global de Referencia ---
    ax = axes[0]
    ax.set_title(f"Clima Global (k={k_automatico}) - Referencia")
    ax.coastlines(alpha=0.6)
    ax.gridlines(linestyle='--', alpha=0.3)
    ax.contourf(lon_ciclica, lats, data_ciclica,
    levels=levels, transform=ccrs.PlateCarree(), cmap=cmap)
    
    # --- Paneles 1-4: Hábitats por Clúster ---
    especies = list(zonas_por_habitat.keys())
    
    for i in range(5):
        ax = axes[i+1]
        if i < len(especies):
            oso = especies[i]
            zonas = zonas_por_habitat[oso]
            
            if not zonas:
                ax.set_title(f"Hábitat: {oso} (¡Ningún clúster encontrado!)")
                ax.coastlines(alpha=0.6)
                ax.set_global()
                continue

            mapa_mascara = mapa_climas.where(mapa_climas.isin(zonas))

            # --- ¡FILTRO GEOGRÁFICO PARA OSO PEREZOSO! ---
            # El Clúster 6 (Tropical Seco) es correcto para India,
            # pero un falso positivo en Australia y África.
            # Le decimos que SÓLO muestre el Clúster 6 en el continente Asiático
            # (ej. Longitud > 40°E y Latitud > 0°N)
            if oso == "Oso Perezoso" and zonas:
                # 'zonas' contiene los clústeres de este oso (p.ej. [6] para k=9, o [4] para k=7)
                # Donde el clúster sea uno de los de 'zonas' Y esté fuera de Asia...
                mapa_mascara = mapa_mascara.where(
                    ~((mapa_mascara.isin(zonas)) & ((mapa_mascara.lon < 40) | (mapa_mascara.lat < 0)))
                )
            # --- FIN DEL FILTRO ---
            
            # <--- MODIFICACIÓN: Añadido filtro geográfico para Oso Panda --->
            # El clúster del panda puede aparecer en otros lugares (falsos positivos).
            # Restringimos el clúster SÓLO a la región de China donde habita.
            if oso == "Oso Panda" and zonas: # Si se encontró algún clúster para el panda
                # Definimos el "cuadro" geográfico del hábitat del panda
                lat_min, lat_max = 28, 35
                lon_min, lon_max = 102, 109
                
                # Mantenemos los datos SÓLO si están dentro del cuadro geográfico.
                # Todo lo demás (falsos positivos) se convierte en NaN.
                mapa_mascara = mapa_mascara.where(
                    (mapa_mascara.lat >= lat_min) & (mapa_mascara.lat <= lat_max) &
                    (mapa_mascara.lon >= lon_min) & (mapa_mascara.lon <= lon_max)
                )
            # <--- FIN DE LA MODIFICACIÓN --->
            
            data_mascara_ciclica, _ = add_cyclic_point(
                mapa_mascara.values, coord=mapa_climas['lon']
            )
            
            ax.set_title(f"Hábitat: {oso} (Clústeres: {zonas})")
            ax.coastlines(alpha=0.6)
            ax.gridlines(linestyle='--', alpha=0.3)
            ax.set_global()
            ax.contourf(lon_ciclica, lats, data_mascara_ciclica,
                        levels=levels, transform=ccrs.PlateCarree(), cmap=cmap)
        else:
            # Oculta los paneles sobrantes (en este caso, el panel 6 o axes[5])
            ax.set_visible(False)

    plt.tight_layout(pad=2.0)
    
    ruta_salida = os.path.join(RUTA_FIGURES, f"mapa_clusters_osos_pandaversion_k{k_automatico}.png")
    plt.savefig(ruta_salida, dpi=300)
    print(f"\n¡Mapa de clústeres guardado en: {ruta_salida}!")
    print("===========================================================")

# --- Ejecutar el script ---
if __name__ == "__main__":
    identificar_habitats_reciente()