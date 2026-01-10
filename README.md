# Elyria Control Plane — Configuration

## Entropy Threshold (ENTROPY_MAX)

Elyria’s governance layer supports environment-driven calibration.

- **Env var:** `ELYRIA_ENTROPY_MAX`
- **Type:** float
- **Default:** `0.30`

### Recommended ranges
- **0.25–0.30** → conservative, higher stabilization
- **0.30–0.35** → balanced (recommended)
- **0.35–0.40** → permissive, higher throughput

### Usage
```bash
export ELYRIA_ENTROPY_MAX=0.35
python -m elyria_cp.app new
