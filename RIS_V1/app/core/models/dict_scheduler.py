import time
import threading

class DictScheduler:
    def __init__(self, timeout, check_interval=60):
        self.data = {}
        self.timeout = timeout
        self.lock = threading.Lock()
        self.last_access = {}
        self.check_interval = check_interval
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        thread = threading.Thread(target=self._cleanup, daemon=True)
        thread.start()

    def _cleanup(self):
        while True:
            time.sleep(self.check_interval)
            with self.lock:
                current_time = time.time()
                keys_to_delete = [key for key, last_time in self.last_access.items()
                                  if current_time - last_time > self.timeout]
                for key in keys_to_delete:
                    del self.data[key]
                    del self.last_access[key]

    def __setitem__(self, key, value):
        with self.lock:
            self.data[key] = value
            self.last_access[key] = time.time()

    def __getitem__(self, key):
        with self.lock:
            value = self.data[key]
            self.last_access[key] = time.time()
            return value

    def get(self, key, default=None):
        with self.lock:
            if key in self.data:
                self.last_access[key] = time.time()
                return self.data[key]
            return default    