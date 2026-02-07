# Contributing to DrishtiStream

Thank you for your interest in contributing to DrishtiStream.

## Important: Architectural Boundaries

Before contributing, please understand that DrishtiStream has **strict architectural boundaries**. This repository is a **virtual camera abstraction layer only**.

### ✅ In Scope

- Video file reading improvements
- FPS accuracy enhancements
- WebSocket reliability
- Configuration options
- Cloud storage integration (GCS, S3)
- Container optimization
- Documentation

### ❌ Out of Scope

The following belong in **DrishtiChokepointAgent**, not here:

- Machine learning / AI
- Object detection (YOLO, etc.)
- Analytics / metrics computation
- Heatmaps or visualizations
- Agent decision logic
- Any frame modification or overlay

## Development Setup

```bash
# Clone repository
git clone <repo-url>
cd DrishtiStream

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
uvicorn src.drishti_stream.main:app --reload
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep functions focused and small

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass
4. Update documentation if needed
5. Submit PR with clear description

## Questions?

Open an issue for discussion before making significant changes.
