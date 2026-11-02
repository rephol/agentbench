import os, sys
sys.path.insert(0, os.getcwd())
from datetime import datetime, timezone, timedelta
from logparse import parse_line, summarize
r = parse_line('127.0.0.1 - frank [10/Oct/2023:13:55:36 +0000] "GET /a/b.html?x=1 HTTP/1.1" 200 2326')
assert r["ip"] == "127.0.0.1" and r["method"] == "GET" and r["path"] == "/a/b.html"
assert r["status"] == 200 and r["size"] == 2326
assert r["ts"] == datetime(2023, 10, 10, 13, 55, 36, tzinfo=timezone.utc) and r["ts"].tzinfo is not None
r = parse_line('10.0.0.2 - - [01/Jan/2024:00:00:01 -0500] "POST /api HTTP/2.0" 404 -')
assert r["size"] == 0 and r["status"] == 404 and r["method"] == "POST"
assert r["ts"].utcoffset() == timedelta(hours=-5)
for bad in ["", "   ", "garbage", '1.1.1.1 - - [bad date] "GET / HTTP/1.1" 200 1',
            '1.1.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET / HTTP/1.1" abc 1',
            '1.1.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET / HTTP/1.1" 200']:
    assert parse_line(bad) is None, bad
L = '1.1.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET %s HTTP/1.1" %d %s'
lines = [L % ("/a", 200, "10"), L % ("/a?q=1", 200, "5"), L % ("/b", 404, "-"), L % ("/c", 500, "1"),
         L % ("/b", 301, "2"), L % ("/d", 200, "0"), L % ("/d", 200, "0"), "", "oops"]
s = summarize(lines)
assert s["total"] == 7 and s["malformed"] == 1, s
assert s["status_classes"] == {"2xx": 4, "4xx": 1, "5xx": 1, "3xx": 1}, s
assert s["bytes"] == 18, s
assert s["top_paths"] == [("/a", 2), ("/b", 2), ("/d", 2)], s["top_paths"]
assert summarize([]) == {"total": 0, "malformed": 0, "status_classes": {}, "bytes": 0, "top_paths": []}
assert summarize(iter(lines))["total"] == 7
print("ok")
