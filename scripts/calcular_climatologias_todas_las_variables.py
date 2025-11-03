# -*- coding: utf-8 -*-
"""
SCRIPT PARA CALCULAR CLIMATOLOGÍAS MENSUALES

Instrucciones:
1. Se ejecuta después de haber unido los archivos por modelo.
2. Lee los datos de 'data_unida/[variable]'.
3. Calcula la media para cada mes del año (climatología) sobre el
   periodo temporal completo.
4. Guarda los resultados (12 pasos de tiempo) en 'data_climatologia/[variable]'.
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
RUTA_UNIDA_BASE = "../data_unida"
RUTA_CLIMATOLOGIA_BASE = "../data_climatologia" # Carpeta final para las medias

# 3. Función principal
def calcular_climatologia(nombre_variable, ruta_in, ruta_out):
    """
    Calcula y guarda la climatología mensual para cada modelo de una variable.
    """
    print("==========================================================")
    print(f"Calculando climatologías para: [ {nombre_variable.upper()} ]")
    print(f"Leyendo datos de: {ruta_in}")
    print("==========================================================")
    os.makedirs(ruta_out, exist_ok=True)

    # Buscar todos los archivos unidos
    patron_busqueda = os.path.join(ruta_in, "*_unido.nc")
    lista_archivos = glob.glob(patron_busqueda)

    if not lista_archivos:
        print(f"¡ERROR! No se encontraron archivos '*_unido.nc' en '{ruta_in}'.")
        print("Asegúrate de haber ejecutado el script de unión primero.")
        return

    print(f"Se encontraron {len(lista_archivos)} archivos de modelos para procesar.")

    # 4. Calcular climatología para cada archivo
    print("\n--- Calculando y guardando climatologías ---")
    for ruta_archivo in lista_archivos:
        nombre_original = os.path.basename(ruta_archivo)
        # Cambiamos el sufijo para reflejar el nuevo contenido
        nombre_salida = nombre_original.replace("_unido.nc", "_climatologia.nc")
        ruta_salida_final = os.path.join(ruta_out, nombre_salida)
        
        print(f"  Procesando: {nombre_original}... ", end="")
        try:
            with xr.open_dataset(ruta_archivo) as ds:
                # La operación clave: agrupar por mes y calcular la media
                climatologia_mensual = ds.groupby('time.month').mean('time')
                
                # Añadir metadatos para aclarar qué es este archivo
                climatologia_mensual.attrs['history'] = 'Calculated monthly climatology (mean over all years).'
                
                # Guardar el resultado
                climatologia_mensual.to_netcdf(ruta_salida_final)
                print("¡Hecho!")

        except Exception as e:
            print(f"¡FALLÓ! Error: {e}")

    print("\n----------------------------------------------------------")
    print(f"Climatologías para '{nombre_variable.upper()}' calculadas.")
    print(f"Archivos finales guardados en '{ruta_out}'")
    print("----------------------------------------------------------\n")

# 5. Ejecutar
if __name__ == "__main__":
    print("--- INICIANDO CÁLCULO DE CLIMATOLOGÍAS (TODAS LAS VARIABLES) ---")
    for variable in VARIABLES_A_PROCESAR:
        ruta_entrada_especifica = os.path.join(RUTA_UNIDA_BASE, variable)
        ruta_salida_especifica = os.path.join(RUTA_CLIMATOLOGIA_BASE, variable)
        calcular_climatologia(variable, ruta_entrada_especifica, ruta_salida_especifica)
    print("--- CÁLCULO DE CLIMATOLOGÍAS COMPLETADO ---")