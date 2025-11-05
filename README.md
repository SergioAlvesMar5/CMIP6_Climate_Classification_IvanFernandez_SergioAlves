# CMIP6\_Climate\_Classification\_IvanFernandez\_SergioAlves

Este repositorio (`ProyectoOsos`) contiene un conjunto de scripts de Python diseñados para procesar datos de modelos climáticos (como CMIP6) y clasificarlos en zonas climáticas o hábitats distintos mediante técnicas de Machine Learning no supervisado (PCA y K-Means).

El pipeline completo realiza las siguientes operaciones:

1.  **Verificación de Datos:** Comprueba la consistencia de los archivos de entrada (grid, unidades).
2.  **Preprocesamiento:** Remalla (regridding) los datos a una grid común aplicando una máscara de tierra.
3.  **Agregación:** Une los datos por modelo, calcula las climatologías mensuales y crea un *ensemble* (promedio) multi-modelo.
4.  **Reducción de Dimensionalidad:** Aplica Análisis de Componentes Principales (PCA) sobre las variables climáticas (`pr`, `tasmax`, `tasmin`).
5.  **Clustering:**
      * Calcula el número óptimo de clústeres (`k`) usando el "Método del Codo".
      * Genera un mapa de clasificación global usando K-Means con el `k` óptimo.
6.  **Análisis de Hábitats:** Identifica los clústeres resultantes con hábitats de interés (ej. Oso Polar, Panda) basándose en puntos de muestra geográficos.

-----

## 📂 Estructura de Carpetas y Descarga de Datos

Para que los scripts funcionen correctamente, se espera la siguiente estructura de directorios (los scripts se encuentran en `ProyectoOsos/scripts/`):

```
ProyectoOsos/
├── data/
│   ├── instalacion_data.txt  (CONTIENE ENLACE GOOGLE DRIVE)
│   ├── pr/
│   ├── tasmax/
│   └── tasmin/
├── data_auxiliar/
│   └── landsea.nc
├── data_climatologia/
├── data_ensemble/
├── data_kmeans/
├── data_pca/
├── data_remallada/
│   └── instalacion_data_remallada.txt (CONTIENE ENLACE)
├── data_unida/
│   └── instalacion_data_unida.txt (CONTIENE ENLACE)
├── figures/
└── scripts/
    ├── ... (todos los scripts .py)
```

### ❗ Nota Importante sobre los Datos (Google Drive)

Debido al gran tamaño de los archivos NetCDF (`.nc`) iniciales, el **contenido** de las carpetas `data`, `data_remallada` y `data_unida` no está alojado en GitHub.

En su lugar, dentro de cada una de estas tres carpetas en el repositorio, encontrarás un archivo `.txt` (ej. `instalacion_data.txt`) que contiene un enlace de Google Drive.

**Instrucciones de descarga:**

1.  Navega a la carpeta correspondiente en este repositorio (ej. `ProyectoOsos/data/`).
2.  Abre el archivo `.txt` que se encuentra dentro.
3.  Copia el enlace de Google Drive y úsalo para descargar el archivo comprimido.
4.  Descomprime el contenido descargado dentro de esa misma carpeta para que el pipeline pueda encontrar los archivos (`.nc`).

Las carpetas de datos generados *después* del preprocesamiento (`data_climatologia`, `data_ensemble`, etc.) son mucho más pequeñas y sí están incluidas directamente en el repositorio.

-----

## 📦 Instalación

Se recomienda crear un entorno virtual (por ejemplo, con `conda` o `venv`) e instalar las dependencias.

```bash
pip install -r requirements.txt
```

El archivo `requirements.txt` debería contener, como mínimo:

```
numpy
pandas
xarray
scikit-learn
kneed
matplotlib
cartopy
joblib
```

-----

## 🚀 Recomendación de Ejecución

Aunque en el repositorio incluimos las carpetas de datos intermedios (`data_climatologia`, `data_ensemble`, etc.) resultantes de nuestra propia ejecución, **recomendamos ejecutar todo el pipeline desde el principio**.

Para ello, una vez descargados los datos iniciales (`data`, `data_remallada`, `data_unida` y `data_auxiliar`) siguiendo las instrucciones de la nota anterior, solo tienes que seguir el "Flujo de Ejecución" descrito a continuación para regenerar todos los resultados.

-----

## ⚙️ Flujo de Ejecución (Workflow)

Los scripts deben ejecutarse en un orden específico para que el pipeline funcione. **(Ejecutar desde la carpeta `ProyectoOsos/scripts/`)**

### Parte 1: Preprocesamiento de Datos

Se procesan las variables `pr`, `tasmax` y `tasmin` desde los datos crudos hasta un *ensemble* listo para el análisis.

```bash
# 1. Verificar consistencia de los datos originales (Opcional pero recomendado)
python verificar_datos_originales_todas_las_variables.py

# 2. Remallar todos los datos a una grid fija (usando data_auxiliar/landsea.nc)
python remallar_a_grid_fijo_todas_las_variables.py

# 3. Unir los archivos remallados (series temporales) por modelo
python unir_remallados_por_modelo_todas_las_variables.py

# 4. Calcular las climatologías mensuales (promedio de 12 meses)
python calcular_climatologias_todas_las_variables.py

# 5. Crear el ensemble multi-modelo (promedio de todos los modelos)
python crear_ensemble_todas_las_variables.py
```

### Parte 2: Análisis de Machine Learning (Automático)

Este flujo utiliza el "Método del Codo" para determinar automáticamente el mejor número de clústeres (`k`).

```bash
# 6. Aplicar PCA sobre los datos del ensemble
python aplicar_pca.py

# 7. Calcular el 'k' óptimo con el Método del Codo y guardarlo
python calcular_y_guardar_codo.py

# 8. Generar el mapa K-Means usando el 'k' óptimo guardado
python generar_mapa_kmeans.py

# 9. Analizar el mapa K-Means e identificar los hábitats
python analizar_y_mapear_habitats_pandaversion.py
```

### 📈 Resultados (Workflow Automático)

  * `../figures/metodo_del_codo.png`: Gráfico del Método del Codo.
  * `../data_kmeans/k_optimo.txt`: Archivo de texto con el `k` óptimo detectado.
  * `../data_kmeans/mapa_clasificacion_k[N].nc`: Dataset NetCDF con la clasificación.
  * `../figures/mapa_clasificacion_k[N].png`: Mapa global de las zonas climáticas.
  * `../figures/mapa_clusters_habitats.png`: Mapa final con los hábitats identificados.

-----

## 🗺️ Flujo Alternativo (Selección Manual de `k`)

Si prefieres forzar un número específico de clústeres (por ejemplo, `k=9`) e ignorar el Método del Codo, puedes usar los scripts alternativos.

**Sigue la Parte 1 (pasos 1-5) y el paso 6 (PCA).** Luego, en lugar de los pasos 7 y 8:

```bash
# 7. (Alternativo) Generar el mapa forzando k=9
python nueve_clusters.py

# 8. (Alternativo) Generar el mapa forzando k=5
python cinco_clusters.py

# ... (Igualmente para 7, 8 o 10 clusters)

# 9. Analizar el mapa generado
# (Este script detectará automáticamente el último mapa creado)
python analizar_y_mapear_habitats_pandaversion.py
```

-----

## 📜 Descripción de Scripts

(Rutas relativas asumidas desde la carpeta `scripts/`)

  * `verificar_datos_originales_...`: Lee `../data/` y comprueba la consistencia de grids y unidades antes de procesar.
  * `remallar_a_grid_fijo_...`: Estandariza la resolución espacial de todos los modelos a una grid común (64x128) y aplica la máscara `../data_auxiliar/landsea.nc`. Guarda en `../data_remallada/`.
  * `unir_remallados_por_modelo_...`: Concatena las series temporales de cada modelo. Guarda en `../data_unida/`.
  * `calcular_climatologias_...`: Calcula la media mensual para cada modelo. Guarda en `../data_climatologia/`.
  * `crear_ensemble_...`: Calcula la media de todos los modelos, creando el archivo final para el análisis. Guarda en `../data_ensemble/`.
  * `aplicar_pca.py`: Carga los datos del ensemble, los estandariza y aplica PCA. Guarda los componentes principales (CPs) en `../data_pca/componentes_principales.nc`.
  * `calcular_y_guardar_codo.py`: Ejecuta K-Means para un rango de `k` (2 a 20), genera el gráfico del codo (`../figures/`) y guarda el `k` óptimo en `../data_kmeans/k_optimo.txt`.
  * `generar_mapa_kmeans.py`: Lee `../data_kmeans/k_optimo.txt`, entrena el modelo K-Means final con ese `k` y guarda el mapa NetCDF y PNG.
  * `(cinco|siete|ocho|nueve|diez)_clusters.py`: Variantes de `generar_mapa_kmeans.py` que fuerzan un valor `k` manual (5, 7, 8, 9 o 10).
  * `analizar_y_mapear_habitats_...`: Script final. Carga el mapa K-Means más reciente de `../data_kmeans/`, usa puntos de muestra (ej. "Oso Polar", "Oso Pardo") para identificar a qué clúster pertenecen, y genera el mapa final de hábitats en `../figures/`.
