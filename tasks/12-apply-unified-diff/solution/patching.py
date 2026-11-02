import re


class PatchError(Exception):
    """Raised when a patch is malformed or does not apply."""


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _split(text):
    return re.findall(r"[^\n]*\n|[^\n]+", text)


def apply_patch(original, patch):
    """Apply a single-file unified diff; see task statement."""
    old = _split(original)
    plines = patch.split("\n")
    if plines and plines[-1] == "":
        plines.pop()
    i = 0
    while i < len(plines) and not plines[i].startswith("@@"):
        i += 1
    out = []
    pos = 0
    while i < len(plines):
        m = _HUNK.match(plines[i])
        if not m:
            raise PatchError("bad hunk header: %r" % plines[i])
        i += 1
        a = int(m.group(1))
        old_n = 1 if m.group(2) is None else int(m.group(2))
        new_n = 1 if m.group(4) is None else int(m.group(4))
        start = a if old_n == 0 else a - 1
        if start < pos or start > len(old):
            raise PatchError("hunk out of order or out of range")
        out.extend(old[pos:start])
        pos = start
        seen_old = seen_new = 0
        while seen_old < old_n or seen_new < new_n:
            if i >= len(plines):
                raise PatchError("truncated hunk")
            line = plines[i]
            i += 1
            kind, text = (line[:1] or " "), line[1:]
            if kind == "\\":
                raise PatchError("unexpected no-newline marker")
            if kind not in " -+":
                raise PatchError("bad hunk line: %r" % line)
            has_nl = True
            if i < len(plines) and plines[i].startswith("\\"):
                has_nl = False
                i += 1
            if kind in " -":
                if pos >= len(old):
                    raise PatchError("hunk runs past end of file")
                want = text + ("\n" if has_nl else "")
                if old[pos] != want:
                    raise PatchError("context mismatch at line %d" % (pos + 1))
                if kind == " ":
                    out.append(old[pos])
                pos += 1
                seen_old += 1
            if kind in " +":
                if kind == "+":
                    out.append(text + ("\n" if has_nl else ""))
                seen_new += 1
        # a trailing marker after the last body line is consumed above
    out.extend(old[pos:])
    return "".join(out)
