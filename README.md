# LLM Coherence Control Plane (ECP)

Demonstrating and mitigating coherence collapse in recursive LLM interaction
via an explicit external control plane.

## Core Claim

Coherence in LLM systems is not an intrinsic property of the model.
It is a managed outcome of constraint-aware interaction design.

## Demonstrating Causality

**Before**
Unchecked recursion → coherence collapse (measured)

**After**
ECP active → sustained coherence under load (verified)

Same model.  
Same prompt.  
Same runtime.

**Only difference:**  
The system enforces bounds.
## What This Repo Is

This repository provides:
- A minimal control-plane specification for LLM interaction
- Instrumentation hooks for coherence metrics (Kₜ, Rₜ)
- Reset, segmentation, and guard policies external to the model
- Reproducible demonstrations of failure vs. stabilized behavior

## What This Is Not

- Not a new model
- Not prompt engineering
- Not fine-tuning
- Not speculative theory

This is operational infrastructure.
## Prior Art & Attribution

If you build on this work, please cite this repository.
This project establishes a control-plane approach to LLM coherence
as operational infrastructure, not a modeling technique.

## License

MIT — open core.
## Citation

If you use or build upon this work, please cite the repository.
See `CITATION.cff` for the preferred citation format.

