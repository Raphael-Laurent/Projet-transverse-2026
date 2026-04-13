import cv2
import os
from PIL import Image
import pytesseract

def extract_frames(video_path, output_folder="frames", max_frames=5):
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    count = 0
    saved = 0

    while saved < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imwrite(f"{output_folder}/frame_{saved}.jpg", frame)
        saved += 1
        
    cap.release()


def image_to_text(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img)


def video_to_image_text(video_path):
    extract_frames(video_path)

    text = ""

    if not os.path.exists("frames"):  # 👈 sécurité
        return ""

    for file in os.listdir("frames"):
        if file.endswith(".jpg"):
            text += image_to_text(f"frames/{file}") + "\n"

    return text