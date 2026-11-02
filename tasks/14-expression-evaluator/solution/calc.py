import re

_TOKEN = re.compile(r"\s*(?:(\d+\.\d*|\.\d+|\d+)|(\*\*|//|[-+*/%()]))")


def _tokenize(s):
    toks, pos = [], 0
    s = s.rstrip()
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise ValueError("bad character at %d" % pos)
        if m.group(1) is not None:
            t = m.group(1)
            toks.append(("num", float(t) if "." in t else int(t)))
        else:
            toks.append(("op", m.group(2)))
        pos = m.end()
    return toks


class _Parser:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def eat_op(self, *ops):
        kind, val = self.peek()
        if kind == "op" and val in ops:
            self.i += 1
            return val
        return None

    def expr(self):
        v = self.term()
        while (op := self.eat_op("+", "-")):
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.unary()
        while (op := self.eat_op("*", "/", "//", "%")):
            r = self.unary()
            if op == "*":
                v = v * r
            elif op == "/":
                v = v / r
            elif op == "//":
                v = v // r
            else:
                v = v % r
        return v

    def unary(self):
        op = self.eat_op("+", "-")
        if op:
            v = self.unary()
            return -v if op == "-" else +v
        return self.power()

    def power(self):
        base = self.atom()
        if self.eat_op("**"):
            return base ** self.unary()
        return base

    def atom(self):
        kind, val = self.peek()
        if kind == "num":
            self.i += 1
            return val
        if self.eat_op("("):
            v = self.expr()
            if not self.eat_op(")"):
                raise ValueError("missing )")
            return v
        raise ValueError("unexpected %r" % (val,))


def evaluate(expr):
    toks = _tokenize(expr)
    if not toks:
        raise ValueError("empty expression")
    p = _Parser(toks)
    v = p.expr()
    if p.i != len(toks):
        raise ValueError("trailing input")
    return v
