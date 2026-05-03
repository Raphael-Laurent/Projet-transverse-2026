"""
Module d'analyse visuelle des vidéos.

Extrait des frames à intervalles réguliers sur toute la durée de la vidéo,
puis analyse leur contenu via OCR (Tesseract) et/ou vision IA (Ollama/LLaVA).
"""

import cv2
import os
import base64
import logging
import requests
from PIL import Image

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# URL de l'API Ollama pour les modèles de vision
OLLAMA_API_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "llava"


class ImageAnalysisError(Exception):
    """Erreur levée lorsque l'analyse visuelle échoue."""
    pass


def extract_frames(video_path: str, output_folder: str = None, max_frames: int = 5) -> list[str]:
    """
    Extrait des frames à intervalles réguliers sur toute la durée de la vidéo.

    Au lieu de prendre les N premières frames (= quelques millisecondes),
    cette version échantillonne uniformément sur toute la durée.

    Args:
        video_path: Chemin vers le fichier vidéo.
        output_folder: Dossier de sortie. Par défaut: <projet>/frames/
        max_frames: Nombre de frames à extraire.

    Returns:
        Liste des chemins vers les images extraites.

    Raises:
        ImageAnalysisError: Si la vidéo ne peut pas être lue.
    """
    if output_folder is None:
        output_folder = os.path.join(BASE_DIR, "frames")

    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ImageAnalysisError(f"Impossible d'ouvrir la vidéo : {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if total_frames <= 0:
        cap.release()
        raise ImageAnalysisError("La vidéo ne contient aucune frame.")

    # Calculer les indices de frames à extraire (répartis uniformément)
    if total_frames <= max_frames:
        frame_indices = list(range(total_frames))
    else:
        step = total_frames / max_frames
        frame_indices = [int(step * i) for i in range(max_frames)]

    duration = total_frames / fps if fps > 0 else 0
    logger.info(
        f"Vidéo : {total_frames} frames, {fps:.1f} fps, {duration:.1f}s — "
        f"extraction de {len(frame_indices)} frames"
    )

    saved_paths = []
    for idx, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Impossible de lire la frame {frame_idx}")
            continue

        frame_path = os.path.join(output_folder, f"frame_{idx}.jpg")
        cv2.imwrite(frame_path, frame)
        saved_paths.append(frame_path)

    cap.release()
    logger.info(f"{len(saved_paths)} frames extraites dans {output_folder}")
    return saved_paths


def image_to_text_ocr(image_path: str) -> str:
    """
    Extrait le texte d'une image via OCR (Tesseract).

    Args:
        image_path: Chemin vers l'image.

    Returns:
        Texte extrait de l'image.
    """
    try:
        import pytesseract
        img = Image.open(image_path)
        return pytesseract.image_to_string(img).strip()
    except ImportError:
        logger.warning("pytesseract non installé, OCR indisponible.")
        return ""
    except Exception as e:
        logger.warning(f"Erreur OCR sur {image_path} : {e}")
        return ""


def image_to_base64(image_path: str) -> str:
    """Encode une image en base64 pour l'API Ollama vision."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_frame_with_vision(image_path: str) -> str:
    """
    Analyse une frame via un modèle de vision IA (LLaVA via Ollama).

    Args:
        image_path: Chemin vers l'image à analyser.

    Returns:
        Description textuelle du contenu de l'image.
    """
    img_b64 = image_to_base64(image_path)

    prompt = (
        "Décris brièvement cette image extraite d'une vidéo de réseau social. "
        "Indique si tu détectes des signes de manipulation ou de génération par IA "
        "(artefacts visuels, incohérences, texte superposé suspect, etc.). "
        "Sois concis."
    )

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": VISION_MODEL,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    except requests.ConnectionError:
        logger.warning("Ollama non accessible pour l'analyse vision.")
        return ""
    except Exception as e:
        logger.warning(f"Erreur analyse vision sur {image_path} : {e}")
        return ""


def analyze_video_frames(video_path: str, max_frames: int = 5, use_vision: bool = True) -> dict:
    """
    Pipeline complet d'analyse visuelle d'une vidéo.

    Extrait des frames, les analyse par OCR et/ou vision IA, et retourne
    les résultats consolidés.

    Args:
        video_path: Chemin vers la vidéo.
        max_frames: Nombre de frames à analyser.
        use_vision: Si True, utilise le modèle de vision IA en plus de l'OCR.

    Returns:
        Dictionnaire contenant :
            - ocr_text (str): Texte extrait par OCR (concaténé)
            - vision_descriptions (list[str]): Descriptions par vision IA
            - frame_count (int): Nombre de frames analysées
    """
    try:
        frame_paths = extract_frames(video_path, max_frames=max_frames)
    except ImageAnalysisError as e:
        logger.error(f"Extraction de frames échouée : {e}")
        return {"ocr_text": "", "vision_descriptions": [], "frame_count": 0}

    ocr_texts = []
    vision_descriptions = []

    for path in frame_paths:
        # OCR (Tesseract)
        ocr_result = image_to_text_ocr(path)
        if ocr_result:
            ocr_texts.append(ocr_result)

        # Vision IA (LLaVA)
        if use_vision:
            vision_result = analyze_frame_with_vision(path)
            if vision_result:
                vision_descriptions.append(vision_result)

    result = {
        "ocr_text": "\n".join(ocr_texts),
        "vision_descriptions": vision_descriptions,
        "frame_count": len(frame_paths),
    }

    logger.info(
        f"Analyse visuelle terminée — {len(ocr_texts)} textes OCR, "
        f"{len(vision_descriptions)} descriptions vision"
    )
    return result