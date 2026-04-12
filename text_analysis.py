import requests
import json

def analyze_text(text: str) -> dict:
    prompt = f"""
    Analyse ce texte et répond en JSON avec :
    - summary : un résumé court
    - credibility_score : Un score de crédibilité de 0 à 10
    - result : attribue un résultat : "vrai", "faux" ou "incertain"

    Texte : 
    {text}
    """
    
    
    reponse = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )
    
    result = reponse.json()["response"]
    
    return result