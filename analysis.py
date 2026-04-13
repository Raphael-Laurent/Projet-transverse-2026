import requests

def analyze_text(text: str) -> dict:
    prompt = f"""
Analyse rapidement ce texte provenant d'un audio tiktok et attribue lui un score basé sur la véracité des informations circulées. Soit bref.

Répond uniquement en JSON, sans explications, ni commentaires, ni autres éléments :
- score sur 100
- label (true 100 - 66 /false 0 - 33/uncertain 33 - 66)

Texte :
{text}
"""

    return call_ollama(prompt)


def analyze_image_text(text: str) -> dict:
    prompt = f"""
Ce texte est le résultat de plusieurs frames d'une vidéo traduite en texte, analyse la rapidement et attribue lui un score basé sur l'utilisation de l'IA pour générer ces images (plus l'IA a été utilisée, plus le score ser bas). Soit bref.

Réponds en JSON sans explications, ni commentaires, ni autres éléments :
- score sur 100
- label (true 100 - 66 /false 0 - 33/uncertain 33 - 66)

Texte :
{text}
"""

    return call_ollama(prompt)


def call_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
            "keep_alive": "5m"
        }
    )
    return response.json()["response"]