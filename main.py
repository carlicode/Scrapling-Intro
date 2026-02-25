from scrapling.fetchers import Fetcher

# 1. Hacemos una petición simple
page = Fetcher.get("https://quotes.toscrape.com")

# 2. Extraemos textos usando CSS selectors
quotes = page.css(".quote .text::text").getall()

# 3. Mostramos resultados
print("📜 Quotes encontradas:\n")
for q in quotes[:5]:
    print("-", q)