"""citation-gate: LLM claims must cite records you actually sent."""

from .gate import verify_claims

__version__ = "0.1.0"
__all__ = ["verify_claims"]
