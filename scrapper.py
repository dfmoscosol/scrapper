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
            "urllogo",
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
                            "urllogo": "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPCEtLSBHZW5lcmF0b3I6IEFkb2JlIElsbHVzdHJhdG9yIDE2LjIuMCwgU1ZHIEV4cG9ydCBQbHVnLUluIC4gU1ZHIFZlcnNpb246IDYuMDAgQnVpbGQgMCkgIC0tPgo8IURPQ1RZUEUgc3ZnIFBVQkxJQyAiLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4iICJodHRwOi8vd3d3LnczLm9yZy9HcmFwaGljcy9TVkcvMS4xL0RURC9zdmcxMS5kdGQiPgo8c3ZnIHZpZXdCb3g9IjAgMCAxMTU1IDE2NCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGNsaXAtcnVsZT0iZXZlbm9kZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLW1pdGVybGltaXQ9IjIiPjxwYXRoIGQ9Ik0xNTkuNzUgODEuNTRjMC00NC40OSAzNi42My04MC40NyA4Mi40My04MC40NyA0Ni4xMiAwIDgyLjc2IDM2IDgyLjc2IDgwLjQ3IDAgNDQuMTYtMzYuNjQgODAuOC04Mi43NiA4MC44LTQ1LjggMC04Mi40My0zNi42OC04Mi40My04MC44em0xMjUuNjEgMGMwLTIyLjI0LTE5LjMtNDEuODctNDMuMTgtNDEuODctMjMuNTUgMC00Mi44NSAxOS42My00Mi44NSA0MS44NyAwIDIyLjU3IDE5LjMgNDIuMiA0Mi44NSA0Mi4yIDIzLjkyIDAgNDMuMTgtMTkuNjMgNDMuMTgtNDIuMnptNzA1LjYzIDEuMzFjMC00OC43NCAzOS41OC04MS43OCA3NS41Ny04MS43OCAyNC41MyAwIDM4LjYgNy41MiA0OC4wOCAyMS45MmwzLjc3LTE5aDM2Ljc5djE1NS40aC0zNi43OWwtNC43NS0xNmMtMTAuNzkgMTEuNzgtMjQuMjEgMTktNDcuMSAxOS0zNS4zMy0uMDUtNzUuNTctMzEuMTMtNzUuNTctNzkuNTR6bTEyNS42MS0uMzNjLS4wOS0yMy41MjctMTkuNDctNDIuODM1LTQzLTQyLjgzNS0yMy41OSAwLTQzIDE5LjQxMS00MyA0M3YuMTY1YzAgMjEuNTkgMTkuMyA0MC44OSA0Mi44NiA0MC44OSAyMy44NSAwIDQzLjE0LTE5LjMgNDMuMTQtNDEuMjJ6TTk0NS43OCAyMlY0aC00MC4yM3YxNTUuMzloNDAuMjNWNzUuNjZjMC0yNS4xOSAxMi40NC0zOC4yNyAzNC0zOC4yNyAxLjQzIDAgMi43OS4xIDQuMTIuMjNMOTkxLjM2LjExYy0yMC45Ny4xMS0zNi4xNyA3LjMtNDUuNTggMjEuODl6bS00MDQuMjcuMDF2LTE4bC00MC4yMy4wOS4zNCAxNTUuMzcgNDAuMjMtLjA5LS4yMi04My43MmMtLjA2LTI1LjE4IDEyLjM1LTM4LjI5IDMzLjkzLTM4LjM0IDEuMzc2LjAwNCAyLjc1Mi4wODEgNC4xMi4yM0w1ODcuMSAwYy0yMSAuMTctMzYuMjIgNy4zOS00NS41OSAyMi4wMXpNMzM4Ljg4IDk5LjJWNC4wMWg0MC4yMlY5NC4zYzAgMTkuOTUgMTEuMTIgMzEuNzMgMzAuNDIgMzEuNzMgMjEuNTkgMCAzNC0xMy4wOSAzNC0zOC4yOFY0LjAxaDQwLjI0djE1NS4zOGgtNDAuMjF2LTE4Yy05LjQ4IDE0LjcyLTI0Ljg2IDIxLjkyLTQ2LjEyIDIxLjkyLTM1Ljk4LjAxLTU4LjU1LTI2LjE2LTU4LjU1LTY0LjExem0zOTEuNzQtMTcuNDhjLjA5LTQzLjUxIDMxLjIzLTgwLjc0IDgwLjYyLTgwLjY1IDQ1LjguMDkgNzguMTEgMzYuNzggNzggODAgLjAxIDQuMjczLS4zMyA4LjU0LTEgMTIuNzZsLTExOC40MS0uMjJjNC41NCAxOC42NSAxOS44OSAzMi4wOSA0My4xMiAzMi4xNCAxNC4wNiAwIDI5LjEyLTUuMTggMzguMy0xNi45NGwyNy40NCAyMmMtMTQuMTEgMTkuOTMtMzkgMzEuNjYtNjUuNDggMzEuNjEtNDYuNzUtLjE2LTgyLjY3LTM1LjIzLTgyLjU5LTgwLjd6bTExOC4xMi0xNi4xNGMtMi4yNi0xNS43LTE4LjU5LTI3Ljg0LTM3Ljg5LTI3Ljg3LTE4LjY1IDAtMzMuNzEgMTEuMDYtMzkuNjMgMjcuNzNsNzcuNTIuMTR6bS0yNjEuNCA1OS45NGwzNS43Ni0xOC43MmM1LjkxIDEyLjgxIDE3LjczIDIwLjM2IDM0LjQ4IDIwLjM2IDE1LjQzIDAgMjEuMzQtNC45MiAyMS4zNC0xMS44MiAwLTI1LTg0LjcxLTkuODUtODQuNzEtNjcgMC0zMS41MiAyNy41OC00OC4yNiA2MS43Mi00OC4yNiAyNS45NCAwIDQ4LjkyIDExLjQ5IDYxLjQgMzIuODNsLTM1LjQ0IDE4Ljc1Yy01LjI1LTEwLjUxLTE1LjEtMTYuNDItMjcuNTgtMTYuNDItMTIuMTQgMC0xOC4wNiA0LjI3LTE4LjA2IDExLjQ5IDAgMjQuMyA4NC43MSA4Ljg3IDg0LjcxIDY3IDAgMzAuMjEtMjQuNjIgNDguNTktNjQuMzUgNDguNTktMzMuODItLjAzLTU3LjQ2LTExLjE5LTY5LjI3LTM2Ljh6TTAgODEuNTRDMCAzNi43MyAzNi42My43NCA4Mi40My43NGMyNy45NDctLjE5NiA1NC4xODIgMTMuNzM3IDY5LjY3IDM3bC0zNC4zNCAxOS45MmE0Mi45NzIgNDIuOTcyIDAgMDAtMzUuMzMtMTguMzJjLTIzLjU1IDAtNDIuODUgMTkuNjMtNDIuODUgNDIuMiAwIDIyLjU3IDE5LjMgNDIuMiA0Mi44NSA0Mi4yYTQyLjUwMiA0Mi41MDIgMCAwMDM2LjMxLTIwbDM0IDIwLjI4Yy0xNS4zMDcgMjMuOTU1LTQxLjkwMiAzOC40MzEtNzAuMzMgMzguMjhDMzYuNjMgMTYyLjM0IDAgMTI1LjY2IDAgODEuNTR6IiBmaWxsPSIjMDA1NkQyIiBmaWxsLXJ1bGU9Im5vbnplcm8iLz48L3N2Zz4="
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
            response = requests.get(next_url, headers=os.getenv("headers_udemy")).json()
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
            "urllogo"
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
                            "urllogo": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Udemy_logo.svg/2560px-Udemy_logo.svg.png"
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

#Categoriza todo el dataframe segun los momentos
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
