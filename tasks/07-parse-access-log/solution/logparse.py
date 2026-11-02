"""Parse web server access logs in Common Log Format."""
import re
from collections import Counter
from datetime import datetime

_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<ts>[^\]]+)\] "(?P<method>[A-Z]+) (?P<target>\S+) [^"]*" '
    r'(?P<status>\d{3}) (?P<size>\d+|-)\s*$'
)


def parse_line(line):
    m = _RE.match(line.strip()) if line and line.strip() else None
    if not m:
        return None
    try:
        ts = datetime.strptime(m["ts"], "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        return None
    size = 0 if m["size"] == "-" else int(m["size"])
    return {"ip": m["ip"], "ts": ts, "method": m["method"], "path": m["target"].split("?", 1)[0],
            "status": int(m["status"]), "size": size}


def summarize(lines):
    total = malformed = size = 0
    classes = Counter()
    paths = Counter()
    for line in lines:
        if not line.strip():
            continue
        r = parse_line(line)
        if r is None:
            malformed += 1
            continue
        total += 1
        size += r["size"]
        classes[f"{r['status'] // 100}xx"] += 1
        paths[r["path"]] += 1
    top = sorted(paths.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    return {"total": total, "malformed": malformed, "status_classes": dict(classes), "bytes": size, "top_paths": top}
