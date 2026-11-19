import urllib.request
import json
import urllib.parse

queries = [
    'mghp',
    'kkht',
    'nvqs',
    'drl',
    'cpa',
    'don xin tam dung hoc tap',
    'mien giam hoc phi',
    'tam hoan nvqs',
    'ho so ho tro chi phi hoc tap',
]

for q in queries:
    url = f'http://127.0.0.1:8000/api/v1/search?q={urllib.parse.quote(q)}'
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"=== Query: '{q}' (Total hits: {data.get('total_hits')}) ===")
            for x in data.get('results', [])[:4]:
                print(f"   [{x.get('score'):>5}] {x.get('title')}")
    except Exception as e:
        print(f"Error for '{q}': {e}")
