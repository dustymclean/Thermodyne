from duckduckgo_search import DDGS

def search_official(brand, title):
    query = f"{brand} {title}"
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
        for r in results:
            print(r['href'])

search_official("Puffco", "Proxy")
