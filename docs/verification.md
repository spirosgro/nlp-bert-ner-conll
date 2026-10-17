# Verification record

Verified locally on **16 October 2026**, Windows 11, Python **3.12.14**.

| Toolchain | Result |
|---|---|
| Oracle JDK 23.0.1, Java 17 bytecode target | Build succeeded; 32 tests passed |
| Zulu OpenJDK 17.0.9, Java 17 bytecode target | Build succeeded; 32 tests passed, including checked-in output comparisons |
| ANTLR 4.13.1 tool/runtime | Official download verified against pinned SHA-256 |

These are observed local versions, not recommendations to install old patch
releases. Use a maintained JDK installation. The same ANTLR version generates
and runs the parser. Handwritten code passed strict lint; generated code uses
the separate lint policy explained in the architecture document.

## What the tests exercise

- All six source-derived programs: Fibonacci, factorial, arithmetic, logic,
  interactive input and a while loop. Each is translated, parsed by Python and
  executed against expected stdout; reference `.py` files also match output.
- Arithmetic associativity, explicit grouping, unary minus, modulo, boolean
  precedence and short-circuit behavior.
- Empty programs/blocks, zero-argument functions, recursion, nested calls,
  nearest-else binding and both less-than spellings.
- String escapes, Unicode input, identifiers colliding with Python names,
  leading-zero numbers, whitespace, comments and BOM handling.
- Missing terminator, trailing input, lexer errors with locations, invalid
  escapes, illegal returns, duplicate parameters and oversized numbers/input.
- Output preservation on invalid input, explicit overwrite, check-only mode,
  CLI misuse and runtime handling of undefined names.

Tests use only standard-library Python plus the compiled Java application.
Each case has its own temporary directory. Compiler subprocesses have a
15-second timeout; authored Python examples have a 5-second timeout. No
untrusted downloaded program is automatically executed.

## Baseline and CI

The original six examples were independently processed with the original Java
code before changes. Four emitted ANTLR diagnostics despite exit code 0; one
generated Python that failed syntax parsing. The complete table is in
[provenance](provenance.md).

GitHub Actions is configured for Windows/Linux and JDK 17/21 with Python 3.12.
Hosted runs have not been observed before publication. Neither that configuration
nor Java 17 bytecode alone establishes Linux or JDK 21 runtime success.

`python tools/check_release.py` validates public files, Python syntax, local
Markdown links, required content and selected publication hygiene rules. It
does not replace compilation or provide a comprehensive security audit.

## Not established

There is no full upstream Tabloid conformance suite, randomized differential
testing, fuzzing campaign, performance benchmark, Python 3.10 runtime run,
static type analysis or sandbox assurance. Test success supports the documented
examples and checks; it is not a proof of semantic correctness for all programs.
