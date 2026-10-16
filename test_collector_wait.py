import time
from backend.collectors.windows_event_collector import get_windows_collector
c = get_windows_collector()
print('Instantiated')
print('Before start:', c.get_status())
c.start()
print('Started')
time.sleep(7)
print('After wait:', c.get_status())
