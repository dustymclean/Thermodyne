from duckduckgo_search import DDGS
try:
    results = list(DDGS().text("Tronian Omegatron official site buy", backend="html", max_results=3))
    print(results)
except Exception as e:
    print("Error:", e)
