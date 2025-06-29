import yaml, sys

def read_config(config_path):
    """
    read the configuration from config_path (yaml file).
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        sys.exit(f"Configuration file {config_path} not found.")
    except yaml.YAMLError as e:
        sys.exit(f"Error parsing {config_path}: {e}")

