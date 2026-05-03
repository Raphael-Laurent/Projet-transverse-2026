"""
Module de téléchargement de vidéos depuis les réseaux sociaux.

Utilise yt-dlp pour télécharger des vidéos depuis TikTok, YouTube, Instagram, etc.
"""

import yt_dlp
import os
import logging

logger = logging.getLogger(__name__)

# Répertoire de base du projet (pour des chemins absolus fiables)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DownloadError(Exception):
    """Erreur levée lorsque le téléchargement échoue."""
    pass


def download_video(url: str, output_dir: str = None) -> str:
    """
    Télécharge une vidéo depuis une URL (TikTok, YouTube, Instagram, etc.).

    Args:
        url: URL de la vidéo à télécharger.
        output_dir: Dossier de destination. Par défaut: <projet>/videos/

    Returns:
        Chemin absolu vers le fichier vidéo téléchargé.

    Raises:
        DownloadError: Si le téléchargement échoue (URL invalide, vidéo privée, réseau, etc.)
    """
    if not url or not url.strip():
        raise DownloadError("L'URL fournie est vide.")

    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, "videos")

    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Téléchargement de la vidéo : {url}")
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if not os.path.exists(file_path):
                raise DownloadError(f"Le fichier téléchargé est introuvable : {file_path}")

            logger.info(f"Vidéo téléchargée : {file_path}")
            return file_path

    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(f"Impossible de télécharger la vidéo : {e}")
    except Exception as e:
        raise DownloadError(f"Erreur inattendue lors du téléchargement : {e}")
