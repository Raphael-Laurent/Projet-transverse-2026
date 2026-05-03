"""
Module de transcription audio.

Utilise OpenAI Whisper pour transcrire l'audio d'une vidéo en texte.
Nécessite FFmpeg pour l'extraction audio.
"""

import shutil
import logging

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Erreur levée lorsque la transcription échoue."""
    pass


def check_ffmpeg() -> bool:
    """Vérifie que FFmpeg est installé et accessible dans le PATH."""
    return shutil.which("ffmpeg") is not None


def transcribe_video(video_path: str, model_size: str = "base") -> dict:
    """
    Transcrit l'audio d'une vidéo en texte via Whisper.

    Args:
        video_path: Chemin vers le fichier vidéo.
        model_size: Taille du modèle Whisper ('tiny', 'base', 'small', 'medium', 'large').

    Returns:
        Dictionnaire contenant :
            - text (str): Texte transcrit
            - language (str): Langue détectée

    Raises:
        TranscriptionError: Si FFmpeg est absent ou si la transcription échoue.
    """
    if not check_ffmpeg():
        raise TranscriptionError(
            "FFmpeg n'est pas installé. Installez-le avec : winget install Gyan.FFmpeg"
        )

    try:
        import whisper
    except ImportError:
        raise TranscriptionError(
            "Le package 'openai-whisper' n'est pas installé. "
            "Installez-le avec : pip install openai-whisper"
        )

    try:
        logger.info(f"Chargement du modèle Whisper ({model_size})...")
        model = whisper.load_model(model_size)

        logger.info(f"Transcription de : {video_path}")
        result = model.transcribe(video_path)

        text = result.get("text", "").strip()
        language = result.get("language", "unknown")

        logger.info(f"Transcription terminée — langue détectée : {language}, longueur : {len(text)} chars")

        return {
            "text": text,
            "language": language,
        }

    except Exception as e:
        raise TranscriptionError(f"Erreur lors de la transcription : {e}")