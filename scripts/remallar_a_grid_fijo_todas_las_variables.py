# -*- coding: utf-8 -*-
"""
SCRIPT DE REMALLADO CON MÁSCARA DE TIERRA DETALLADA

Cambio:
1. Detecta longitudes 0-360 y las convierte a -180-180.
2. Carga la máscara detallada 'landsea.nc'.
3. Remalla la máscara a la grid de destino.
4. Aplica la máscara, conservando tierra (1), islas (3) y hielo (4).
   El océano (0) y los lagos (2) se convierten en NaN.
5. Procesa 'pr', 'tasmax' y 'tasmin' en una sola ejecución.
"""
import xarray as xr
import os
import glob
import numpy as np

# --- CONFIGURACIÓN DE DATOS ---
VARIABLES_A_PROCESAR = ["pr", "tasmax", "tasmin"]
GRID_LAT = 64
GRID_LON = 128


# ¡IMPORTANTE! Asegurar de colocar el archivo 'landsea.nc'
# en la carpeta '../data_auxiliar/' para que este script lo encuentre.
RUTA_MASCARA = "../data_auxiliar/landsea.nc" 
# Basado en la metadata del archivo, el nombre de la variable es 'LSMASK'
VARIABLE_MASCARA = "LSMASK" 
# Valores que queremos MANTENER (Tierra, Islas, Hielo)
VALORES_VALIDOS = [1, 3, 4] 

# --- RUTAS ---
RUTA_DATOS_BASE = "../data"
RUTA_REMALLADA_BASE = "../data_remallada"

def remallar_corregido(nombre_variable, ruta_in, ruta_out, grid_ref_ds, mascara_remallada):
    print("==========================================================")
    print(f"Iniciando remallado CORREGIDO para: [ {nombre_variable.upper()} ]")
    print(f"Resolución objetivo FIJA: {GRID_LAT}x{GRID_LON}")
    print("==========================================================")
    os.makedirs(ruta_out, exist_ok=True)

    lista_archivos = glob.glob(os.path.join(ruta_in, f"{nombre_variable}_*.nc"))
    if not lista_archivos:
        print(f"¡ERROR! No se encontraron archivos en '{ruta_in}'.")
        return

    print(f"\n--- Procesando, remallando y aplicando máscara a cada archivo ---")
    total_archivos = len(lista_archivos)
    for i, ruta_archivo in enumerate(lista_archivos):
        nombre_original = os.path.basename(ruta_archivo)
        nombre_salida = nombre_original.replace(".nc", "_regrid.nc")
        ruta_salida_final = os.path.join(ruta_out, nombre_salida)
        
        print(f"  ({i+1}/{total_archivos}) Procesando: {nombre_original}... ", end="")

        try:
            with xr.open_dataset(ruta_archivo) as ds_original:
                if 'time_bnds' in ds_original.variables:
                    ds_original = ds_original.drop_vars('time_bnds')
                # 1. Corregir longitud si es 0-360
                if ds_original['lon'].max() > 180:
                    print("Convirtiendo lon... ", end="")
                    ds_original.coords['lon'] = (ds_original.coords['lon'] + 180) % 360 - 180
                    ds_original = ds_original.sortby(ds_original.lon)

                # 2. Interpolar al grid de referencia
                print("Remallando... ", end="")
                ds_procesado = ds_original.interp(lat=grid_ref_ds.lat, lon=grid_ref_ds.lon)

                # 3. Aplicar máscara
                print("Aplicando máscara... ", end="")
                # Donde la máscara tenga un valor en VALORES_VALIDOS, mantenemos los datos.
                # Donde no (0=ocean, 2=lake), se reemplaza con NaN.
                ds_procesado = ds_procesado.where(mascara_remallada.isin(VALORES_VALIDOS))

                # 4. Guardar
                ds_procesado.to_netcdf(ruta_salida_final)
                print("¡Hecho!")
        except Exception as e:
            print(f"¡FALLÓ! Error: {e}")

    print(f"\nRemallado para '{nombre_variable.upper()}' completado.")
    print("Todos los archivos de salida ahora contienen NaN en las zonas de océano y lagos.")

if __name__ == "__main__":
    
    # --- 1. Crear grid de referencia (-180 a 180) ---
    print("--- Creando grid de referencia global (-180 a 180) ---")
    new_lat = np.linspace(-90, 90, GRID_LAT, endpoint=True)
    new_lon = np.linspace(-180, 180, GRID_LON, endpoint=True)
    grid_ref_ds = xr.Dataset({'lat': ('lat', new_lat), 'lon': ('lon', new_lon)})

    # --- 2. Cargar y remallar máscara de tierra (se hace una sola vez) ---
    print(f"\n--- Cargando y remallando máscara de tierra detallada ---")
    try:
        with xr.open_dataset(RUTA_MASCARA) as ds_mask:
            # Verificamos si la MÁSCARA usa lon 0-360 y la convertimos
            if ds_mask['lon'].max() > 180:
                print("Convirtiendo longitudes de la MÁSCARA (0-360 -> -180-180)...")
                ds_mask.coords['lon'] = (ds_mask.coords['lon'] + 180) % 360 - 180
                ds_mask = ds_mask.sortby(ds_mask.lon)
            # Seleccionamos la variable 'LSMASK'
            mascara_original = ds_mask[VARIABLE_MASCARA]
            
            # Remallamos la máscara a nuestra grid de destino
            # Usamos 'nearest' (vecino más cercano) que es lo mejor para máscaras
            mascara_remallada = mascara_original.interp(
                lat=grid_ref_ds.lat, 
                lon=grid_ref_ds.lon,
                method='nearest'
            )
            
            # Aseguramos que la máscara esté cargada en memoria
            mascara_remallada.load()
            print("¡Máscara de tierra cargada y remallada exitosamente!")
            print(f"   Se conservarán los pixeles con valores: {VALORES_VALIDOS}")

    except Exception as e:
        print(f"¡ERROR FATAL al cargar o remallar la máscara!: {e}")
        print(f"Verifica que '{RUTA_MASCARA}' exista y que '{VARIABLE_MASCARA}' sea correcto. Abortando.")
        # Si la máscara falla, no podemos continuar
        exit()

    # --- 3. Iterar y procesar cada variable ---
    print("\n--- INICIANDO REMALLADO PARA TODAS LAS VARIABLES ---")
    for variable in VARIABLES_A_PROCESAR:
        ruta_entrada_especifica = os.path.join(RUTA_DATOS_BASE, variable)
        ruta_salida_especifica = os.path.join(RUTA_REMALLADA_BASE, variable)
        
        # Pasamos el grid y la máscara ya calculados a la función
        remallar_corregido(
            variable, 
            ruta_entrada_especifica, 
            ruta_salida_especifica,
            grid_ref_ds,
            mascara_remallada
        )
    
    print("\n--- REMALLADO DE TODAS LAS VARIABLES COMPLETADO ---")