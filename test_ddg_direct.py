from duckduckgo_search import DDGS
query = "Tronian Omegatron site:tronian.com"
try:
    results = list(DDGS().text(query, max_results=3))
    print(results)
except Exception as e:
    print("Error:", e)
