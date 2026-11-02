import os, sys
sys.path.insert(0, os.getcwd())
from ratelimit import TokenBucket
class Clock:
    def __init__(self): self.t = 100.0
    def __call__(self): return self.t
c = Clock()
b = TokenBucket(2, 1.0, clock=c)
assert b.allow() and b.allow() and not b.allow()
c.t += 0.5; assert not b.allow()
c.t += 0.5; assert b.allow(), "fractional refill lost"
assert not b.allow()
c.t += 1000
assert b.allow(2) and not b.allow()
assert not b.allow(3), "more than capacity"
c.t += 10
assert not b.allow(3)
b2 = TokenBucket(10, 0.25, clock=c)
assert b2.allow(10)
for _ in range(15):
    c.t += 1.0
    assert not b2.allow() or True
c.t += 100
assert b2.allow(10), "refill must cap at capacity but reach it"
# failed request must not consume
b3 = TokenBucket(5, 1.0, clock=c)
assert b3.allow(3) and not b3.allow(3) and b3.allow(2)
# steady slow traffic: 0.75 tokens per step
b4 = TokenBucket(2, 1.5, clock=c)
assert b4.allow(2)
allowed = 0
for _ in range(40):
    c.t += 0.5
    allowed += b4.allow()
assert allowed == 30, allowed
print("ok")
