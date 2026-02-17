# HTR Service

Backend service for medieval manuscript recognition — text (syllables) via Kraken HTR and neume detection via YOLOv8.

## Architecture

The pipeline has two parallel branches that share Kraken's text segmentation:

1. **Text recognition**: Default Kraken segmentation → Tridis HTR model → Latin syllabification (pyphen) → syllables with bounding boxes
2. **Neume detection**: Kraken's text boundary polygons are used to mask out text from the RGB image (filled with surrounding parchment color), then YOLOv8 + SAHI runs object detection on the masked image → neume bounding boxes with class labels

Text and neumes look similar at small scales, so masking text before neume detection prevents confusion. SAHI tiles the large manuscript images (e.g. 3328×4992) into overlapping patches for reliable small-object detection.

## Prerequisites

- Python 3.11 or 3.12
- The TRIDIS HTR model (`Tridis_Medieval_EarlyModern.mlmodel`) in `models/`
- Latin liturgical hyphenation patterns (`hyph_la_liturgical.dic`) in `patterns/`
- A YOLOv8 neume detection model in `models/` (optional — neume detection is skipped if no model is present)

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Running the Service

```bash
python -m htr_service
```

The service runs on `http://localhost:8000` with auto-reload enabled.

## API Endpoints

### POST /recognize

Recognize syllables and detect neumes in a manuscript image. Returns results via SSE (Server-Sent Events) with progress stages: segmenting → recognizing → syllabifying → detecting.

**Request:**
- `image` (file): Image file to process
- `region` (optional, JSON string): Crop region `{"x": int, "y": int, "width": int, "height": int}`

**Response:**
```json
{
  "syllables": [
    {
      "text": "glo",
      "bbox": {"x": 100, "y": 200, "width": 50, "height": 30},
      "confidence": 0.95,
      "line_index": 0
    }
  ],
  "lines": [
    {
      "text": "gloria",
      "bbox": {"x": 100, "y": 200, "width": 150, "height": 30}
    }
  ],
  "neumes": [
    {
      "type": "punctum",
      "bbox": {"x": 120, "y": 170, "width": 15, "height": 12},
      "confidence": 0.85
    }
  ]
}
```

**Example:**
```bash
curl -X POST -F "image=@manuscript.jpg" http://localhost:8000/recognize
```

With region:
```bash
curl -X POST \
  -F "image=@manuscript.jpg" \
  -F 'region={"x": 100, "y": 200, "width": 500, "height": 300}' \
  http://localhost:8000/recognize
```

### POST /contribute

Submit annotations (text syllables + neume bounding boxes) for training data. Stores the image and a JSON annotation manifest.

### GET /health

Health check endpoint. Returns `{"status": "ok"}`.

## Training Data

Contributions are stored as:

```
contributions/<uuid>/
├── image.jpg
└── annotations.json
```

The YOLO export pipeline (`training/yolo_export.py`) converts stored contributions into YOLO training format — masking text from each image and writing normalized bounding box labels. Neume class mappings are defined in `neume_classes.yaml`.
