from pathlib import Path

V2FLY_CWD: Path = Path(r'../v2fly')
V2FLY_BIN_FILE_PATH: Path = V2FLY_CWD / 'v2ray.exe'
V2FLY_CONFIG_PATH: Path = V2FLY_CWD / 'client.json'

# nginx
NGINX_CWD: Path = Path(r'../nginx')
NGINX_BIN_FILE_PATH: Path = NGINX_CWD / 'nginx.exe'
NGINX_CONFIG_PATH: Path = NGINX_CWD / 'conf' / 'client.conf'

DELAY: int = 5