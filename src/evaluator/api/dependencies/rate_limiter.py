"""In-memory sliding window rate limiting dependency."""

from collections import defaultdict
import time
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter per client IP or user identity."""

    def __init__(self, window_seconds: float = 60.0) -> None:
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_key: str, max_requests: int) -> tuple[bool, int]:
        """Check if client request is within threshold; returns (allowed, retry_after)."""
        now = time.time()
        window_start = now - self._window_seconds

        # Prune old timestamps
        history = [ts for ts in self._requests[client_key] if ts > window_start]
        self._requests[client_key] = history

        if len(history) >= max_requests:
            earliest = history[0]
            retry_after = max(1, int(self._window_seconds - (now - earliest)))
            return False, retry_after

        self._requests[client_key].append(now)
        return True, 0

    def reset(self) -> None:
        """Clear all recorded rate limit windows."""
        self._requests.clear()


# Global rate limiter instance
_limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests_per_minute: int = 60):
    """Dependency factory checking client rate limits against a configured requests-per-minute threshold."""

    def check_rate_limit(request: Request) -> None:
        client_ip = request.client.host if request.client else "127.0.0.1"
        allowed, retry_after = _limiter.is_allowed(client_ip, max_requests_per_minute)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {max_requests_per_minute} requests per minute.",
                headers={"Retry-After": str(retry_after)},
            )

    return check_rate_limit

