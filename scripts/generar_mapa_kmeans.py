# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('Agg')

import xarray as xr
import os
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point

# --- RUTAS ---
RUTA_PCA_IN = "../data_pca"
RUTA_KMEANS_OUT = "../data_kmeans"
RUTA_FIGURES = "../figures"

def generar_mapa_automatico():
    print("==========================================================")
    print("Generando mapa de clasificación con k automático")
    print("==========================================================")
    print("\n--- 1. Leyendo el valor de 'k' óptimo guardado ---")
    ruta_archivo_k = os.path.join(RUTA_KMEANS_OUT, 'k_optimo.txt')
    try:
        with open(ruta_archivo_k, 'r') as f:
            k_leido = int(f.read().strip())
        print(f"Valor de 'k' encontrado: {k_leido}")
    except Exception as e:
        print(f"¡ERROR! No se pudo leer el archivo k_optimo.txt: {e}")
        return

    print("\n--- 2. Cargando Componentes Principales ---")
    pca_ds = xr.open_dataset(os.path.join(RUTA_PCA_IN, 'componentes_principales.nc'))
    
    datos_apilados = pca_ds.to_array(dim='componente').stack(punto=('lat', 'lon')).transpose('punto', 'componente')
    indices_validos = ~np.isnan(datos_apilados).any(axis=1)
    matriz_limpia = datos_apilados.values[indices_validos]

    print(f"\n--- 3. Aplicando K-means con {k_leido} clústeres ---")
    kmeans = KMeans(n_clusters=k_leido, random_state=42, n_init='auto')
    clusters = kmeans.fit_predict(matriz_limpia)
    
    print("\n--- 3b. Generando gráfico de dispersión (Scatter Plot) ---")
    try:
        # Extraemos los dos primeros componentes principales para la visualización
        # matriz_limpia tiene forma (n_puntos_validos, n_componentes)
        pc1_values = matriz_limpia[:, 0]
        pc2_values = matriz_limpia[:, 1]
        
        plt.figure(figsize=(12, 8))
        
        # Usamos 'scatter' y coloreamos según la variable 'clusters'
        # Usamos 'tab20' para que coincida con el mapa
        # 's=1' hace que los puntos sean pequeños (útil si hay muchos)
        scatter = plt.scatter(
            pc1_values, 
            pc2_values, 
            c=clusters, 
            cmap='tab20', 
            s=1, 
            alpha=0.5 
        )
        
        # Añadimos una barra de color
        cbar = plt.colorbar(scatter, ticks=np.arange(k_leido))
        cbar.set_label('ID del Clúster')
        
        plt.title(f'Visualización de Clústeres K-means (k={k_leido})')
        plt.xlabel('Componente Principal 1')
        plt.ylabel('Componente Principal 2')
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Guardamos la figura
        ruta_figura_scatter = os.path.join(RUTA_FIGURES, f'scatter_clasificacion_k{k_leido}.png')
        plt.savefig(ruta_figura_scatter, dpi=300, bbox_inches='tight')
        plt.close() # Cerramos la figura para liberar memoria y no interferir con el mapa
        
        print(f"¡Imagen del scatter plot guardada en: {ruta_figura_scatter}!")

    except Exception as e:
        print(f"\n¡ERROR AL GENERAR EL SCATTER PLOT! {e}")

    
    print("\n--- 4. Guardando el mapa NetCDF final ---")
    mapa_clusters_array = np.full(datos_apilados.shape[0], np.nan)
    mapa_clusters_array[indices_validos] = clusters
    
    mapa_da = xr.DataArray(mapa_clusters_array, coords={'punto': datos_apilados.coords['punto']}, dims=('punto',)).unstack('punto')
    mapa_ds = mapa_da.to_dataset(name='climate_class')
    mapa_ds.attrs['description'] = f'Mapa de clasificación climática global con {k_leido} clústeres (K-means).'
    
    ruta_salida_netcdf = os.path.join(RUTA_KMEANS_OUT, f'mapa_clasificacion_k{k_leido}.nc')
    mapa_ds.to_netcdf(ruta_salida_netcdf)
    print(f"Mapa de datos guardado en: {ruta_salida_netcdf}")

    print("\n--- 5. Generando y guardando imagen del mapa ---")
    try:
        lats = mapa_ds['lat'].values
        lons = mapa_ds['lon'].values
        data = mapa_ds['climate_class'].values
        
        cyclic_data, cyclic_lons = add_cyclic_point(data, coord=lons)
        
        plt.figure(figsize=(15, 8))
        ax = plt.axes(projection=ccrs.Robinson())
        ax.coastlines()
        ax.gridlines(draw_labels=False, linestyle='--', alpha=0.5)

        # Definimos los niveles para que los colores sean discretos
        levels = np.arange(-0.5, k_leido, 1)
        
        contour = ax.contourf(
            cyclic_lons, lats, cyclic_data,
            levels=levels,
            transform=ccrs.PlateCarree(),
            cmap='tab20' # Usamos un colormap con colores bien diferenciados
        )
        
        # La barra de color necesita ajustarse para 'contourf'
        cbar = plt.colorbar(contour, ax=ax, orientation='vertical', shrink=0.8)
        # Ponemos las etiquetas en el centro de cada color
        tick_locs = np.arange(0, k_leido)
        cbar.set_ticks(tick_locs)
        cbar.set_ticklabels(tick_locs)
        cbar.set_label('Zona Climática')

        ax.set_title(f'Clasificación Climática Global (k={k_leido})', fontsize=16)
        
        ruta_figura_mapa = os.path.join(RUTA_FIGURES, f'mapa_clasificacion_k{k_leido}.png')
        plt.savefig(ruta_figura_mapa, dpi=300, bbox_inches='tight')
        print(f"¡Imagen del mapa guardada en: {ruta_figura_mapa}!")
        print("\n¡Proceso de clasificación finalizado con éxito!")

    except Exception as e:
        print(f"\n¡ERROR AL GENERAR LA IMAGEN! Ocurrió un problema durante el ploteo: {e}")

if __name__ == "__main__":
    generar_mapa_automatico()
