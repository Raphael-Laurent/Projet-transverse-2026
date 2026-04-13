from download import download_tiktok
from transcription import transcribe_video
from image_conversion import video_to_image_text
from analysis import analyze_text, analyze_image_text
import os
import shutil

def cleanup(video_path, frames_folder="frames"):
    # supprimer vidéo
    if os.path.exists(video_path):
        os.remove(video_path)

    """
    # supprimer dossier frames
    if os.path.exists(frames_folder):
        shutil.rmtree(frames_folder)
    """
     
def main():
    url = input("URL TikTok : ")

    video_path = download_tiktok(url)

    audio_text = transcribe_video(video_path)
    image_text = video_to_image_text(video_path)

    print(len(audio_text))
    
    print("Analyse audio...")
    audio_result = analyze_text(audio_text)

    
    print("Analyse image...")
    image_result = analyze_image_text(image_text)
    
    print("\n=== RESULTATS ===")
    print("Audio:", audio_result)
    print("Image:", image_result)
    
    cleanup(video_path)

if __name__ == "__main__":
    main()
    

