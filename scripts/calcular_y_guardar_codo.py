# -*- coding: utf-8 -*-
"""
CALCULA Y GUARDA EL K ÓPTIMO (MÉTODO DEL CODO)

Guarda el 'k' óptimo detectado en un archivo para que el
        siguiente script pueda usarlo automáticamente.
"""
import xarray as xr
import os
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from kneed import KneeLocator

# --- CONFIGURACIÓN ---
K_RANGE = range(2, 21)

# --- RUTAS ---
RUTA_PCA_IN = "../data_pca"
RUTA_KMEANS_OUT = "../data_kmeans" # Carpeta para guardar el k y los datos
RUTA_FIGURES = "../figures"

def calcular_y_guardar_codo():
    print("==========================================================")
    print("Paso 1: Calculando y guardando el k óptimo")
    print("==========================================================")
    os.makedirs(RUTA_KMEANS_OUT, exist_ok=True)
    os.makedirs(RUTA_FIGURES, exist_ok=True)

    print("\n--- Cargando Componentes Principales ---")
    pca_ds = xr.open_dataset(os.path.join(RUTA_PCA_IN, 'componentes_principales.nc'))
    
    datos_apilados = pca_ds.to_array(dim='componente').stack(punto=('lat', 'lon')).transpose('punto', 'componente')
    indices_validos = ~np.isnan(datos_apilados).any(axis=1)
    matriz_limpia = datos_apilados.values[indices_validos]

    print(f"\n--- Probando k desde {K_RANGE.start} hasta {K_RANGE.stop-1} ---")
    inercias = [
        KMeans(n_clusters=k, random_state=42, n_init='auto').fit(matriz_limpia).inertia_
        for k in K_RANGE
    ]
        
    print("\n--- Generando el gráfico del codo ---")
    plt.figure(figsize=(12, 7))
    plt.plot(K_RANGE, inercias, 'bo-', markersize=8, linewidth=2)
    plt.xlabel('Número de Clústeres (k)'); plt.ylabel('Inercia')
    plt.title('Método del Codo para Determinar k Óptimo')
    plt.xticks(K_RANGE); plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(RUTA_FIGURES, 'metodo_del_codo.png'), dpi=300)
    
    print("\n--- Detectando y guardando el 'k' óptimo ---")
    kneedle = KneeLocator(list(K_RANGE), inercias, S=1.0, curve='convex', direction='decreasing')
    k_optimo = kneedle.elbow

    if k_optimo:
        # Guardar el valor en un archivo de texto
        ruta_archivo_k = os.path.join(RUTA_KMEANS_OUT, 'k_optimo.txt')
        with open(ruta_archivo_k, 'w') as f:
            f.write(str(k_optimo))
        
        print("\n==========================================================")
        print(f"El 'k' óptimo sugerido es: {k_optimo}")
        print(f"   Este valor ha sido guardado en: {ruta_archivo_k}")
        print("==========================================================")
    else:
        print("\nNo se pudo determinar un 'k' óptimo. Revisa el gráfico manualmente.")

if __name__ == "__main__":
    calcular_y_guardar_codo()