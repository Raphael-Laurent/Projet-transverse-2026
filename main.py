"""
API Flask — Point d'entrée du projet de détection de deepfakes.

Expose une API REST pour analyser des vidéos de réseaux sociaux
et détecter les deepfakes / contenus générés par IA.
"""

import os
import shutil
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from download import download_video, DownloadError
from transcription import transcribe_video, TranscriptionError, check_ffmpeg
from image_conversion import analyze_video_frames, ImageAnalysisError
from analysis import (
    analyze_audio,
    analyze_visual,
    compute_combined_score,
    check_ollama,
    AnalysisError,
)

# ── Configuration ───────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")
CORS(app)


# ── Utilitaires ─────────────────────────────────────────────────

def cleanup(video_path: str, frames_folder: str = None):
    """Supprime les fichiers temporaires (vidéo + frames)."""
    if frames_folder is None:
        frames_folder = os.path.join(BASE_DIR, "frames")

    if video_path and os.path.exists(video_path):
        os.remove(video_path)
        logger.info(f"Fichier supprimé : {video_path}")

    if os.path.exists(frames_folder):
        shutil.rmtree(frames_folder)
        logger.info(f"Dossier supprimé : {frames_folder}")


# ── Routes API ──────────────────────────────────────────────────

@app.route("/")
def index():
    """Sert la page web d'accueil (future interface)."""
    static_dir = os.path.join(BASE_DIR, "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(static_dir, "index.html")
    return jsonify({
        "message": "API de détection de deepfakes",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/analyze": "Analyser une vidéo depuis son URL",
            "GET /api/status": "Vérifier l'état des dépendances",
        }
    })


@app.route("/api/status", methods=["GET"])
def status():
    """
    Vérifie l'état des dépendances système.

    Returns:
        JSON avec le statut de chaque dépendance.
    """
    ffmpeg_ok = check_ffmpeg()
    ollama_ok = check_ollama()
    tesseract_path = shutil.which("tesseract")

    all_ok = ffmpeg_ok and ollama_ok

    return jsonify({
        "status": "ready" if all_ok else "missing_dependencies",
        "dependencies": {
            "ffmpeg": {"installed": ffmpeg_ok, "path": shutil.which("ffmpeg")},
            "ollama": {"installed": ollama_ok, "url": "http://localhost:11434"},
            "tesseract": {"installed": tesseract_path is not None, "path": tesseract_path},
        }
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Analyse complète d'une vidéo pour détecter un deepfake.

    Body JSON attendu :
        {
            "url": "https://www.tiktok.com/...",
            "use_vision": true  (optionnel, défaut: true)
        }

    Returns:
        JSON structuré avec les scores audio, visuel et combiné.
    """
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Le champ 'url' est requis."}), 400

    url = data["url"].strip()
    use_vision = data.get("use_vision", True)
    video_path = None

    try:
        # ── Étape 1 : Téléchargement ────────────────────────────
        logger.info(f"=== Nouvelle analyse : {url} ===")
        video_path = download_video(url)

        # ── Étape 2 : Transcription audio ───────────────────────
        logger.info("Transcription audio en cours...")
        try:
            transcription = transcribe_video(video_path)
            audio_text = transcription["text"]
            language = transcription["language"]
        except TranscriptionError as e:
            logger.warning(f"Transcription échouée : {e}")
            audio_text = ""
            language = "unknown"

        # ── Étape 3 : Analyse visuelle ──────────────────────────
        logger.info("Analyse visuelle en cours...")
        try:
            visual_data = analyze_video_frames(video_path, use_vision=use_vision)
        except ImageAnalysisError as e:
            logger.warning(f"Analyse visuelle échouée : {e}")
            visual_data = {"ocr_text": "", "vision_descriptions": [], "frame_count": 0}

        # ── Étape 4 : Analyse LLM ──────────────────────────────
        logger.info("Analyse LLM en cours...")
        audio_result = analyze_audio(audio_text)
        visual_result = analyze_visual(
            visual_data["ocr_text"],
            visual_data["vision_descriptions"],
        )

        # ── Étape 5 : Score combiné ─────────────────────────────
        combined = compute_combined_score(audio_result, visual_result)

        result = {
            "url": url,
            "language": language,
            "combined_score": combined["combined_score"],
            "label": combined["label"],
            "audio": {
                "text_length": len(audio_text),
                "result": audio_result,
            },
            "visual": {
                "frames_analyzed": visual_data["frame_count"],
                "ocr_text_length": len(visual_data["ocr_text"]),
                "vision_descriptions_count": len(visual_data["vision_descriptions"]),
                "result": visual_result,
            },
        }

        logger.info(
            f"=== Analyse terminée — Score: {combined['combined_score']}/100 "
            f"({combined['label']}) ==="
        )
        return jsonify(result)

    except DownloadError as e:
        logger.error(f"Erreur téléchargement : {e}")
        return jsonify({"error": f"Téléchargement échoué : {e}"}), 400

    except AnalysisError as e:
        logger.error(f"Erreur analyse : {e}")
        return jsonify({"error": f"Analyse échouée : {e}"}), 503

    except Exception as e:
        logger.error(f"Erreur inattendue : {e}", exc_info=True)
        return jsonify({"error": f"Erreur interne : {e}"}), 500

    finally:
        if video_path:
            cleanup(video_path)


# ── Lancement ───────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Démarrage du serveur Flask...")
    logger.info("Interface : http://localhost:5000")
    logger.info("API Status : http://localhost:5000/api/status")
    app.run(debug=False, host="0.0.0.0", port=5000)
