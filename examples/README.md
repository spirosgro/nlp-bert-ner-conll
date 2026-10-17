# Example programs

The six examples derive from the supplied coursework. They are renamed by
purpose, with only the wording edits described below. The public grammar fixes
the unsupported constructs instead of deleting them from these examples.

| Source | Generated Python | What it demonstrates |
|---|---|---|
| [fibonacci.tbd](fibonacci.tbd) | [fibonacci.py](expected/fibonacci.py) | Recursive function, branch blocks, ten printed Fibonacci values |
| [factorial.tbd](factorial.tbd) | [factorial.py](expected/factorial.py) | Recursive multiplication and explicit return; factorial of 10 |
| [arithmetic.tbd](arithmetic.tbd) | [arithmetic.py](expected/arithmetic.py) | Branch blocks and mixed arithmetic precedence |
| [logic.tbd](logic.tbd) | [logic.py](expected/logic.py) | Equality, booleans and OR |
| [input.tbd](input.tbd) | [input.py](expected/input.py) | Escaped apostrophe and input used as an expression |
| [while_loop.tbd](while_loop.tbd) | [while_loop.py](expected/while_loop.py) | Loop, assignment and `IS SMALLER THAN` alias |

The arithmetic example's comment now describes this dialect's precedence. The
input prompt's original `What\' s` spacing was corrected to `What\'s`, with a
trailing prompt space. These are documented source edits, not a claim that the
original examples all worked unmodified with the original compiler.

`examples/expected/*.py` files are deliberately checked-in reference output for
review. The tests compare current generated code with them and execute the new
output against independently specified stdout. In contrast, ANTLR-generated
Java/token files are temporary build artifacts and stay out of Git.

To regenerate a single file for inspection without replacing its reference:

```text
python tools/tabloid.py examples/fibonacci.tbd -o build/fibonacci.py
python build/fibonacci.py
```

Expected Fibonacci values: `1, 1, 2, 3, 5, 8, 13, 21, 34, 55`, each on its own
line after the heading. The factorial example prints `3628800`; arithmetic
prints `12.3` and `11.0`; the loop prints integers 0 through 9.
