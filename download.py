import yt_dlp
import os

def download_tiktok(url : str, output_dir: str = "videos") -> str:
    
    os.makedirs(output_dir, exist_ok=True) # Créé le dossier de sortie s'il n'existe pas déjà
    
    output_path = os.path.join(output_dir, '%(id)s.%(ext)s')
    
    ydl_opts = {
        "outtmpl": output_path,
        "format": "mp4",
        "quiet": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl :
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        
    return file_path 