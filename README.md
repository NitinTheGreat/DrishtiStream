# DrishtiStream

**Virtual Camera Abstraction Layer for Research-Grade Crowd Analytics**

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)]()

---

## Overview

DrishtiStream is a **virtual camera / sensor abstraction layer** that provides a real-time video stream simulating a CCTV feed. It is designed to be consumed by multiple downstream services in the Drishti ecosystem.

This repository is part of the **Drishti** multi-repo system for chokepoint-aware crowd risk assessment.
Local Testing
  ```
bash

# Terminal 1: Start server
cd "c:\Users\-THE-GREAT-\Downloads\Project Drishti\Ingestion"
pip install -r requirements.txt
uvicorn src.drishti_stream.main:app --host 0.0.0.0 --port 8000
```

```
bash
# Terminal 2: Test with Python client
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8000/ws/stream') as ws:
        for i in range(5):
            msg = json.loads(await ws.recv())
            print(f'Frame {msg[\"frame_id\"]} @ {msg[\"timestamp\"]:.3f}')
asyncio.run(test())
"
```
### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DRISHTI SYSTEM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────┐                                               │
│   │  DrishtiStream  │  ◄── in this repo we are here                 │
│   │  (This Repo)    │                                               │
│   │                 │                                               │
│   │  Virtual Camera │                                               │
│   └────────┬────────┘                                               │
│            │                                                        │
│            │ WebSocket: /ws/stream                                  │
│            │ (raw frames, JSON + base64 JPEG)                       │
│            ▼                                                        │
│   ┌─────────────────────────┐                                       │
│   │  DrishtiChokepointAgent │                                       │
│   │                         │                                       │
│   │  - Perception           │                                       │
│   │  - Flow Metrics         │                                       │
│   │  - Agentic Policy       │                                       │
│   └────────┬────────────────┘                                       │
│            │                                                        │
│            ▼                                                        │
│   ┌─────────────────┐                                               │
│   │ DrishtiDashboard│                                               │
│   │                 │                                               │
│   │  Visualization  │                                               │
│   └─────────────────┘                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What DrishtiStream Does

| Responsibility | Description |
|----------------|-------------|
| **Read Video** | Load video from local filesystem or cloud storage (GCS) |
| **Replay at Fixed FPS** | Emit frames at wall-clock-accurate intervals |
| **Loop Seamlessly** | Restart video transparently when it ends |
| **Serve Multiple Clients** | Allow concurrent WebSocket connections |
| **Remain Stateless** | No consumer-specific state |

---

## What DrishtiStream Does NOT Do

> [!CAUTION]
> This repository must behave like a **dumb camera**. The following are explicitly out of scope:

| ❌ Excluded | Rationale |
|-------------|-----------|
| Machine Learning | Belongs in DrishtiChokepointAgent |
| YOLO / Object Detection | Belongs in DrishtiChokepointAgent |
| Heatmaps / Analytics | Belongs in DrishtiChokepointAgent |
| Metadata Extraction | Belongs in DrishtiChokepointAgent |
| Agents / Decision Logic | Belongs in DrishtiChokepointAgent |
| Dashboards / UI | Belongs in DrishtiDashboard |

---

## Output Contract

### Endpoint

```
WebSocket: /ws/stream
```

### Message Format

Each frame pushed to connected clients contains:

```json
{
  "source": "DrishtiStream",
  "version": "v1.0",
  "frame_id": 1234,
  "timestamp": 1707321234.567,
  "fps": 30,
  "image": "<base64-encoded JPEG>"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source` | `string` | Fixed identifier: `"DrishtiStream"` |
| `version` | `string` | Semantic version of the stream protocol |
| `frame_id` | `integer` | Monotonically increasing frame counter (never resets) |
| `timestamp` | `float` | UNIX timestamp in seconds (wall-clock emission time) |
| `fps` | `integer` | Declared stream FPS |
| `image` | `string` | Base64-encoded JPEG frame |

### Guarantees

- ✅ Frames are **in order**
- ✅ Frames are **time-accurate** (wall-clock aligned to ±1 frame)
- ✅ Frames are **unmodified** (no overlays, annotations, or processing)
- ✅ `frame_id` is **monotonically increasing** (never resets, even on video loop)
- ✅ Multiple clients receive frames **independently**

---

## Quick Start

### Prerequisites

- Python 3.11+
- A video file (MP4, AVI, MKV)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd DrishtiStream

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

1. **Place a video file** in `./data/sample.mp4` (or update `config.yaml`)

2. **Start the server**:
```bash
uvicorn src.drishti_stream.main:app --host 0.0.0.0 --port 8000
```

3. **Verify it's running**:
```bash
curl http://localhost:8000/health
```

4. **Connect a WebSocket client** (see examples below)

---

## Configuration

### config.yaml

```yaml
stream:
  name: "drishti-stream-primary"
  version: "v1.0"
  
video:
  path: "./data/sample.mp4"  # or gs://bucket/path/to/video.mp4
  fps: 30
  loop: true
  jpeg_quality: 85

server:
  host: "0.0.0.0"
  port: 8000

logging:
  level: "INFO"
  format: "json"
```

### Environment Variables

Environment variables override config file values:

| Variable | Description | Default |
|----------|-------------|---------|
| `DRISHTI_VIDEO_PATH` | Path to video file | `./data/sample.mp4` |
| `DRISHTI_FPS` | Target FPS | `30` |
| `DRISHTI_LOOP` | Enable looping | `true` |
| `DRISHTI_JPEG_QUALITY` | JPEG quality (1-100) | `85` |
| `DRISHTI_PORT` | Server port | `8000` |
| `PORT` | Server port (Cloud Run) | `8000` |
| `DRISHTI_LOG_LEVEL` | Log level | `INFO` |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check for orchestration |
| `/metrics` | GET | Detailed streaming metrics |
| `/ws/stream` | WebSocket | Real-time frame streaming |
| `/docs` | GET | OpenAPI documentation |

---

## WebSocket Client Examples

### Python

```python
import asyncio
import websockets
import json

async def consume_stream():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as ws:
        print("Connected to DrishtiStream")
        async for message in ws:
            frame = json.loads(message)
            print(f"Frame {frame['frame_id']} @ {frame['timestamp']:.3f}")
            # Decode image: base64.b64decode(frame['image'])

asyncio.run(consume_stream())
```

### JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');

ws.onopen = () => console.log('Connected to DrishtiStream');

ws.onmessage = (event) => {
  const frame = JSON.parse(event.data);
  console.log(`Frame ${frame.frame_id} @ ${frame.timestamp}`);
  // Display: document.getElementById('img').src = 'data:image/jpeg;base64,' + frame.image;
};
```

---

## Docker Deployment

### Build and Run Locally

```bash
# Build image
docker build -t drishti-stream .

# Run with local video
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data:ro \
  drishti-stream
```

### Docker Compose

```bash
docker-compose up
```

---

## Google Cloud Run Deployment

### Prerequisites

- Google Cloud SDK installed and configured
- Docker installed
- A GCS bucket with your video file (optional)

### Deploy

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/drishti-stream

# Deploy to Cloud Run
gcloud run deploy drishti-stream \
  --image gcr.io/YOUR_PROJECT_ID/drishti-stream \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DRISHTI_VIDEO_PATH=gs://your-bucket/video.mp4" \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 5
```

### Recommended Cloud Run Settings

| Setting | Recommended Value | Reason |
|---------|-------------------|--------|
| CPU | 1 | Sufficient for encoding |
| Memory | 1Gi | Video frame buffering |
| Concurrency | 80 | WebSocket connections per instance |
| Min instances | 1 | Avoid cold starts |
| Max instances | 5 | Scale based on client count |

> [!IMPORTANT]
> Cloud Run automatically sets the `PORT` environment variable. DrishtiStream reads this automatically.

---

## Project Structure

```
DrishtiStream/
├── src/
│   └── drishti_stream/
│       ├── __init__.py         # Package initialization
│       ├── main.py             # FastAPI application entry
│       ├── config.py           # Configuration loader
│       ├── stream/
│       │   ├── __init__.py
│       │   ├── video_reader.py     # OpenCV video reading + GCS
│       │   ├── frame_scheduler.py  # Wall-clock FPS timing
│       │   └── websocket.py        # WebSocket broadcast
│       └── models/
│           ├── __init__.py
│           └── messages.py     # FrameMessage schema
├── tests/                      # Test suite
├── data/                       # Video files (gitignored)
├── config.yaml                 # Configuration file
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local development
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Modern Python packaging
└── README.md                   # This file
```

---

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| Missing video file | Fail fast on startup |
| Corrupt video | Fail fast on startup |
| Zero FPS configured | Validation error on startup |
| Client disconnects | Graceful removal from broadcast |
| Video ends | Loop (if enabled) or continue broadcasting last frame |
| Slow client | Non-blocking send with timeout, auto-disconnect |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Team

DrishtiStream is maintained as part of the Drishti research project.

**Repository Purpose**: Provide a stable, deterministic, camera-agnostic video source for parallel team development and reproducible research.
