# -*- coding: utf-8 -*-
"""
SCRIPT DE VERIFICACIÓN DE CONSISTENCIA DE DATOS ORIGINALES

Instrucciones:
1. Ejecuta este script ANTES de unir los archivos.
2. Asegúrate de que los archivos originales estén en sus carpetas
   correspondientes dentro de 'data/' (ej. 'data/prsn/').
3. El script verifica 'pr', 'tasmax' y 'tasmin' en una sola ejecución.
"""

# 1. Importar librerías
import xarray as xr
import os
import glob
import pandas as pd
from collections import defaultdict

# ==============================================================================
# >> CONFIGURACIÓN <<
# >> El script ahora procesará TODAS las variables de esta lista <<
# ==============================================================================
VARIABLES_A_PROCESAR = ["pr", "tasmax", "tasmin"]
# ==============================================================================

# 2. Definir rutas
RUTA_DATOS_BASE = "../data"

# 3. Función principal de verificación
def verificar_originales(nombre_variable, ruta_in):
    """
    Verifica la consistencia de los archivos originales para una variable,
    agrupándolos por modelo.
    """
    print("==========================================================")
    print(f"Verificando datos ORIGINALES para: [ {nombre_variable.upper()} ]")
    print(f"Buscando archivos en: {ruta_in}")
    print("==========================================================")

    # Buscar todos los archivos .nc
    patron_busqueda = os.path.join(ruta_in, f"{nombre_variable}_*.nc")
    lista_archivos_total = sorted(glob.glob(patron_busqueda))

    if not lista_archivos_total:
        print(f"\n¡ERROR! No se encontraron archivos en '{ruta_in}'.")
        return

    print(f"Se encontraron {len(lista_archivos_total)} archivos en total. Agrupando por modelo...")

    # Agrupar archivos por modelo
    archivos_por_modelo = defaultdict(list)
    for ruta in lista_archivos_total:
        modelo = os.path.basename(ruta).split('_')[2]
        archivos_por_modelo[modelo].append(ruta)
    
    # Almacenaremos la información resumida de cada modelo para el informe final
    informe_resumen = []
    todos_consistentes = True

    # 4. Verificar consistencia DENTRO de cada modelo
    print("\n--- 1. Verificando consistencia interna de cada modelo ---")
    for modelo, lista_archivos in archivos_por_modelo.items():
        print(f"\nAnalizando Modelo: [ {modelo} ] ({len(lista_archivos)} archivos)")
        
        # Leemos las características del primer archivo como referencia
        with xr.open_dataset(lista_archivos[0]) as ds_ref:
            grid_ref = f"{len(ds_ref.lat)}x{len(ds_ref.lon)}"
            unidades_ref = ds_ref[nombre_variable].attrs.get('units', 'N/A')
            calendario_ref = ds_ref.time.encoding.get('calendar', 'N/A')

        # Comparamos el resto de archivos con la referencia
        consistente = True
        for i in range(1, len(lista_archivos)):
            with xr.open_dataset(lista_archivos[i]) as ds_comp:
                grid_comp = f"{len(ds_comp.lat)}x{len(ds_comp.lon)}"
                unidades_comp = ds_comp[nombre_variable].attrs.get('units', 'N/A')
                if grid_comp != grid_ref or unidades_comp != unidades_ref:
                    print(f"  ¡INCONSISTENCIA ENCONTRADA en {os.path.basename(lista_archivos[i])}!")
                    consistente = False
                    todos_consistentes = False
                    break
        
        if consistente:
            print("  Todos los archivos de este modelo son consistentes entre sí.")
            informe_resumen.append({
                'Modelo': modelo,
                'Grid (lat x lon)': grid_ref,
                'Unidades': unidades_ref,
                'Calendario': calendario_ref,
                'Nº Archivos': len(lista_archivos),
                'Consistencia Interna': 'OK'
            })
        else:
            informe_resumen.append({
                'Modelo': modelo, 'Grid (lat x lon)': 'INCONSISTENTE', 'Unidades': 'INCONSISTENTE',
                'Calendario': 'INCONSISTENTE', 'Nº Archivos': len(lista_archivos), 
                'Consistencia Interna': 'FALLÓ'
            })

    if not todos_consistentes:
        print("\n¡ATENCIÓN! Se encontraron inconsistencias DENTRO de los archivos de un mismo modelo.")
        print("Revisa los mensajes de error de arriba antes de continuar.")
        # Mostramos la tabla aunque haya fallos para ayudar a depurar
        df_informe = pd.DataFrame(informe_resumen)
        print("\n--- INFORME DE MODELOS ---")
        print(df_informe.to_string())
        return # Detenemos el análisis más profundo si hay fallos internos

    # 5. Si todo fue consistente internamente, se genera el informe comparativo
    print("\n\n--- 2. Informe de consistencia ENTRE modelos ---")
    df_informe = pd.DataFrame(informe_resumen)
    print(df_informe.to_string())

    print("\n--- RESUMEN DEL ANÁLISIS GLOBAL ---")
    if df_informe['Grid (lat x lon)'].nunique() == 1:
        print(" **Grid Espacial**: ¡Perfecto! Todos los modelos comparten el mismo grid.")
    else:
        print(" **Grid Espacial**: ¡Atención! Se detectaron diferentes grids. Será necesario un 'regridding'.")
        print("   Grids encontrados:", df_informe['Grid (lat x lon)'].unique().tolist())
        
    if df_informe['Unidades'].nunique() == 1:
        print(" **Unidades**: ¡Genial! Todos los modelos usan las mismas unidades.")
    else:
        print(" **Unidades**: ¡Crítico! Unidades diferentes detectadas. Hay que convertir.")
        print("   Unidades encontradas:", df_informe['Unidades'].unique().tolist())
    
    print("\n----------------------------------------------------------")
    print(f"Verificación de originales para '{nombre_variable.upper()}' completada.")
    print("----------------------------------------------------------\n")


# 6. Ejecutar el script
if __name__ == "__main__":
    print("--- INICIANDO VERIFICACIÓN DE DATOS ORIGINALES (TODAS LAS VARIABLES) ---")
    for variable in VARIABLES_A_PROCESAR:
        ruta_entrada_especifica = os.path.join(RUTA_DATOS_BASE, variable)
        verificar_originales(variable, ruta_entrada_especifica)
    print("--- VERIFICACIÓN DE TODAS LAS VARIABLES COMPLETADA ---")