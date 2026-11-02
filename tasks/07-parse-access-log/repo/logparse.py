"""Parse web server access logs in Common Log Format."""
from datetime import datetime  # noqa: F401  (you will need it)

# Example line:
# 127.0.0.1 - frank [10/Oct/2023:13:55:36 +0000] "GET /a/b.html?x=1 HTTP/1.1" 200 2326
# A "-" in the size field means 0 bytes.


def parse_line(line):
    """Parse one log line.

    Returns a dict with keys: ip (str), ts (timezone-aware datetime), method (str),
    path (str, query string removed), status (int), size (int; "-" -> 0).
    Returns None if the line is blank or malformed in any way.
    """
    raise NotImplementedError


def summarize(lines):
    """Summarize an iterable of log lines.

    Returns a dict:
      total: number of well-formed lines
      malformed: number of non-blank lines that failed to parse (blank lines are ignored)
      status_classes: {"2xx": n, ...} counting only classes that occur
      bytes: sum of sizes
      top_paths: up to 3 (path, count) tuples, highest count first, ties broken by path ascending
    """
    raise NotImplementedError
