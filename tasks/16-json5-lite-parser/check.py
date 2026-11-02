import math, os, sys
sys.path.insert(0, os.getcwd())
from json5lite import loads, ParseError

def err(text):
    try:
        loads(text)
    except ParseError as e:
        assert isinstance(e, ValueError)
        return (e.line, e.col)
    raise SystemExit("expected ParseError for %r" % (text,))

# plain JSON
assert loads('{"a": [1, 2.5, -3e2, true, false, null, "x"]}') == {"a": [1, 2.5, -300.0, True, False, None, "x"]}
assert loads("  [ ]  ") == [] and loads("{}") == {}
assert loads("0") == 0 and loads("-0") == 0 and loads("1e3") == 1000.0 and type(loads("1e3")) is float
assert type(loads("12")) is int and type(loads("1.0")) is float
# comments
assert loads("// c\n[1, /* x */ 2 // y\n]") == [1, 2]
assert loads("/* a\n b */ 5 /* c */") == 5
assert loads("[1 /**/, 2]") == [1, 2]
# trailing commas
assert loads("[1,2,]") == [1, 2] and loads('{"a":1,}') == {"a": 1}
assert loads("[[],]") == [[]]
assert err("[,]") == (1, 2)
assert err("[1,,2]") == (1, 4)
assert err('{,}') == (1, 2)
# strings
assert loads("'it\\'s'") == "it's" and loads('"a\\"b"') == 'a"b'
assert loads('"\\x41\\u0042\\n\\t\\0\\v"') == "AB\n\t\0\v"
assert loads('"\\ud83d\\ude00"') == "\U0001F600"
assert loads('"a\\\nb"') == "ab"
assert loads('"\\/"') == "/"
assert loads("'\"'") == '"'
assert err('"\\q"') == (1, 3)
assert err('"abc') == (1, 1)
assert err('["abc') == (1, 2)
assert err('"a\nb"') == (1, 3)
# keys
assert loads("{a: 1, $b_2: 2, 'c d': 3, \"e\": 4}") == {"a": 1, "$b_2": 2, "c d": 3, "e": 4}
assert loads("{a:1,a:2}") == {"a": 2}
assert err("{1: 2}") == (1, 2)
assert err("{a 1}") == (1, 4)
# numbers
assert loads("0x1F") == 31 and loads("-0xff") == -255 and loads("+5") == 5
assert loads(".5") == 0.5 and loads("5.") == 5.0 and loads("-.5") == -0.5 and loads("+1.5e-1") == 0.15
assert loads("Infinity") == math.inf and loads("-Infinity") == -math.inf and loads("+Infinity") == math.inf
assert math.isnan(loads("NaN")) and math.isnan(loads("[NaN]")[0])
assert err("012") == (1, 1)
assert err("[1, 0x]") == (1, 7) and err("0x") == (1, 3)
assert err("1e") == (1, 3) and err("1e+") == (1, 4)
assert err("-") == (1, 2) and err("[-]") == (1, 3)
# literals
assert loads("[true,false,null]") == [True, False, None]
# structure errors
assert err("") == (1, 1)
assert err("   ") == (1, 4)
assert err("// only a comment") == (1, 18)
assert err("[1, 2") == (1, 6)
assert err('{"a": 1') == (1, 8)
assert err('{"a" 1}') == (1, 6)
assert err("[1 2]") == (1, 4)
assert err("1 2") == (1, 3)
assert err("[1] x") == (1, 5)
assert err("/* open") == (1, 1)
assert err("[1, /* open") == (1, 5)
assert err("{\n  a: 1,\n  b: @\n}") == (3, 6)
assert err("[\r\n1,\r\n?]") == (3, 1)
assert err("é @") == (1, 1)
assert err("[\"é\", @]") == (1, 7)
# deep nesting
assert loads("[" * 200 + "]" * 200) is not None
print("ok")
