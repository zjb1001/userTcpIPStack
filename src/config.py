class Config:
    def __init__(self):
        self.config = {
            'log_level': 'INFO',
            'device_name': 'tap0',
            'mtu': 1500
        }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
