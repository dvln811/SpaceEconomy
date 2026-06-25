"""Load economy_config.yaml and expose as a module-level dict."""
import os, yaml

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'economy_config.yaml')

def _load():
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)

CONFIG = _load()

# Shortcuts
MINING = CONFIG['mining']
PASSIVE = CONFIG['passive_generation']
ECONOMY = CONFIG['economy']
