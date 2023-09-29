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

descripciones = {
    "tecnologica": "El propósito de la integración de TIC en la educación ha sido mejorar los procesos de enseñanza y aprendizaje, así como la gestión escolar. Algunas tecnologías como lenguajes de programación para niños, ambientes virtuales de aprendizaje y pizarras digitales, han sido diseñadas específicamente con fines educativos y otras, como el software de diseño y la cámara digital fueron creadas con otros fines pero se han adaptado para usos pedagógicos. Las tecnologías que se prestan para usos pedagógicos pueden ser aparatos como el televisor, el proyector o el computador, que hay que saber prender, configurar, utilizar y mantener, o también puede ser software con el que se puede escribir, diseñar, editar, graficar, animar, modelar, simular y tantas aplicaciones más. Algunos ejemplos de estas tecnologías son los dispositivos móviles, la microscopia electrónica, la computación en la nube, las hojas de cálculo, los sistemas de información geográfica y la realidad aumentada. Dentro del contexto educativo, la competencia tecnológica se puede definir como la capacidad para seleccionar y utilizar de forma pertinente, responsable y eficiente una variedad de herramientas tecnológicas entendiendo los principios que las rigen, la forma de combinarlas y las licencias que las amparan",
    "comunicativa": "Las TIC facilitan la conexión entre estudiantes, docentes, investigadores, otros profesionales y miembros de la comunidad, incluso de manera anónima, y también permiten conectarse con datos, recursos, redes y experiencias de aprendizaje. La comunicación puede ser en tiempo real, como suelen ser las comunicaciones análogas, o en diferido, y pueden ser con una persona o recurso a la vez, o con múltiples personas a través de diversidad de canales. Desde esta perspectiva, la competencia comunicativa se puede definir como la capacidad para expresarse, establecer contacto y relacionarse en espacios virtuales y audiovisuales a través de diversos medios y con el manejo de múltiples lenguajes, de manera sincrónica y asincrónica",
    "investigativa": "El eje alrededor del cual gira la competencia investigativa es la gestión del conocimiento y, en última instancia, la generación de nuevos conocimientos. La investigación puede ser reflexiva al indagar por sus mismas prácticas a través de la observación y el registro sistematizado de la experiencia para autoevaluarse y proponer nuevas estrategias. El Internet y la computación en la nube se han convertido en el repositorio de conocimiento de la humanidad. La codificación del genoma humano y los avances en astrofísica son apenas algunos ejemplos del impacto que pueden tener tecnologías como los supercomputadores, los simuladores, la minería de datos, las sofisticadas visualizaciones y la computación distribuida en la investigación. En este contexto, la competencia investigativa se define como la capacidad de utilizar las TIC para la transformación del saber y la generación de nuevos conocimientos",
    "pedagogica": "La pedagogía es el saber propio de los docentes que se construyen en el momento que la comunidad investiga el sentido de lo que hace. Las TIC han mediado algunas de las prácticas tradicionales y también han propiciado la consolidación de nuevas formas de aproximación al quehacer docente, enriqueciendo así el arte de enseñar. En consecuencia, la competencia pedagógica se constituye en el eje central de la práctica de los docentes potenciando otras competencias como la comunicativa y la tecnológica para ponerlas al servicio de los procesos de enseñanza y aprendizaje. Considerando específicamente la integración de TIC en la educación, la competencia pedagógica se puede definir como la capacidad de utilizar las TIC para fortalecer los procesos de enseñanza y aprendizaje, reconociendo alcances y limitaciones de la incorporación de estas tecnologías en la formación integral de los estudiantes y en su propio desarrollo profesional",
    "gestion": "De acuerdo con el Plan Sectorial de Educación, el componente de gestión educativa se concentra en modular los factores asociados al proceso educativo, con el fin de imaginar de forma sistemática y sistémica lo que se quiere que suceda (planear); organizar los recursos para que suceda lo que se imagina (hacer); recoger las evidencias para reconocer lo que ha sucedido y, en consecuencia, medir qué tanto se ha logrado lo que se esperaba (evaluar) para finalmente realizar los ajustes necesarios (decidir). Para todos estos procesos existen sofisticadas tecnologías que pueden hacer más eficiente la gestión escolar. También existen herramientas similares para la gestión académica haciéndola no solamente más eficiente sino más participativa, y presentándole a los estudiantes formas alternas de involucrarse en las clases que pueden favorecer a aquellos que aprenden mejor en un ambiente no tradicional. Con estas consideraciones, la competencia de gestión se puede definir como la capacidad para utilizar las TIC en la planeación, organización, administración y evaluación de manera efectiva de los procesos educativos; tanto a nivel de prácticas pedagógicas como de desarrollo institucional",
}

momentos = {
    "gestion": [
        "Organiza actividades propias de su quehacer profesional con el uso de las TIC",
        "Integra las TIC en procesos de dinamización de las gestiones directiva, académica, administrativa y comunitaria de su institución",
        "Propone y lidera acciones para optimizar procesos integrados de la gestión escolar",
    ],
    "comunicativa": [
        "Emplea diversos canales y lenguajes propios de las TIC para comunicarse con la comunidad educativa",
        "Desarrolla estrategias de trabajo colaborativo en el contexto escolar a partir de su participación en redes y comunidades con el uso de las TIC",
        "Participa en comunidades y publica sus producciones textuales en diversos espacios virtuales y a través de múltiples medios digitales, usando los lenguajes que posibilitan las TIC",
    ],
    "investigativa": [
        "Usa las TIC para hacer registro y seguimiento de lo que vive y observa en su práctica, su contexto y el de sus estudiantes",
        "Lidera proyectos de investigación propia y con sus estudiantes",
        "Construye estrategias educativas innovadoras que incluyen la generación colectiva  de conocimientos",
    ],
    "tecnologica": [
        "Reconoce un amplio espectro de herramientas tecnológicas y algunas formas de integrarlas a la práctica educativa.",
        "Utiliza diversas herramientas tecnológicas en los procesos educativos, de acuerdo a su rol, área de formación, nivel y contexto en el que se desempeña",
        "Aplica el conocimiento de una amplia variedad de tecnologías en el diseño de ambientes de aprendizaje innovadores y para plantear soluciones a problemas identificados en el contexto",
    ],
    "pedagogica": [
        "Identifica nuevas estrategias y metodologías mediadas por las TIC, como herramienta para su desempeño profesional",
        "Propone proyectos y estrategias de aprendizaje con el uso de TIC para potenciar el aprendizaje de los estudiantes",
        "Lidera experiencias significativas que involucran ambientes de aprendizaje diferenciados de acuerdo a las necesidades e intereses propias y de los estudiantes",
    ],
}


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


def eliminar_etiquetas_html(texto_html):
    soup = BeautifulSoup(texto_html, "html.parser")
    texto_sin_etiquetas = soup.get_text()
    return texto_sin_etiquetas


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


def df_final(coursera, udemy, terminos_inclusion):
    df = pd.concat([coursera, udemy], axis=0)
    patron = r"\b(?:" + "|".join(map(re.escape, terminos_inclusion)) + r")\b"

    # Utiliza str.findall para encontrar todas las coincidencias en cada título
    df["coincidencias"] = df["titulo"].str.findall(patron)

    # Filtra las filas que tienen al menos dos coincidencias
    resultado = df[df["coincidencias"].apply(len) >= 2]

    # Elimina la columna 'coincidencias' si ya no la necesitas
    resultado = resultado.drop(columns=["coincidencias"])

    return resultado


def categorizar_curso(competencia, descripcion, momentos, curso):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Eres un experto en el documento de competencias TIC del Ministerio de Educacion Nacional de Colombia",
            },
            {
                "role": "user",
                "content": "El pentagono de competencias TIC del MEN de Colombia tiene cinco competencias, y para cada competencia se puede estar uno de tres niveles o momentos, que son:\nExplorador\nIntegrador\nInnovador \nTe puedo pasar la descripción de una competencia y sus momentos, para luego pasarte la descripcion de un curso en linea y que me digas para que momento o nivel corresponde el curso?"
            },
            {
                "role": "assistant",
                "content": "Claro, estaré encantado de ayudarte a determinar en qué nivel o momento del Pentágono de Competencias TIC del MEN de Colombia corresponde un curso en línea. Por favor, proporciona la descripción de la competencia y sus momentos, así como la descripción del curso en línea, y con gusto te daré mi opinión sobre en qué nivel se encuentra.",
            },
            {
                "role": "user",
                "content": f"La competencia {competencia} tiene las siguiente descripción:\n{descripcion}.\nY sus momentos son:\nExplorador: {momentos[0]}.\nIntegrador: {momentos[1]}.\nInnovador: {momentos[2]}.",
            },
            {
                "role": "assistant",
                "content": "Gracias por proporcionar la descripción de la competencia y sus momentos. Ahora, por favor, comparte la descripción del curso en línea para que pueda determinar en qué nivel o momento del Pentágono de Competencias TIC corresponde.",
            },
            {
                "role": "user",
                "content": f"Es muy importante que me respondas solamente con una palabra a que momento corresponde: Explorador, Integrador o Innovador. La descripcion del curso es: \n {curso}. ",
            },
        ],
        temperature=0.8,
        max_tokens=5,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    time.sleep(30)
    return response["choices"][0]["message"]["content"]


def categorizar_df(df,competencia):
    df['momento'] = df.apply(lambda row: categorizar_curso(competencia,descripciones[competencia],momentos[competencia],row['descripcion']), axis=1)
    return df

# Función para cargar el DataFrame y enviar datos a la base de datos
def cargar_datos():
    # Cargar datos en un DataFrame
    """df_cursos_pedagogica = df_final(
       extraer_df_coursera(extraer_cursos_coursera(cadenas_busqueda_pedagogica),"Pedagógica"),
       extraer_df_udemy(extraer_cursos_udemy(cadenas_busqueda_pedagogica),"Pedagógica"),
       terminos_inclusion_pedagogica
    )
    print(df_cursos_pedagogica)

    df_cursos_comunicativa = df_final(
       extraer_df_coursera(extraer_cursos_coursera(cadenas_busqueda_comunicativa),"Comunicativa"),
       extraer_df_udemy(extraer_cursos_udemy(cadenas_busqueda_comunicativa),"Comunicativa"),
       terminos_inclusion_comunicativa
    )
    print(df_cursos_comunicativa)

    df_cursos_gestion = df_final(
       extraer_df_coursera(extraer_cursos_coursera(cadenas_busqueda_gestion),"De Gestión"),
       extraer_df_udemy(extraer_cursos_udemy(cadenas_busqueda_gestion),"De Gestión"),
       terminos_inclusion_gestion
    )
    print(df_cursos_gestion)

    df_cursos_investigativa = df_final(
       extraer_df_coursera(extraer_cursos_coursera(cadenas_busqueda_investigativa),"Investigativa"),
       extraer_df_udemy(extraer_cursos_udemy(cadenas_busqueda_investigativa),"Investigativa"),
       terminos_inclusion_investigativa
    )
    print(df_cursos_investigativa)

    df_cursos_tecnologica = df_final(
       extraer_df_coursera(extraer_cursos_coursera(cadenas_busqueda_tecnologica),"Tecnológica"),
       extraer_df_udemy(extraer_cursos_udemy(cadenas_busqueda_tecnologica),"Tecnológica"),
       terminos_inclusion_tecnologica
    )
    print(df_cursos_tecnologica)

    dataframes = [df_cursos_pedagogica, df_cursos_comunicativa, df_cursos_gestion, df_cursos_investigativa, df_cursos_tecnologica]

    df = pd.concat(dataframes, ignore_index=True)
    print(df)"""

    df = pd.read_csv("final.csv")
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
    # schedule.every().month.on(3).friday.at("12:00").do(cargar_datos)
    # schedule.every().wednesday.at("10:12").do(cargar_datos)
    df = pd.read_csv("cs2.csv")
    df = df.drop_duplicates()
    print(len(df))
    df = categorizar_df(df,"pedagogica")
    print(df)
    df.to_csv("categorizado.csv",index=False)
    #print(categorizar_curso("comunicativa",descripciones["comunicativa"],momentos["comunicativa"],"Los continuos cambios tecnológicos, sobre todo en aquellos aspectos vinculados a las tecnologías de la información y la comunicación (TIC) hacen que las personas tengan la necesidad de actualizarse de forma continua para que sus conocimientos no queden obsoletos. En este contexto, para las empresas se convierte en algo imprescindible disponer de profesionales que tengan las competencias necesarias para ejercer con éxito las actividades que requieren en su lugar de trabajo. El curso, basado en las experiencias previas y el syllabus de ECDL (European Computer Driving Licence), nace con la voluntad de facilitar: - el desarrollo continuado de las personas en aquellas competencias vinculadas a las tecnologías de la información y la comunicación, - la inserción laboral y la renovación de las competencias tecnológicas de los estudiantes y de los profesionales. Los 3 cursos que ofrecemos bajo el título general “Competencias digitales” están destinados a personas sin conocimientos de ofimática o a personas con unas competencias digitales básicas y que deseen mejorar sus conocimientos de ofimática para ser más eficientes en sus estudios o en su trabajo, o bien quieran aumentar sus perspectivas laborales. En este curso, trabajaremos 3 aplicaciones ofimáticas básicas: - Microsoft Word (procesador de textos). - Microsoft Excel (hoja de cálculo). - Microsoft PowerPoint (Presentaciones)."))
    #print(categorizar_curso("pedagogica",descripciones["pedagogica"],momentos["pedagogica"],"Este curso de administración se enfoca en el proceso de innovación al presentar a los estudiantes metodologías para la resolución de problemas e innovación que requieren investigación, persistencia y agilidad. Se alentará a los estudiantes a: Sintetizar las ideas, imágenes, conceptos y conjuntos de habilidades existentes de manera original Abrazar la ambigüedad Apoyar el pensamiento divergente y la toma de riesgos Este curso te ayudará a convertirte en un líder de equipo de innovación eficaz, a asumir un papel como ejecutivo de innovación dentro de una gran corporación o a proveer la actividad empresarial. Además, el conocimiento adquirido te ayudara a para planificar, aplicar y ejecutar habilidades de innovación para desarrollar y lanzar nuevos productos y servicios. Este curso te enseñara a utilizar la innovación y la mentalidad empresarial y las metodologías para convertir las oportunidades en especificaciones de productos, conceptos comerciales y eventuales introducciones de estos productos o servicios a nuevos mercados."))
    #print(categorizar_curso("gestion",descripciones["gestion"],momentos["gestion"],"Objetivo del Curso: Al finalizar el curso, el participante conocerá los requisitos de un sistema de gestión de organizaciones educativas basado en la norma ISO 21001:2018. ISO 21001:2018 Sistemas de Gestión de Organizaciones Educativas La educación no sólo es un derecho fundamental, sino una parte fundamental de la sociedad, por lo que la calidad de los proveedores de educación es una preocupación de todos. Aquí es donde aparece la norma ISO 21001. Si bien no necesariamente puede garantizar resultados, existen muchas instituciones educativas que pueden hacer para estimular el aprendizaje y garantizar que los estudiantes reciben el nivel de calidad esperado. Se está desarrollando un nuevo estándar para ayudarles a hacer esto, y que sólo se ha llegado a una etapa crítica. Estos son algunos de los beneficios de su implementación: Ayuda a responder con rapidez y eﬁcacia las necesidades de las partes interesadas. Mejora la coordinación de los procesos, la alineación de la misión, visión, objetivos y planes de acción de la organización, así como la comunicación entre todos los implicados. Mantiene un proceso de mejora continua basado en el análisis y evaluación de la información para generar los niveles óptimos de rendimiento. Facilita a un mayor número de personas la disponibilidad, accesibilidad y equidad de los servicios educativos. Propicia la incorporación de distintos estilos de aprendizaje para necesidades y entornos diferentes, promoviendo su implicación e inclusión en el ámbito educativo. Contribuye a un desarrollo sostenible que incluya educación de calidad para todos."))
    #print(categorizar_curso("comunicativa",descripciones["comunicativa"],momentos["comunicativa"],"Los continuos cambios tecnológicos, sobre todo en aquellos aspectos vinculados a las tecnologías de la información y la comunicación (TIC) hacen que las personas tengan la necesidad de actualizarse de forma continua para que sus conocimientos no queden obsoletos. En este contexto, para las empresas se convierte en algo imprescindible disponer de profesionales que tengan las competencias necesarias para ejercer con éxito las actividades que requieren en su lugar de trabajo. El curso, basado en las experiencias previas y el syllabus de ECDL (European Computer Driving Licence), nace con la voluntad de facilitar: - el desarrollo continuado de las personas en aquellas competencias vinculadas a las tecnologías de la información y la comunicación, - la inserción laboral y la renovación de las competencias tecnológicas de los estudiantes y de los profesionales. Los 3 cursos que ofrecemos bajo el título general “Competencias digitales” están destinados a personas sin conocimientos de ofimática o a personas con unas competencias digitales básicas y que deseen mejorar sus conocimientos de ofimática para ser más eficientes en sus estudios o en su trabajo, o bien quieran aumentar sus perspectivas laborales. En este curso, trabajaremos 3 aplicaciones ofimáticas básicas: - Microsoft Word (procesador de textos). - Microsoft Excel (hoja de cálculo). - Microsoft PowerPoint (Presentaciones)."))
    #print(categorizar_curso("comunicativa",descripciones["comunicativa"],momentos["comunicativa"],"Los continuos cambios tecnológicos, sobre todo en aquellos aspectos vinculados a las tecnologías de la información y la comunicación (TIC) hacen que las personas tengan la necesidad de actualizarse de forma continua para que sus conocimientos no queden obsoletos. En este contexto, para las empresas se convierte en algo imprescindible disponer de profesionales que tengan las competencias necesarias para ejercer con éxito las actividades que requieren en su lugar de trabajo. El curso, basado en las experiencias previas y el syllabus de ECDL (European Computer Driving Licence), nace con la voluntad de facilitar: - el desarrollo continuado de las personas en aquellas competencias vinculadas a las tecnologías de la información y la comunicación, - la inserción laboral y la renovación de las competencias tecnológicas de los estudiantes y de los profesionales. Los 3 cursos que ofrecemos bajo el título general “Competencias digitales” están destinados a personas sin conocimientos de ofimática o a personas con unas competencias digitales básicas y que deseen mejorar sus conocimientos de ofimática para ser más eficientes en sus estudios o en su trabajo, o bien quieran aumentar sus perspectivas laborales. En este curso, trabajaremos 3 aplicaciones ofimáticas básicas: - Microsoft Word (procesador de textos). - Microsoft Excel (hoja de cálculo). - Microsoft PowerPoint (Presentaciones)."))



if __name__ == "__main__":
    programar_tarea()

    while True:
        schedule.run_pending()
        time.sleep(1)
