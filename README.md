# 🔍 Projet-transverse-2026 — Détecteur de Deepfakes

Outil de détection de deepfakes et de contenus générés par IA sur les réseaux sociaux (TikTok, YouTube, Instagram, etc.).

## Architecture

```
URL vidéo  ──►  download.py (yt-dlp)  ──►  vidéo.mp4
                                               │
                      ┌────────────────────────┤
                      ▼                        ▼
              transcription.py          image_conversion.py
              (Whisper + FFmpeg)        (OpenCV + LLaVA/OCR)
                      │                        │
                      ▼                        ▼
               Texte audio             Données visuelles
                      │                        │
                      └────────┬───────────────┘
                               ▼
                          analysis.py
                        (Ollama/Mistral)
                               │
                               ▼
                     Score combiné (JSON)
                    40% audio + 60% visuel
```

## Prérequis

### Python 3.10+

### Packages Python
```bash
pip install -r requirements.txt
```

### Outils système

| Outil | Rôle | Installation (Windows) |
|-------|------|------------------------|
| **FFmpeg** | Extraction audio (requis par Whisper) | `winget install Gyan.FFmpeg` |
| **Tesseract OCR** | Lecture de texte dans les images (optionnel) | `winget install UB-Mannheim.TesseractOCR` |
| **Ollama** | LLM local pour l'analyse | [ollama.com](https://ollama.com/download/windows) |

### Modèles Ollama
```bash
ollama pull mistral    # Analyse textuelle
ollama pull llava      # Analyse visuelle (optionnel mais recommandé)
```

## Utilisation

### Démarrer le serveur
```bash
python main.py
```
Le serveur démarre sur `http://localhost:5000`.

### Endpoints API

#### `GET /api/status`
Vérifie l'état des dépendances système.

```bash
curl http://localhost:5000/api/status
```

#### `POST /api/analyze`
Lance l'analyse complète d'une vidéo.

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@user/video/123"}'
```

**Réponse** :
```json
{
  "url": "...",
  "language": "fr",
  "combined_score": 72,
  "label": "true",
  "audio": {
    "text_length": 450,
    "result": {"score": 80, "label": "true", "explanation": "..."}
  },
  "visual": {
    "frames_analyzed": 5,
    "result": {"score": 67, "label": "true", "explanation": "..."}
  }
}
```

### Labels de score
| Score | Label | Signification |
|-------|-------|---------------|
| 67–100 | `true` | Contenu probablement authentique |
| 34–66 | `uncertain` | Impossible de conclure |
| 0–33 | `false` | Contenu probablement manipulé / généré par IA |

## Structure du projet

```
├── main.py              # API Flask (point d'entrée)
├── download.py          # Téléchargement vidéo (yt-dlp)
├── transcription.py     # Transcription audio (Whisper)
├── image_conversion.py  # Analyse visuelle (OpenCV + LLaVA)
├── analysis.py          # Analyse LLM (Ollama/Mistral)
├── static/              # Interface web (futur)
├── requirements.txt     # Dépendances Python
└── .gitignore
```
