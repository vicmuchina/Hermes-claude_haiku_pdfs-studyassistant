import os
from openai import OpenAI
import requests

def get_model_info(model_name):
    response = requests.get(
        'https://openrouter.ai/api/v1/models',
        headers={'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}'}
    )
    models = response.json()
    for model in models['data']:
        if model['id'] == model_name:
            return model
    return None

model = "mattshumer/reflection-70b:free"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

model_info = get_model_info(model)
max_tokens = model_info['context_length'] if model_info else 131072