# DrishtiStream

**Virtual Camera Abstraction Layer for Research-Grade Crowd Analytics**

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)]()

---

## Overview

DrishtiStream is a **virtual camera / sensor abstraction layer** that provides a real-time video stream simulating a CCTV feed. It is designed to be consumed by multiple downstream services in the Drishti ecosystem.

This repository is part of the **Drishti** multi-repo system for chokepoint-aware crowd risk assessment.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DRISHTI SYSTEM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────┐                                               │
│   │  DrishtiStream  │  ◄── You are here                             │
│   │  (This Repo)    │                                               │
│   │                 │                                               │
│   │  Virtual Camera │                                               │
│   └────────┬────────┘                                               │
│            │                                                        │
│            │ WebSocket: /ws/stream                                  │
│            │ (raw frames)                                           │
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
| `frame_id` | `integer` | Monotonically increasing frame counter |
| `timestamp` | `float` | UNIX timestamp in seconds |
| `fps` | `integer` | Declared stream FPS |
| `image` | `string` | Base64-encoded JPEG frame |

### Guarantees

- ✅ Frames are **in order**
- ✅ Frames are **time-accurate** (wall-clock aligned)
- ✅ Frames are **unmodified** (no overlays, annotations, or processing)

---

## Configuration

DrishtiStream is configured via `config.yaml` and environment variables.

### config.yaml

```yaml
stream:
  name: "drishti-stream-primary"
  version: "v1.0"
  
video:
  path: "./data/sample.mp4"  # or gs://bucket/path/to/video.mp4
  fps: 30
  loop: true

server:
  host: "0.0.0.0"
  port: 8000
```

### Environment Variables

Environment variables override config file values:

| Variable | Description |
|----------|-------------|
| `DRISHTI_VIDEO_PATH` | Path to video file |
| `DRISHTI_FPS` | Target FPS |
| `DRISHTI_LOOP` | Enable looping (`true`/`false`) |
| `DRISHTI_PORT` | Server port |

---

## Downstream Usage

### Connecting via WebSocket (Python)

```python
import asyncio
import websockets
import json

async def consume_stream():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            frame = json.loads(message)
            print(f"Frame {frame['frame_id']} @ {frame['timestamp']}")
            # Process frame['image'] as needed

asyncio.run(consume_stream())
```

### Connecting via WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');

ws.onmessage = (event) => {
  const frame = JSON.parse(event.data);
  console.log(`Frame ${frame.frame_id} @ ${frame.timestamp}`);
  // Process frame.image as needed
};
```

---

## Deployment

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn src.drishti_stream.main:app --reload
```

### Docker

```bash
# Build
docker build -t drishti-stream .

# Run
docker run -p 8000:8000 -v $(pwd)/data:/app/data drishti-stream
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/drishti-stream

# Deploy
gcloud run deploy drishti-stream \
  --image gcr.io/PROJECT_ID/drishti-stream \
  --platform managed \
  --allow-unauthenticated
```

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
│       │   ├── video_reader.py     # Video file reading
│       │   ├── frame_scheduler.py  # FPS-accurate timing
│       │   └── websocket.py        # WebSocket endpoint
│       └── models/
│           └── messages.py     # Output message schema
├── tests/                      # Test suite
├── config.yaml                 # Configuration file
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

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
