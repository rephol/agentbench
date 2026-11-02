import time


class TokenBucket:
    """Token bucket rate limiter.

    Holds up to `capacity` tokens and starts full. Tokens refill continuously at
    `rate` tokens per second (fractions accumulate) and never exceed `capacity`.
    `allow(n=1)` takes n tokens and returns True if enough were available;
    otherwise it takes nothing and returns False. Asking for more than
    `capacity` tokens is never allowed.
    """

    def __init__(self, capacity, rate, clock=time.monotonic):
        self.capacity = capacity
        self.rate = rate
        self.clock = clock
        self.tokens = capacity
        self.last = clock()

    def _refill(self):
        now = self.clock()
        added = int((now - self.last) * self.rate)
        self.tokens = min(self.capacity, self.tokens + added)
        self.last = now

    def allow(self, n=1):
        self._refill()
        if n > self.tokens:
            return False
        self.tokens -= n
        return True
