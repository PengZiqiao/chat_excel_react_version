from zhipuai import ZhipuAI
from pathlib import Path
import yaml

current_dir = Path(__file__).resolve().parent

with open(current_dir / '..' / 'config.yaml', 'r') as f:
    config = yaml.safe_load(f)

MODEL = config['model']
API_KEY = config['api_key']

client = ZhipuAI(api_key=API_KEY)


