import requests

tests = [
    "https://tronian.com/products/omegatron",
    "https://puffco.com/products/proxy",
    "https://www.zeusarsenal.com/products/zeus-arc-gts",
    "https://www.storz-bickel.com/en-us/volcano-hybrid",
    "https://arizer.com/solo3/"
]

headers = {'User-Agent': 'Mozilla/5.0'}
for url in tests:
    resp = requests.get(url, headers=headers, allow_redirects=True)
    print(url, "=>", resp.status_code)
