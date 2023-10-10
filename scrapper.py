import schedule
import time
import datetime
import psycopg2
from sqlalchemy import create_engine, inspect
from bs4 import BeautifulSoup
import requests
import urllib.parse
import pandas as pd
import re
import openai
import os

cadenas_busqueda_pedagogica = [
    "tic educación",
    "tecnología docente",
    "enseñanza tic",
    "tic educativas",
    "enseñanza tecnología",
    "docencia digital",
    "educación digital",
    "tecnología educativa",
    "enseñanza digital",
    "aprendizaje tic",
    "pedagogía tecnológica",
    "tecnologías aprendizaje",
]
cadenas_busqueda_comunicativa = [
    "comunicación digital",
    "redes sociales educativas",
    "comunicación online",
    "interacción digital",
    "comunicación virtual",
    "redes educativas",
    "interacción online",
]
cadenas_busqueda_gestion = [
    "gestión educativa",
    "gestión tecnología",
    "administración educativa",
    "planificación digital",
    "evaluación online",
    "planificación tic",
    "evaluación educativa",
    "administración tic",
    "planeación educativa",
]
cadenas_busqueda_investigativa = [
    "investigación tic",
    "investigación online",
    "investigación digital",
    "métodos online",
    "investigación tic",
    "análisis digital",
    "métodos digitales",
    "investigación educación",
    "análisis datos educativos",
]
cadenas_busqueda_tecnologica = [
    "competencia digital",
    "competencia tecnología",
    "tecnología docentes",
    "habilidades digitales",
    "tic educación",
    "tecnología educación",
    "habilidades tecnológicas",
    "tic aprendizaje",
    "tecnología educativa",
    "tic enseñanza",
]

#Extrae los cursos de coursera
def extraer_cursos_coursera(cadenas):
    URL_BASE_COURSERA = os.getenv("URL_BASE_COURSERA")
    cursos = []
    for cadena in cadenas:
        # 1. Obtener el HTML
        URL_BUSQUEDA = (
            f"{URL_BASE_COURSERA}{urllib.parse.quote(cadena, safe='')}&language=Spanish"
        )
        pedido_obtenido = requests.get(URL_BUSQUEDA)
        pedido_obtenido.encoding = "utf-8"
        html_obtenido = pedido_obtenido.text

        # 2. "Parsear" ese HTML
        soup = BeautifulSoup(html_obtenido, "html.parser", from_encoding="utf-8")

        # 3. Extraer el numero de paginas de la busqueda
        divs = soup.find_all("button", class_=["box number", "box number current"])
        if len(divs) == 0:
            paginas = 0
        else:
            paginas = divs[len(divs) - 1]["aria-label"].rsplit(maxsplit=1)[-1]

        # 4.Extraer los cursos de todas las paginas
        for i in range(int(paginas)):
            URL_FINAL = f"{URL_BUSQUEDA}&page={i+1}"
            pedido_obtenido_final = requests.get(URL_FINAL)
            pedido_obtenido_final.encoding = "utf-8"
            html_obtenido_final = pedido_obtenido_final.text
            soup_final = BeautifulSoup(html_obtenido_final, "html.parser")
            divs_final = soup_final.find_all(class_="cds-CommonCard-clickArea")
            for div in divs_final:
                # Obtener urlimagen
                img_div = div.find("div", class_="cds-CommonCard-previewImage")
                if img_div:
                    img = img_div.find("img")
                    if img and img.has_attr("src"):
                        urlimagen = img["src"]
                    else:
                        urlimagen = "N/A"
                else:
                    urlimagen = "N/A"

                # Obtener url
                a = div.find(
                    "a",
                    class_="cds-119 cds-113 cds-115 cds-CommonCard-titleLink css-si869u cds-142",
                )
                if a and a.has_attr("href"):
                    href = a["href"]
                else:
                    href = "N/A"
                print(href)
                # Obtener ofertante
                p_ofertante = div.find(
                    "p",
                    class_="cds-119 cds-ProductCard-partnerNames css-dmxkm1 cds-121",
                )
                if p_ofertante:
                    ofertante = p_ofertante.get_text()
                else:
                    ofertante = "N/A"

                # Obtener titulo
                h3_titulo = div.find(
                    "h3", class_="cds-119 cds-CommonCard-title css-e7lgfl cds-121"
                )
                if h3_titulo:
                    titulo = h3_titulo.get_text()
                else:
                    titulo = "N/A"

                if href.startswith("/learn"):
                    cursos.append(
                        {
                            "titulo": titulo,
                            "url": "https://www.coursera.org" + href,
                            "url_img": urlimagen,
                            "ofertante": ofertante,
                        }
                    )

    return cursos

#Extrae el df de los cursos de coursera
def extraer_df_coursera(cursos, competencia):
    df = pd.DataFrame(
        columns=[
            "titulo",
            "url",
            "urlimagen",
            "ofertante",
            "descripcion",
            "habilidades",
            "competencia",
        ]
    )
    for curso in cursos:
        # 1. Obtener el HTML
        pedido_obtenido = requests.get(curso["url"])
        pedido_obtenido.encoding = "utf-8"
        html_obtenido = pedido_obtenido.text
        # 2. "Parsear" ese HTML
        soup = BeautifulSoup(html_obtenido, "html.parser")
        # 3. Extraer la descripcion
        div_content_inner = soup.find("div", class_="content-inner")
        descripcion = ""
        if div_content_inner:
            for parrafo in div_content_inner.find_all("p"):
                descripcion += parrafo.get_text() + " "
        # 4. Extraer skills

        div_css_1cj91aq = soup.find("div", class_="css-1cj91aq")

        # Comprobar si el div contiene un h2 con la clase cds-119 css-h1jogs cds-121
        h2 = (
            div_css_1cj91aq.find("h2", class_="cds-119 css-h1jogs cds-121")
            if div_css_1cj91aq
            else None
        )

        if h2:
            # Obtener todos los objetos span dentro del div
            spans = div_css_1cj91aq.find_all("span")
            textos_span = [span.get_text() for span in spans]
        else:
            textos_span = []

        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "titulo": curso["titulo"],
                            "url": curso["url"],
                            "urlimagen": curso["url_img"],
                            "ofertante": curso["ofertante"],
                            "descripcion": descripcion,
                            "habilidades": list(filter(None, set(textos_span))),
                            "competencia": competencia,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return df.drop_duplicates(subset="titulo", keep="first")

#Extrae los cursos de udemy
def extraer_cursos_udemy(cadenas):
    URL_BASE_UDEMY = os.getenv("URL_BASE_UDEMY")
    cursos_totales = []
    for cadena in cadenas:
        next_url = f"{URL_BASE_UDEMY}{urllib.parse.quote(cadena, safe='')}"  # Inicializa next_url con la URL actual
        while next_url:
            print(next_url)
            response = requests.get(next_url, headers=headers_udemy).json()
            if (
                "detail" in response
                and "results" not in response
                and "next" not in response
            ):
                next_url = None  # Establece next_url en "null" y sal del bucle
            else:
                cursos = response.get(
                    "results", []
                )  # Obtén la lista de cursos de la respuesta actual
                cursos_totales.extend(cursos)  # Agrega los cursos a la lista total
                next_url = response.get("next")

    return cursos_totales

#Elimina las etiquetas html de un string
def eliminar_etiquetas_html(texto_html):
    soup = BeautifulSoup(texto_html, "html.parser")
    texto_sin_etiquetas = soup.get_text()
    return texto_sin_etiquetas

#Extrae el df de los cursos de udemy
def extraer_df_udemy(cursos, competencia):
    df = pd.DataFrame(
        columns=[
            "titulo",
            "url",
            "urlimagen",
            "ofertante",
            "descripcion",
            "habilidades",
            "competencia",
        ]
    )
    for curso in cursos:
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "titulo": curso["title"],
                            "url": f"https://udemy.com{curso['url']}",
                            "urlimagen": curso["image_480x270"],
                            "ofertante": curso["visible_instructors"][0][
                                "display_name"
                            ],
                            "descripcion": eliminar_etiquetas_html(
                                curso["description"]
                            ),
                            "habilidades": curso["what_you_will_learn_data"]["items"],
                            "competencia": competencia,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    return df.drop_duplicates(subset="titulo", keep="first")

#Une los dfs que se reciban en un array
def unir_dfs(df):
    df = pd.concat(df, axis=0)
    return df

#Clasifica la descripcion del curso en los tres niveles
def clasificar_segun_bloom_tres_niveles(descripcion):
    # Definir grupos de verbos clave para cada nivel combinado
    niveles_combinados = {
        "Explorador": [
                                        "Conocer", "Entender", "Recordar", "Enumerar", "Nombrar", "Definir", "Citar", "Explicar", "Comprender",
                                        "Identificar", "Resumir", "Describir", "Distinguir", "Señalar", "Repetir", "Comentar", "Ilustrar", "Recopilar",
                                        "Registrar", "Comunicar", "Comparar", "Clasificar", "Analizar", "Deducir", "Extraer", "Inferir", "Diferenciar",
                                        "Discutir", "Relatar", "Interrogar", "Resaltar", "Reseñar", "Sintetizar", "Generalizar", "Asociar", "Categorizar",
                                        "Reconocer", "Interpretar", "Relacionar", "Enunciar", "Caracterizar", "Concluir", "Inferir", "Argumentar", "Examinar",
                                        "Elegir"
                                    ],
        "Integrador": [
                                    "Aplicar", "Utilizar", "Resolver", "Analizar", "Diseñar", "Calcular", "Evaluar", "Comparar", "Contrastar",
                                    "Investigar", "Inspeccionar", "Examinar", "Probar", "Experimentar", "Investigar", "Criticar", "Detectar",
                                    "Clasificar", "Organizar", "Estructurar", "Desglosar", "Reconstruir", "Diseñar", "Esquematizar", "Diagramar",
                                    "Determinar", "Diferenciar", "Sintetizar", "Combinar", "Integrar", "Componer", "Completar", "Calificar",
                                    "Justificar", "Defender", "Argumentar", "Verificar", "Comprobar", "Corroborar", "Subdividir", "Describir",
                                    "Caracterizar", "Discriminar", "Diagramar", "Concluir", "Planificar"
                                ],
        "Innovador": [
                                    "Crear", "Combinar", "Diseñar", "Planificar", "Organizar", "Sintetizar", "Generar", "Producir", "Inventar",
                                    "Construir", "Formular", "Elaborar", "Componer", "Esquematizar", "Modelar", "Valorar", "Evaluar", "Juzgar",
                                    "Criticar", "Seleccionar", "Elegir", "Decidir", "Definir", "Argumentar", "Justificar", "Razonar", "Priorizar",
                                    "Estimar", "Contrastar", "Analizar", "Sopesar", "Examinar", "Investigar", "Determinar"
                                ],
    }

    # Inicializar el nivel taxonómico como desconocido
    nivel = "Desconocido"

    # Recorrer los niveles combinados y buscar verbos clave
    for key, verbos_clave in niveles_combinados.items():
        for verbo in verbos_clave:
            if verbo.lower() in descripcion.lower():
                nivel = key
                break

    return nivel


def categorizar_momentos(df):
    df["momento"] = df.apply(
        lambda row: clasificar_segun_bloom_tres_niveles(row["descripcion"]), axis=1
    )
    
    df = df[df["momento"] != "Desconocido"]
    return df


# Función para cargar el DataFrame y enviar datos a la base de datos
def cargar_datos():
    # Cargar datos en un DataFrame

    df_cursos_pedagogica = unir_dfs(
        [extraer_df_coursera(
            extraer_cursos_coursera(cadenas_busqueda_pedagogica), "Pedagógica"
        ),
        extraer_df_udemy(
            extraer_cursos_udemy(cadenas_busqueda_pedagogica), "Pedagógica"
        )]
    )
    print(df_cursos_pedagogica)

    df_cursos_comunicativa = unir_dfs(
        [extraer_df_coursera(
            extraer_cursos_coursera(cadenas_busqueda_comunicativa), "Comunicativa"
        ),
        extraer_df_udemy(
            extraer_cursos_udemy(cadenas_busqueda_comunicativa), "Comunicativa"
        )]
    )
    print(df_cursos_comunicativa)

    df_cursos_gestion = unir_dfs(
        [extraer_df_coursera(
            extraer_cursos_coursera(cadenas_busqueda_gestion), "De Gestión"
        ),
        extraer_df_udemy(extraer_cursos_udemy(cadenas_busqueda_gestion), "De Gestión")]
    )
    print(df_cursos_gestion)

    df_cursos_investigativa = unir_dfs(
        [extraer_df_coursera(
            extraer_cursos_coursera(cadenas_busqueda_investigativa), "Investigativa"
        ),
        extraer_df_udemy(
            extraer_cursos_udemy(cadenas_busqueda_investigativa), "Investigativa"
        )]
    )
    print(df_cursos_investigativa)

    df_cursos_tecnologica = unir_dfs(
        [extraer_df_coursera(
            extraer_cursos_coursera(cadenas_busqueda_tecnologica), "Tecnológica"
        ),
        extraer_df_udemy(
            extraer_cursos_udemy(cadenas_busqueda_tecnologica), "Tecnológica"
        )]
    )
    print(df_cursos_tecnologica)

    dataframes = [
        df_cursos_pedagogica,
        df_cursos_comunicativa,
        df_cursos_gestion,
        df_cursos_investigativa,
        df_cursos_tecnologica,
    ]

    df = unir_dfs(dataframes)
    print(df)

    # Establecer una conexión a la base de datos y crear un motor SQLAlchemy
    db_config = os.getenv("db_config")
    conn_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
    engine = create_engine(conn_string)

    # Verificar si la tabla 'cursos' existe en la base de datos y eliminarla
    inspector = inspect(engine)
    if inspector.has_table("cursos"):
        # Si existe, borra la tabla
        engine.execute("DROP TABLE cursos")

    # Insertar los datos del DataFrame en la tabla cursos
    df.to_sql("curso", engine, if_exists="append", index=False)

    # Cierra la conexión de SQLAlchemy
    engine.dispose()

    # Imprimir un mensaje para verificar que se ejecutó la tarea
    print("Datos cargados en la base de datos.")


# Programar la ejecución en el tercer viernes de cada mes a las 12:00 PM
def programar_tarea():
    schedule.every().month.on(3).friday.at("12:00").do(cargar_datos)

if __name__ == "__main__":
    programar_tarea()

    while True:
        schedule.run_pending()
        time.sleep(1)
