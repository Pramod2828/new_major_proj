import requests, json, sys
base='http://127.0.0.1:5000/api/collector'
try:
    r=requests.get(f'{base}/status')
    print('STATUS CODE', r.status_code)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print('Error status', e)

try:
    r=requests.post(f'{base}/poll-now')
    print('POLL CODE', r.status_code)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print('Error poll', e)
