"""StunAssure verification core.

Prove, cheaply and fail-safe, that each batch of fish was rendered insensible and stayed
insensible until death: ``simulate → verify → certify → report``. The core has zero runtime
dependencies (pure standard library) so it runs anywhere, including offline on the poorest vessel.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
