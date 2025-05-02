import os
import time
import threading
from prometheus_client import start_http_server, Gauge
from collections import defaultdict

class ErrorMonitor:
    def __init__(self):
        self.metrics = {
            'agent_uptime': Gauge('agent_uptime_seconds', 'Agent uptime in seconds', ['agent']),
            'api_errors': Gauge('api_error_count', 'Number of API errors by agent', ['agent']),
        }
        self._uptime = defaultdict(int)
        self._running = True
        threading.Thread(target=self._simulate_uptime_tracking, daemon=True).start()

    def _simulate_uptime_tracking(self):
        """Simulate tracking agent uptime every 5 seconds."""
        while self._running:
            for agent in ['weather', 'news', 'translation']:
                self._uptime[agent] += 5
                self.metrics['agent_uptime'].labels(agent=agent).set(self._uptime[agent])
            time.sleep(5)

    def report_error(self, agent_name: str):
        current = self.metrics['api_errors'].labels(agent=agent_name)._value.get()
        self.metrics['api_errors'].labels(agent=agent_name).set(current + 1)

    def stop(self):
        self._running = False


if __name__ == '__main__':
    monitor = ErrorMonitor()
    start_http_server(9090)
    print("Prometheus metrics exposed at :9090")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
