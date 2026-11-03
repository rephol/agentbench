"""A lenient JSON reader ("JSON5-lite").

loads(text) -> Python value. Accepts standard JSON plus:

* `//` line comments and `/* */` block comments wherever whitespace is allowed.
* Trailing commas in arrays and objects (`[1, 2,]`, `{"a": 1,}`). A lone comma
  (`[,]`) or a doubled comma (`[1,,2]`) is an error.
* Strings in single or double quotes. Escapes: \\n \\r \\t \\b \\f \\v \\0 \\' \\" \\\\ \\/,
  \\xHH, \\uHHHH (a surrogate pair \\ud83d\\ude00 must combine into one character),
  and a backslash followed by a newline (line continuation: contributes nothing).
  Any other escape, and a raw newline inside a string, is an error.
* Unquoted object keys matching [A-Za-z_$][A-Za-z0-9_$]*.
* Numbers: integers, decimals, exponents, a leading `+` or `-`, a leading or
  trailing dot (`.5`, `5.`), hex integers (`0x1F`, `-0xff`), and the words
  `Infinity`, `-Infinity`, `+Infinity`, `NaN`. Integers without dot/exponent
  (including hex) are `int`; everything else is `float`. Leading zeros such as
  `012` are an error.
* `true`, `false`, `null`. Duplicate object keys: the last one wins.
* Whitespace is space, tab, CR, LF.

Errors raise ParseError (a ValueError) with 1-based `line` and `col`:

* an unexpected character: the position of that character;
* trailing non-comment text after the value: the position of its first character;
* an unterminated string: the position of its opening quote;
* an unterminated block comment: the position of its opening `/*`;
* unexpected end of input: the position just past the last character
  (an empty or comment-only document is also this error);
* a raw newline inside a string: the position of that newline;
* an unknown escape such as `\\q`: the position of the character right after the
  backslash; a malformed `\\x`/`\\u` (too few or non-hex digits): the position of
  the character right after the `x`/`u`;
* a number with a leading zero (`012`, `-012`): the position of the leading `0`
  (after any sign);
* a number missing required digits (nothing after `0x`, `e`, `e+`, `-`, or a lone
  `.`): the position of the first character where a digit was needed, which is
  the position just past the end of input if the text ends there.
Columns count characters, not bytes. A CRLF counts as one line break.
"""


class ParseError(ValueError):
    def __init__(self, msg, line, col):
        super().__init__(f"{msg} at line {line}, column {col}")
        self.msg, self.line, self.col = msg, line, col


_IDSTART = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$")
_IDREST = _IDSTART | set("0123456789")
_ESC = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0",
        "'": "'", '"': '"', "\\": "\\", "/": "/"}


class _P:
    def __init__(self, s):
        self.s = s.replace("\r\n", "\n")
        self.i = 0

    def pos(self, i=None):
        i = self.i if i is None else i
        before = self.s[:i]
        return before.count("\n") + 1, i - (before.rfind("\n") + 1) + 1

    def err(self, msg, i=None):
        line, col = self.pos(i)
        raise ParseError(msg, line, col)

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def ws(self):
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\r\n":
                self.i += 1
            elif s.startswith("//", self.i):
                j = s.find("\n", self.i)
                self.i = len(s) if j < 0 else j
            elif s.startswith("/*", self.i):
                j = s.find("*/", self.i + 2)
                if j < 0:
                    self.err("unterminated comment")
                self.i = j + 2
            else:
                break

    def value(self):
        self.ws()
        c = self.peek()
        if c == "":
            self.err("unexpected end of input")
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c in "'\"":
            return self.string()
        for word, val in (("true", True), ("false", False), ("null", None)):
            if self.s.startswith(word, self.i) and self.s[self.i + len(word):self.i + len(word) + 1] not in _IDREST - {""}:
                self.i += len(word)
                return val
        return self.number()

    def number(self):
        s, i0 = self.s, self.i
        j = i0
        sign = 1
        if j < len(s) and s[j] in "+-":
            sign = -1 if s[j] == "-" else 1
            j += 1
        for word, val in (("Infinity", float("inf")), ("NaN", float("nan"))):
            if s.startswith(word, j):
                self.i = j + len(word)
                return sign * val if word == "Infinity" else val
        if s.startswith(("0x", "0X"), j):
            k = j + 2
            while k < len(s) and s[k] in "0123456789abcdefABCDEF":
                k += 1
            if k == j + 2:
                self.err("bad hex number", k)
            self.i = k
            return sign * int(s[j + 2:k], 16)
        k = j
        digits = ""
        while k < len(s) and s[k].isdigit() and s[k].isascii():
            k += 1
        intpart = s[j:k]
        isfloat = False
        frac = ""
        if k < len(s) and s[k] == ".":
            isfloat = True
            k += 1
            m = k
            while k < len(s) and s[k].isdigit() and s[k].isascii():
                k += 1
            frac = s[m:k]
        if not intpart and not frac:
            self.err("unexpected character" if k < len(s) else "unexpected end of input", k)
        if len(intpart) > 1 and intpart[0] == "0":
            self.err("leading zero", j)
        if k < len(s) and s[k] in "eE":
            e = k + 1
            if e < len(s) and s[e] in "+-":
                e += 1
            m = e
            while e < len(s) and s[e].isdigit() and s[e].isascii():
                e += 1
            if e == m:
                self.err("bad exponent", e)
            isfloat = True
            k = e
        self.i = k
        txt = s[j:k]
        return sign * float(txt) if isfloat else sign * int(txt)

    def string(self):
        q = self.s[self.i]
        start = self.i
        self.i += 1
        out = []
        s = self.s
        while True:
            if self.i >= len(s):
                self.err("unterminated string", start)
            c = s[self.i]
            if c == q:
                self.i += 1
                return "".join(out)
            if c == "\n":
                self.err("newline in string")
            if c == "\\":
                self.i += 1
                if self.i >= len(s):
                    self.err("unterminated string", start)
                e = s[self.i]
                if e == "\n":
                    self.i += 1
                elif e in _ESC:
                    out.append(_ESC[e])
                    self.i += 1
                elif e == "x":
                    out.append(self.hex(2))
                elif e == "u":
                    ch = self.hex(4)
                    if "\ud800" <= ch <= "\udbff" and s.startswith("\\u", self.i):
                        save = self.i
                        self.i += 1
                        lo = self.hex(4)
                        if "\udc00" <= lo <= "\udfff":
                            ch = chr(0x10000 + ((ord(ch) - 0xD800) << 10) + (ord(lo) - 0xDC00))
                        else:
                            self.i = save
                    out.append(ch)
                else:
                    self.err("bad escape")
            else:
                out.append(c)
                self.i += 1

    def hex(self, n):
        s = self.s
        self.i += 1
        h = s[self.i:self.i + n]
        if len(h) != n or any(x not in "0123456789abcdefABCDEF" for x in h):
            self.err("bad hex escape")
        self.i += n
        return chr(int(h, 16))

    def key(self):
        c = self.peek()
        if c in "'\"":
            return self.string()
        if c in _IDSTART and c != "":
            j = self.i
            while j < len(self.s) and self.s[j] in _IDREST:
                j += 1
            k = self.s[self.i:j]
            self.i = j
            return k
        self.err("unexpected end of input" if c == "" else "unexpected character")

    def obj(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.peek() == "}":
                self.i += 1
                return out
            k = self.key()
            self.ws()
            if self.peek() != ":":
                self.err("expected ':'" if self.peek() else "unexpected end of input")
            self.i += 1
            out[k] = self.value()
            self.ws()
            c = self.peek()
            if c == ",":
                self.i += 1
            elif c == "}":
                self.i += 1
                return out
            else:
                self.err("expected ',' or '}'" if c else "unexpected end of input")

    def arr(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.peek() == "]":
                self.i += 1
                return out
            out.append(self.value())
            self.ws()
            c = self.peek()
            if c == ",":
                self.i += 1
            elif c == "]":
                self.i += 1
                return out
            else:
                self.err("expected ',' or ']'" if c else "unexpected end of input")


def loads(text):
    p = _P(text)
    v = p.value()
    p.ws()
    if p.i < len(p.s):
        p.err("trailing characters")
    return v
