from download import download_tiktok
from transcription import transcribe_video
from analysis import analyze_text

url = input("Entrez l'URL de la vidéo TikTok : ")

video_path = download_tiktok(url)
text = transcribe_video(video_path)

analysis = analyze_text(text)
print("Résumé :", analysis)

#https://www.tiktok.com/@im_nuee/video/7310321641316306209?q=nu%C3%A9e&t=1776024187566