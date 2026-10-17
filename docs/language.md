# Language contract and compatibility

This document defines the public compiler's coursework dialect. Its behavior
is intentional and tested, but it does not promise compatibility with every
Tabloid interpreter.

## Lexical rules

Keywords are uppercase. Identifiers start with a lowercase ASCII letter or
underscore, followed by letters, digits or underscores. Source identifiers are
mapped injectively to `_t_` plus the original spelling in Python; even a source
identifier already beginning `_t_` receives the prefix again.

Spaces, tabs and newlines separate tokens and can occur between words of a
multiword keyword. Newlines are not statement terminators. A comment begins
with `UNCONFIRMED RUMOR:` and runs through the physical line. UTF-8 input can
have a leading BOM. CLI input is limited to 1 MiB of bytes.

Numbers use digits with an optional decimal fraction: `12`, `3.14`, `00012`.
Leading zeros are normalized for valid Python output. `.5`, `1.`, scientific
notation and symbolic `-` are not supported; use `0.5`, `1.0` and `MINUS 1`.
Number tokens are capped at 256 characters. Integers and floats follow Python
semantics, including float overflow and rounding.

Strings use single quotes and these escapes: `\'`, `\\`, `\n`, `\r`, `\t`.
Unsupported escapes and literal line breaks inside a string are rejected.
Unicode is allowed in string contents. The compiler decodes and re-quotes string
values; it does not paste their contents as Python statements.

## Precedence and associativity

From strongest to weakest:

| Level | Operators | Associativity |
|---|---|---|
| Grouping | `(expression)` | Explicit |
| Unary | `MINUS` | Right |
| Multiplicative | `TIMES`, `DIVIDED BY`, `MODULO` | Left |
| Additive | `PLUS`, `MINUS` | Left |
| Comparison | `IS ACTUALLY`, `BEATS`, `SMALLER THAN`, `IS SMALLER THAN` | One comparison per level |
| Conjunction | `AND` | Left, short-circuit |
| Disjunction | `OR` | Left, short-circuit |

Implicit chains such as `a SMALLER THAN b SMALLER THAN c` are rejected. Use
`(a SMALLER THAN b) AND (b SMALLER THAN c)` for two comparisons. Parenthesized
comparison results are ordinary Python booleans.

Function-call arguments and input prompts consume a full expression. Thus
`twice OF 2 PLUS 3` means `twice(2 + 3)`, while `(twice OF 2) PLUS 3` means
`twice(2) + 3`. Parenthesize an inner call before a comma belonging to an outer
call: `add OF (twice OF 3), 4`. A zero-argument call is `name OF ()`; a
zero-parameter declaration uses `WITH` immediately followed by its block.

## Statements and scope

Assignments, printing, functions, branches, loops, returns and expression
statements are supported. `LATEST NEWS ON` is an expression that calls Python
`input` and returns a string; no automatic numeric conversion is provided.

Functions require a block. `WHAT IF` accepts a block or one statement for each
branch. `LIES!` binds to the nearest unmatched `WHAT IF`; use blocks for clarity.
Loops require blocks. Empty blocks emit `pass`. A program must end with
`PLEASE LIKE AND SUBSCRIBE`, and any subsequent non-comment token is an error.

`SHOCKING DEVELOPMENT` is valid only inside a function. A bare return emits
Python `return`. Because newlines have no syntactic meaning, a following bare
expression can become its return value. Put a bare return immediately before
`END OF STORY` or another unambiguous statement keyword. There is no implicit
return of the last expression: falling off a function returns Python `None`.

Python name binding and function-local scope apply. A function that assigns a
name treats it as local; no Tabloid `global` or `nonlocal` syntax is provided.
Functions may be nested or recursive, but calls before a definition executes
can fail at runtime. No static undefined-name, function-arity or type analysis
is implemented. Duplicate parameters and return-outside-function are checked.

## Differences from original Tabloid

The [upstream README](https://github.com/thesephist/tabloid) describes an
expression-based interpreter with JavaScript-like behavior and implicit final
expression returns. This compiler deliberately follows its supplied coursework
structure instead.

| Topic | This repository |
|---|---|
| Backend values/operators | Python integers, floats, strings, truthiness and short-circuit operators |
| Control flow | Statement-oriented if/while; not arbitrary control-flow expressions |
| Returns | Explicit return; otherwise Python `None` |
| Chained infix syntax | Documented conventional precedence |
| While/comments/end marker | Coursework forms are supported |
| Less-than spelling | Both original `SMALLER THAN` and sample's `IS SMALLER THAN` |
| I/O | Python `print` and string-valued `input` |

For example, Python's `/`, `%`, truthiness and string/number coercion do not
provide JavaScript equivalence. Cross-interpreter equivalence is outside the
current test claims.
