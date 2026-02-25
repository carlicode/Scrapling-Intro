# Tutorial: Web scraping con Scrapling

Este repositorio es un **tutorial paso a paso** para aprender a extraer datos de la web con Python usando la librería [Scrapling](https://github.com/D4Vinci/Scrapling). Al final sabrás hacer peticiones HTTP, usar selectores CSS para sacar texto y enlaces, y montar un scraper que guarde resultados en JSON.

**Qué vamos a hacer:**

1. Preparar el entorno e instalar Scrapling.
2. Hacer tu primera extracción: traer citas de una página de ejemplo.
3. Entender selectores CSS y el parser de Scrapling.
4. Construir un scraper completo para búsquedas en arXiv y guardar los datos en un archivo.

---

## Qué es Scrapling

Scrapling es un framework de web scraping en Python. Permite:

- **Traer páginas:** con `Fetcher` (HTTP simple), o con navegador para sitios con JavaScript o anti-bot.
- **Extraer datos:** con selectores CSS o XPath, al estilo Scrapy/Parsel (`.css()`, `.get()`, `.getall()`, `::text`, etc.).
- **Escalar:** crawls con muchas URLs, concurrencia y spiders (lo verás en la documentación cuando quieras ir más allá).

En este tutorial usamos solo **Fetcher** (peticiones HTTP) y el **parser** (Selector) para quedarnos en lo esencial.

Documentación completa: [scrapling.readthedocs.io](https://scrapling.readthedocs.io).

---

## 1. Preparación

### Requisitos

- **Python 3.10 o superior**
- Dependencias: `scrapling` y `requests` (para el ejemplo de arXiv)

### Instalación

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar el entorno
# En Linux/macOS:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar Scrapling y requests
pip install scrapling requests
```

Comprueba que todo va bien:

```bash
python -c "from scrapling.fetchers import Fetcher; print('OK')"
```

Si ves `OK`, estás listo para el siguiente paso.

---

## 2. Tu primera extracción

Vamos a extraer las **citas** de la página de prueba [Quotes to Scrape](https://quotes.toscrape.com). Es un sitio pensado para practicar scraping.

### Paso 2.1 — Traer la página

Scrapling puede hacer la petición HTTP y devolver un objeto con el que luego extraer datos. Se usa la clase `Fetcher` y el método `.get()`:

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get("https://quotes.toscrape.com")
```

`page` no es solo el HTML en texto: es un **Selector** sobre ese HTML. Con él podemos buscar elementos dentro de la página.

### Paso 2.2 — Elegir qué extraer con CSS

En Quotes to Scrape, cada cita está dentro de un `<div class="quote">`, y el texto de la cita está en un `<span class="text">`. Para quedarnos solo con el **texto** (sin etiquetas HTML) usamos el pseudo-elemento `::text`:

```python
quotes = page.css(".quote .text::text").getall()
```

- `.quote` → elementos con clase `quote`
- `.text` → dentro de ellos, elementos con clase `text`
- `::text` → solo el texto interior
- `.getall()` → devuelve una **lista** con todos los resultados (si usas `.get()` obtienes solo el primero)

### Paso 2.3 — Mostrar los resultados

```python
print("📜 Citas encontradas:\n")
for q in quotes[:5]:   # las 5 primeras
    print("-", q)
```

### Ejecutar el ejemplo

En el proyecto ya tienes esto en `main.py`. Ejecuta:

```bash
python main.py
```

Deberías ver algo como:

```
📜 Quotes encontradas:

- "The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
- "It is our choices, Harry, that show what we truly are, far more than our abilities."
...
```

**Resumen:** `Fetcher.get(url)` trae la página; `page.css("selector::text").getall()` extrae una lista de textos. Con eso ya puedes scrapear muchas páginas estáticas.

---

## 3. Entender selectores y el parser

### Selectores CSS

Con `.css()` puedes usar lo que ya conoces de CSS:

| Selector      | Ejemplo                    | Significado                          |
|---------------|----------------------------|--------------------------------------|
| Clase         | `.quote`                   | elementos con `class="quote"`        |
| Varias clases | `.quote.text`              | elementos que tengan ambas clases    |
| Descendiente  | `.quote .text`             | `.text` dentro de `.quote`           |
| Pseudo texto  | `.text::text`              | solo el texto dentro de `.text`      |
| Atributo      | `a::attr(href)`            | valor del atributo `href` del enlace |

- **`.get()`** → el primer resultado o `None`.
- **`.getall()`** → lista con todos los resultados.

### Usar solo el parser (sin Fetcher)

Si ya tienes el HTML (por ejemplo descargado con `requests`), puedes usar el parser de Scrapling sin hacer la petición tú mismo:

```python
from scrapling.parser import Selector

html = "<div class='quote'><span class='text'>Una cita</span></div>"
page = Selector(html)
texto = page.css(".quote .text::text").get()
# texto == "Una cita"
```

En el siguiente apartado haremos exactamente eso: descargamos el HTML con `requests` y extraemos los datos con `Selector`.

---

## 4. Scraper completo: búsquedas en arXiv

Vamos a construir un script que busque artículos en [arXiv](https://arxiv.org), extraiga título, autores, fecha, resumen y enlaces, y guarde todo en un JSON.

### Paso 4.1 — Descargar el HTML de la búsqueda

arXiv permite buscar por URL. Construimos la URL con la query y el número de resultados (25, 50, 100 o 200) y descargamos con `requests`:

```python
import requests
from urllib.parse import quote_plus

query = "machine learning"
size = 25
url = (
    "https://arxiv.org/search/?"
    f"query={quote_plus(query)}"
    "&searchtype=all&abstracts=show&order=-announced_date_first"
    f"&size={size}"
)
html = requests.get(url, headers={"User-Agent": "Mozilla/5.0 ..."}, timeout=30).text
```

(En el archivo `ArXiv-scrapling.py` esta lógica está en la función `fetch_html()`.)

### Paso 4.2 — Parsear con Scrapling

Pasamos el HTML al parser y buscamos cada resultado. En la página de búsqueda de arXiv, cada artículo está en un `<li class="arxiv-result">`. Dentro hay párrafos y spans con clases concretas para título, autores, fecha y resumen:

```python
from scrapling.parser import Selector

page = Selector(html)
results = page.css("li.arxiv-result")

for r in results:
    title = r.css("p.title.is-5.mathjax::text").get()
    authors = r.css("p.authors a::text").getall()
    # ... más campos
```

Aquí vemos que **sobre cada elemento** (`r`) podemos volver a usar `.css()` para buscar dentro de él. Así sacamos título, autores, abstract, etc., de cada bloque.

### Paso 4.3 — Guardar en JSON

Cada artículo lo guardamos como un diccionario con `title`, `authors`, `submitted`, `abstract`, `url`, `pdf_url`. Al final, volcamos la lista a un archivo:

```python
import json

with open("arxiv_results.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### Ejecutar el scraper de arXiv

El proyecto incluye todo esto en `ArXiv-scrapling.py`. Por defecto busca *"retrieval augmented generation"* y guarda 25 resultados. Ejecuta:

```bash
python ArXiv-scrapling.py
```

Verás un resumen en la terminal y se creará el archivo `arxiv_results.json`. Puedes cambiar la búsqueda o el `size` editando las variables al final del archivo:

```python
if __name__ == "__main__":
    query = "retrieval augmented generation"  # cambia aquí
    data = scrape_arxiv_search(query=query, size=25)
    # ...
```

**Resumen:** combinamos `requests` para descargar y `Selector(html)` de Scrapling para extraer. El flujo es siempre: obtener HTML → Selector → `.css()` / `.get()` / `.getall()` → estructurar datos → guardar (JSON, CSV, etc.).

---

## 5. Resumen y siguientes pasos

Has aprendido a:

- Instalar Scrapling y hacer una petición con `Fetcher.get()`.
- Extraer datos con `.css()` y los pseudo-elementos `::text` y `::attr(href)`.
- Usar `.get()` y `.getall()` y entender la diferencia.
- Usar el parser `Selector(html)` con HTML que ya tengas (por ejemplo con `requests`).
- Montar un scraper que guarde resultados en JSON.

### Ideas para seguir

- **Probar otras páginas:** usa [Quotes to Scrape](https://quotes.toscrape.com) para practicar más selectores (autores, enlaces, paginación).
- **Documentación de Scrapling:** [scrapling.readthedocs.io](https://scrapling.readthedocs.io) — fetchers avanzados (navegador, anti-bot), spiders, proxies, CLI.
- **Respetar el sitio:** revisa `robots.txt` y condiciones de uso; no hagas demasiadas peticiones seguidas.

---

## Estructura del proyecto

```
Scrapling/
├── main.py              # Tutorial paso 2: primera extracción (Quotes)
├── ArXiv-scrapling.py   # Tutorial paso 4: scraper arXiv
├── arxiv_results.json   # Generado al ejecutar ArXiv-scrapling.py
├── venv/                # Entorno virtual (no subir a git)
└── README.md            # Este tutorial
```

*Scrapling está bajo licencia BSD-3-Clause. Este repo es solo para aprendizaje.*
