def evaluate(expr):
    """Evaluate an arithmetic expression string and return an int or float.

    Supported: non-negative number literals ("12", "3.5", ".5", "2."), the binary
    operators + - * / // % ** , unary + and -, parentheses, and arbitrary whitespace.
    Semantics match Python exactly, including precedence and associativity:
      - ** binds tighter than unary minus on its left: -2**2 == -4
      - ** is right-associative: 2**3**2 == 512, and its right operand may carry a
        sign: 2**-1 == 0.5
      - / is true division (always a float); // and % follow Python's floor semantics
      - integer literals produce ints, literals with a "." produce floats
      - division by zero raises ZeroDivisionError (as Python does)
    Any syntax problem (empty input, unbalanced parentheses, a dangling operator,
    two numbers in a row, an unknown character) raises ValueError.
    """
    raise NotImplementedError
