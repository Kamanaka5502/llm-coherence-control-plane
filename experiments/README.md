# LLM Coherence Control Plane (Minimal Experiment)

This repository demonstrates a reproducible failure mode in recursive LLM-style refinement
and a minimal external control mechanism that prevents it.

## Problem
Unconstrained recursive “improve the previous response” loops exhibit monotonic coherence collapse.

## Method
We measure coherence (Kₜ) over iterative refinement:
- **Before**: no constraints, no reset, no compression
- **After**: explicit constraint preservation + periodic reset (ECP)

## Result
- Collapse is monotonic and accelerating
- Stabilization is bounded and persistent
- No model changes required

## Reproduce
```bash
pip install matplotlib
python experiments/plot_kt.py
