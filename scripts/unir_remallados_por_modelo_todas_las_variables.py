# -*- coding: utf-8 -*-
"""
SCRIPT PARA UNIR ARCHIVOS REMALLADOS POR MODELO

Instrucciones:
1. Ejecuta este script DESPUÉS de haber remallado los archivos con 
   'remallar_a_grid_fijo.py'.
2. Lee de la carpeta 'data_remallada/[variable]' y guarda los resultados
   en 'data_unida/[variable]'.
3. Procesa 'pr', 'tasmax' y 'tasmin' en una sola ejecución.
"""

# 1. Importar librerías
import xarray as xr
import os
import glob
from collections import defaultdict

# ==============================================================================
# >> CONFIGURACIÓN <<
# ==============================================================================
VARIABLES_A_PROCESAR = ["pr", "tasmax", "tasmin"]
# ==============================================================================

# 2. Definir rutas
RUTA_REMALLADA_BASE = "../data_remallada"
RUTA_UNIDA_BASE = "../data_unida"  # Carpeta final para los datos listos

# 3. Función principal
def unir_modelos(nombre_variable, ruta_in, ruta_out):
    """
    Une los archivos previamente remallados, agrupándolos por modelo.
    """
    print("==========================================================")
    print(f"Iniciando unión de archivos para: [ {nombre_variable.upper()} ]")
    print(f"Leyendo datos de: {ruta_in}")
    print("==========================================================")
    os.makedirs(ruta_out, exist_ok=True)

    # Buscar todos los archivos remallados
    patron_busqueda = os.path.join(ruta_in, "*_regrid.nc")
    lista_archivos = glob.glob(patron_busqueda)

    if not lista_archivos:
        print(f"¡ERROR! No se encontraron archivos '*_regrid.nc' en '{ruta_in}'.")
        print("Asegúrate de haber ejecutado primero el script de remallado.")
        return

    print(f"Se encontraron {len(lista_archivos)} archivos remallados.")

    # Agrupar archivos por modelo
    archivos_por_modelo = defaultdict(list)
    for ruta_archivo in lista_archivos:
        nombre_archivo = os.path.basename(ruta_archivo)
        modelo = nombre_archivo.split('_')[2]  # El nombre del modelo sigue estando en la 3ª posición
        archivos_por_modelo[modelo].append(ruta_archivo)

    print("\nArchivos agrupados por modelo:")
    for modelo, archivos in archivos_por_modelo.items():
        print(f"  -> Modelo: {modelo} ({len(archivos)} archivos)")

    # Unir y guardar
    print("\n--- Uniendo y guardando archivos por modelo ---")
    for modelo, archivos_del_modelo in archivos_por_modelo.items():
        # El nombre final ya no necesita el sufijo '_regrid'
        nombre_salida = f"{nombre_variable}_{modelo}_unido.nc"
        ruta_salida_final = os.path.join(ruta_out, nombre_salida)
        
        print(f"  Procesando {modelo}... ", end="")
        try:
            # open_mfdataset une los archivos a lo largo de sus coordenadas (tiempo)
            with xr.open_mfdataset(archivos_del_modelo, combine='by_coords') as ds:
                ds.to_netcdf(ruta_salida_final)
            print("¡Hecho!")
        except Exception as e:
            print(f"¡FALLÓ! Error: {e}")

    print("\n----------------------------------------------------------")
    print(f"Proceso de unión para '{nombre_variable.upper()}' completado.")
    print(f"Archivos finales guardados en '{ruta_out}'")
    print("----------------------------------------------------------\n")


# 4. Ejecutar
if __name__ == "__main__":
    print("--- INICIANDO UNIÓN DE ARCHIVOS (TODAS LAS VARIABLES) ---")
    for variable in VARIABLES_A_PROCESAR:
        ruta_entrada_especifica = os.path.join(RUTA_REMALLADA_BASE, variable)
        ruta_salida_especifica = os.path.join(RUTA_UNIDA_BASE, variable)
        unir_modelos(variable, ruta_entrada_especifica, ruta_salida_especifica)
    print("--- UNIÓN DE TODAS LAS VARIABLES COMPLETADA ---")