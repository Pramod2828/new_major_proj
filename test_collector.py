from backend.collectors.windows_event_collector import get_windows_collector
collector = get_windows_collector()
print('Collector instantiated')
print('Status before start:', collector.get_status())
collector.start()
print('Status after start:', collector.get_status())
