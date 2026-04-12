from download import download_tiktok

url = input("Entrez l'URL de la vidéo TikTok : ")

video_path = download_tiktok(url)

print(f"Vidéo téléchargée : {video_path}")