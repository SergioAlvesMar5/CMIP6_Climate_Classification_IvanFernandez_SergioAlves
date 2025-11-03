# -*- coding: utf-8 -*-
"""
SCRIPT PARA CREAR EL ENSEMBLE MULTI-MODELO

Instrucciones:
1. Se ejecuta como el paso final del preprocesamiento de datos.
2. Lee todos los archivos de climatología de los modelos desde 
   'data_climatologia/[variable]'.
3. Calcula el promedio de todos los modelos.
4. Guarda el resultado en un único archivo en 'data_ensemble/'.
5. Procesa 'pr', 'tasmax' y 'tasmin' en una sola ejecución.
"""

# 1. Importar librerías
import xarray as xr
import os
import glob

# ==============================================================================
# >> CONFIGURACIÓN <<
# ==============================================================================
VARIABLES_A_PROCESAR = ["pr", "tasmax", "tasmin"]
# ==============================================================================

# 2. Definir rutas
RUTA_CLIMATOLOGIA_BASE = "../data_climatologia"
RUTA_ENSEMBLE_BASE = "../data_ensemble" # Carpeta final para los datos listos para el análisis
RUTA_SALIDA = RUTA_ENSEMBLE_BASE # Guardaremos directamente en la carpeta raíz

# 3. Función principal
def crear_ensemble(nombre_variable, ruta_in, ruta_out):
    """
    Calcula y guarda el ensemble multi-modelo para una variable.
    """
    print("==========================================================")
    print(f"Creando ENSEMBLE para: [ {nombre_variable.upper()} ]")
    print(f"Leyendo datos de: {ruta_in}")
    print("==========================================================")
    os.makedirs(ruta_out, exist_ok=True)

    # Buscar todos los archivos de climatología
    patron_busqueda = os.path.join(ruta_in, "*_climatologia.nc")
    lista_archivos = sorted(glob.glob(patron_busqueda))

    if not lista_archivos:
        print(f"¡ERROR! No se encontraron archivos '*_climatologia.nc' en '{ruta_in}'.")
        return
    
    if len(lista_archivos) < 2:
        print(f"¡ADVERTENCIA! Solo se encontró {len(lista_archivos)} archivo. No se puede crear un ensemble.")
        return

    print(f"Se encontraron {len(lista_archivos)} modelos para promediar.")

    # 4. Abrir todos los archivos y calcular el promedio
    nombre_salida = f"{nombre_variable}_ensemble_climatologia.nc"
    ruta_salida_final = os.path.join(ruta_out, nombre_salida)
    
    print(f"\n--- Calculando promedio multi-modelo... ---")
    try:
        # Abrimos todos los datasets y los concatenamos a lo largo de una nueva
        # dimensión que llamaremos 'modelo'. Esto nos crea un "cubo" de datos.
        datasets = [xr.open_dataset(f) for f in lista_archivos]
        ensemble_data = xr.concat(datasets, dim='modelo')

        # Calculamos la media a lo largo de la nueva dimensión 'modelo'
        ensemble_mean = ensemble_data.mean(dim='modelo')
        
        # Añadimos metadatos
        ensemble_mean.attrs['history'] = f'Multi-model ensemble mean calculated from {len(lista_archivos)} models.'
        ensemble_mean.attrs['variable'] = nombre_variable
        
        # Guardamos el resultado final
        ensemble_mean.to_netcdf(ruta_salida_final)
        print(f"¡Hecho! Ensemble guardado en: {ruta_salida_final}")

    except Exception as e:
        print(f"¡FALLÓ! Error: {e}")

    print("\n----------------------------------------------------------")
    print(f"¡Creación de ensemble para '{nombre_variable.upper()}' completada!")
    print("----------------------------------------------------------\n")

# 5. Ejecutar
if __name__ == "__main__":
    print("--- INICIANDO CREACIÓN DE ENSEMBLES (TODAS LAS VARIABLES) ---")
    for variable in VARIABLES_A_PROCESAR:
        ruta_entrada_especifica = os.path.join(RUTA_CLIMATOLOGIA_BASE, variable)
        # La ruta de salida es la misma carpeta base para todas
        crear_ensemble(variable, ruta_entrada_especifica, RUTA_SALIDA)
        
    print("--- PREPROCESAMIENTO DE DATOS COMPLETADO (TODOS LOS ENSEMBLES CREADOS) ---")