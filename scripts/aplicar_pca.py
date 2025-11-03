# -*- coding: utf-8 -*-
"""
SCRIPT PARA APLICAR ANÁLISIS DE COMPONENTES PRINCIPALES (PCA)

Instrucciones:
1. Se ejecuta después de haber creado los ensembles.
2. Carga todas las variables de la carpeta 'data_ensemble'.
3. Prepara los datos: los combina, aplana y estandariza.
4. Aplica PCA para reducir la dimensionalidad.
5. Guarda los componentes principales y el modelo PCA entrenado.
"""

# 1. Importar librerías
import xarray as xr
import os
import glob
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib # Para guardar el modelo PCA

# ==============================================================================
# >> CONFIGURACIÓN <<
# ==============================================================================
VARIABLES_CLIMATICAS = ["pr", "tasmax", "tasmin"]
VARIANZA_EXPLICADA_OBJETIVO = 0.90 # 90%
# ==============================================================================

# 2. Definir rutas
RUTA_ENSEMBLE = "../data_ensemble"
RUTA_PCA_SALIDA = "../data_pca"

# 3. Función principal
def ejecutar_pca():
    """
    Orquesta todo el proceso de carga, preparación y aplicación de PCA.
    """
    print("==========================================================")
    print("Iniciando Reducción de Dimensionalidad con PCA")
    print("==========================================================")
    os.makedirs(RUTA_PCA_SALIDA, exist_ok=True)

    # 4. Cargar y combinar todos los datasets de ensemble
    print(f"\n--- 1. Cargando datos de las variables: {VARIABLES_CLIMATICAS} ---")
    

    # Cargamos cada dataset, seleccionamos ÚNICAMENTE la variable de datos
    # principal y descartamos el resto (como las 'bnds').
    datasets = []
    for var in VARIABLES_CLIMATICAS:
        ruta_archivo = os.path.join(RUTA_ENSEMBLE, f"{var}_ensemble_climatologia.nc")
        with xr.open_dataset(ruta_archivo) as ds:
            # Nos aseguramos de quedarnos solo con la variable principal
            datasets.append(ds[[var]])
    
    # Fusionamos los datasets ya limpios.
    datos_combinados = xr.merge(datasets, compat='override')
    datos_combinados = datos_combinados.sortby('lon')
    
    print("¡Datos cargados y combinados!")
    print("\nDataset combinado:")
    print(datos_combinados)

    # 5. Preparar los datos para PCA
    print("\n--- 2. Preparando la matriz de características ---")
    datos_apilados = datos_combinados.to_array(dim='variable').stack(punto=('lat', 'lon'))
    datos_apilados = datos_apilados.transpose('punto', 'variable', 'month')
    
    n_puntos, n_vars, n_meses = datos_apilados.shape
    matriz_features = datos_apilados.values.reshape(n_puntos, n_vars * n_meses)
    
    indices_validos = ~np.isnan(matriz_features).any(axis=1)
    matriz_limpia = matriz_features[indices_validos]
    
    print(f"Matriz creada. Forma: {matriz_limpia.shape} (puntos x características)")

    # 6. Estandarizar los datos
    print("\n--- 3. Estandarizando los datos (media 0, desviación estándar 1) ---")
    scaler = StandardScaler()
    matriz_estandarizada = scaler.fit_transform(matriz_limpia)
    
    # 7. Aplicar PCA
    print(f"\n--- 4. Aplicando PCA para capturar >= {VARIANZA_EXPLICADA_OBJETIVO*100}% de la varianza ---")
    pca = PCA(n_components=VARIANZA_EXPLICADA_OBJETIVO)
    componentes_principales = pca.fit_transform(matriz_estandarizada)
    
    n_componentes = pca.n_components_
    print(f"PCA completado. Se seleccionaron {n_componentes} componentes.")
    
    varianza_acumulada = np.cumsum(pca.explained_variance_ratio_)
    print("Varianza explicada por cada componente:")
    for i, var in enumerate(pca.explained_variance_ratio_):
        print(f"  CP {i+1}: {var*100:.2f}% (Acumulada: {varianza_acumulada[i]*100:.2f}%)")

    # 8. Guardar los resultados
    print("\n--- 5. Guardando los resultados ---")
    output_array = np.full((n_puntos, n_componentes), np.nan)
    output_array[indices_validos, :] = componentes_principales
    
    # Creamos un DataArray con las dimensiones correctas para desapilar
    coords_para_output = {
        'punto': datos_apilados.coords['punto'],
        'componente': range(1, n_componentes + 1)
    }
    output_da = xr.DataArray(output_array, coords=coords_para_output, dims=('punto', 'componente'))
    
    # Desapilamos para volver a la forma de mapa
    mapa_componentes = output_da.unstack('punto')
    
    # Guardamos en un Dataset
    pca_ds = mapa_componentes.to_dataset(dim='componente')
    # Renombramos las variables para que sean más claras
    pca_ds = pca_ds.rename({i: f'CP_{i}' for i in range(1, n_componentes + 1)})

    ruta_salida_netcdf = os.path.join(RUTA_PCA_SALIDA, 'componentes_principales.nc')
    pca_ds.to_netcdf(ruta_salida_netcdf)
    print(f"Componentes guardados en: {ruta_salida_netcdf}")
    
    ruta_salida_modelo = os.path.join(RUTA_PCA_SALIDA, 'pca_model.joblib')
    joblib.dump({'pca': pca, 'scaler': scaler, 'indices_validos': indices_validos}, ruta_salida_modelo)
    print(f"Modelo PCA, scaler e índices guardados en: {ruta_salida_modelo}")

if __name__ == "__main__":
    ejecutar_pca()