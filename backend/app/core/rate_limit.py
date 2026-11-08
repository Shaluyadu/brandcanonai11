import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from app.core.exceptions import BrandCanonException


class InMemoryRateLimiter:
    """
    Sliding-window in-memory rate limiter for authentication routes.
    Prevents brute-force credential stuffing and denial of service.
    """
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request, key_prefix: str = "auth"):
        client_ip = "unknown"
        # Extract real client IP if behind reverse proxy / load balancer
        forwarded_for = request.headers.get("x-forwarded-for")
        real_ip = request.headers.get("x-real-ip")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif real_ip:
            client_ip = real_ip.strip()
        elif request.client:
            client_ip = request.client.host

        key = f"{key_prefix}:{client_ip}"
        now = time.time()
        window_start = now - self.window_seconds

        # Prune older entries
        self.requests[key] = [t for t in self.requests[key] if t > window_start]

        if len(self.requests[key]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.requests[key][0]))
            raise BrandCanonException(
                status_code=429,
                code="RATE_LIMIT_EXCEEDED",
                message=f"Too many requests from this IP address. Please retry in {max(1, retry_after)} seconds."
            )

        self.requests[key].append(now)


auth_rate_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)

