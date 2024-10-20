import os

class Config:
    HOST = "Your Host"
    PORT = "Your Port"
    RELOAD = "Your Reload"
    WORKERS = "Your Workers",
    LIMIT_CONCURRENCY = "Your Limit Concurrency"

config = Config()
    
instance_config_path = os.path.join(os.path.dirname(__file__), 'instance', 'config.py')
if os.path.exists(instance_config_path):
    instance_config = {}
    with open(instance_config_path) as f:
        exec(f.read(), instance_config)

    # instance_config에서 Config의 속성을 오버라이드
    for key, value in instance_config.items():
        if hasattr(config, key):
            setattr(config, key, value)