"""
Module d'analyse de véracité via LLM local.

Utilise Ollama (Mistral) pour analyser le contenu audio et visuel
d'une vidéo et attribuer un score de fiabilité.
"""

import json
import logging
import requests

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "mistral"


class AnalysisError(Exception):
    """Erreur levée lorsque l'analyse LLM échoue."""
    pass


def check_ollama() -> bool:
    """
    Vérifie qu'Ollama est démarré et accessible.

    Returns:
        True si Ollama répond, False sinon.
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Envoie un prompt à Ollama et retourne la réponse brute.

    Args:
        prompt: Le prompt à envoyer au modèle.
        model: Nom du modèle Ollama à utiliser.

    Returns:
        Réponse textuelle du modèle.

    Raises:
        AnalysisError: Si Ollama n'est pas accessible ou retourne une erreur.
    """
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "5m",
            },
            timeout=120,
        )
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            raise AnalysisError(f"Erreur Ollama : {data['error']}")

        return data.get("response", "")

    except requests.ConnectionError:
        raise AnalysisError(
            "Impossible de se connecter à Ollama. "
            "Assurez-vous qu'Ollama est démarré (lancez 'ollama serve')."
        )
    except requests.Timeout:
        raise AnalysisError("Ollama n'a pas répondu dans le délai imparti (120s).")
    except requests.HTTPError as e:
        raise AnalysisError(f"Erreur HTTP Ollama : {e}")


def parse_json_response(raw_response: str) -> dict:
    """
    Parse la réponse JSON du LLM en gérant les cas d'erreur.

    Le LLM peut entourer le JSON de texte ou de balises markdown.
    Cette fonction tente d'extraire le JSON valide.

    Args:
        raw_response: Réponse brute du modèle.

    Returns:
        Dictionnaire parsé contenant au minimum 'score' et 'label'.
    """
    text = raw_response.strip()

    # Retirer les balises markdown ```json ... ```
    if "```json" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Tenter d'extraire le premier objet JSON trouvé
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Impossible de parser le JSON du LLM : {raw_response[:200]}")
        return {
            "score": 50,
            "label": "uncertain",
            "raw_response": raw_response,
            "parse_error": True,
        }

    # Normaliser les clés
    score = result.get("score", 50)
    if isinstance(score, str):
        try:
            score = int(score)
        except ValueError:
            score = 50

    label = result.get("label", "uncertain").lower()
    if label not in ("true", "false", "uncertain"):
        label = "uncertain"

    return {
        "score": max(0, min(100, score)),
        "label": label,
        "explanation": result.get("explanation", ""),
    }


def analyze_audio(text: str) -> dict:
    """
    Analyse le texte transcrit de l'audio pour évaluer sa véracité.

    Args:
        text: Texte transcrit de l'audio de la vidéo.

    Returns:
        Dictionnaire avec 'score' (0-100), 'label' (true/false/uncertain), 'explanation'.
    """
    if not text or not text.strip():
        logger.info("Aucun texte audio à analyser.")
        return {"score": 50, "label": "uncertain", "explanation": "Aucun audio détecté."}

    prompt = f"""Analyse ce texte provenant de l'audio d'une vidéo de réseau social.
Évalue la véracité des informations présentées.

Réponds UNIQUEMENT en JSON valide avec ces champs :
- "score": nombre entier de 0 à 100 (100 = très fiable, 0 = faux)
- "label": "true" (score 67-100), "uncertain" (score 34-66), ou "false" (score 0-33)
- "explanation": une phrase courte expliquant ton évaluation (OBLIGATOIREMENT EN FRANÇAIS)

Texte à analyser :
{text}"""

    raw = call_ollama(prompt)
    return parse_json_response(raw)


def analyze_visual(ocr_text: str, vision_descriptions: list[str]) -> dict:
    """
    Analyse le contenu visuel pour détecter des signes de manipulation ou d'IA.

    Args:
        ocr_text: Texte extrait par OCR des frames de la vidéo.
        vision_descriptions: Descriptions des frames par le modèle de vision.

    Returns:
        Dictionnaire avec 'score' (0-100), 'label', 'explanation'.
    """
    # Construire le contexte visuel
    visual_context = ""

    if ocr_text.strip():
        visual_context += f"Texte lu dans les images (OCR) :\n{ocr_text}\n\n"

    if vision_descriptions:
        visual_context += "Descriptions visuelles des frames :\n"
        for i, desc in enumerate(vision_descriptions, 1):
            visual_context += f"- Frame {i} : {desc}\n"

    if not visual_context.strip():
        logger.info("Aucun contenu visuel à analyser.")
        return {"score": 50, "label": "uncertain", "explanation": "Aucun contenu visuel exploitable."}

    prompt = f"""Analyse ces informations visuelles extraites d'une vidéo de réseau social.
Évalue si les images semblent authentiques ou si elles montrent des signes de manipulation
ou de génération par intelligence artificielle (deepfake, images IA, montage, etc.).

Réponds UNIQUEMENT en JSON valide avec ces champs :
- "score": nombre entier de 0 à 100 (100 = authentique, 0 = manipulé/IA)
- "label": "true" (score 67-100), "uncertain" (score 34-66), ou "false" (score 0-33)
- "explanation": une phrase courte expliquant ton évaluation (OBLIGATOIREMENT EN FRANÇAIS)

Données visuelles :
{visual_context}"""

    raw = call_ollama(prompt)
    return parse_json_response(raw)


def compute_combined_score(audio_result: dict, visual_result: dict) -> dict:
    """
    Calcule un score combiné à partir des analyses audio et visuelle.

    Pondération : 40% audio, 60% visuel (le visuel est plus fiable pour
    détecter les deepfakes et le contenu généré par IA).

    Args:
        audio_result: Résultat de l'analyse audio.
        visual_result: Résultat de l'analyse visuelle.

    Returns:
        Dictionnaire avec le score combiné, le label et un résumé.
    """
    audio_score = audio_result.get("score", 50)
    visual_score = visual_result.get("score", 50)

    combined_score = int(audio_score * 0.4 + visual_score * 0.6)
    combined_score = max(0, min(100, combined_score))

    if combined_score >= 67:
        label = "true"
    elif combined_score >= 34:
        label = "uncertain"
    else:
        label = "false"

    return {
        "combined_score": combined_score,
        "label": label,
        "audio": audio_result,
        "visual": visual_result,
    }