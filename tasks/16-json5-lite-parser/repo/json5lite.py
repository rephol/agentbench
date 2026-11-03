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


def loads(text):
    raise NotImplementedError
