from download import download_tiktok
from transcription import transcribe_video

url = input("Entrez l'URL de la vidéo TikTok : ")

video_path = download_tiktok(url)

print(f"Vidéo téléchargée : {video_path}")

text = transcribe_video(video_path)

print(f"Transcription : {text}")