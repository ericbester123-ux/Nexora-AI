"""
Shared rate-limiter instance (slowapi), keyed by client remote address.

Imported both by `app.main` (to register it on the FastAPI app) and by
individual endpoint modules (to apply the `@limiter.limit(...)` decorator).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
