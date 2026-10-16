from backend.collectors.windows_event_collector import get_windows_collector
import traceback, json
c=get_windows_collector()
print('Collector instantiated')
try:
    status=c.get_status()
    print('Status ok', json.dumps(status, indent=2))
except Exception as e:
    print('Error on get_status')
    traceback.print_exc()
