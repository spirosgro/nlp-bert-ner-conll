# Provenance and corrections

This repository is based on university coursework supplied by Spiros Grouztidis
in the local `omadiki_teliko` project. The reviewed material contained a Tabloid
grammar, two handwritten Java classes, ANTLR-generated sources, the ANTLR 4.13.1
complete JAR and six source/output examples. The original files were preserved
outside this public repository. The project develops existing coursework and
does not claim to invent the original Tabloid language.

## Baseline reproduced before editing

The original Java sources were compiled in a separate working directory and
run against copies of all six original `.tbd` examples. Generated Python was
syntax-checked with Python's AST parser; baseline programs were not executed.

| Original sample | ANTLR diagnostics | Exit code | Output written | Python syntax valid |
|---|---|---:|---|---|
| sample1: Fibonacci | Yes | 0 | Yes | Yes |
| sample2: factorial | No | 0 | Yes | Yes |
| sample3: arithmetic | Yes | 0 | Yes | Yes |
| sample4: logic | No | 0 | Yes | Yes |
| sample5: input | Yes | 0 | Yes | No |
| sample6: loop | Yes | 0 | Yes | Yes |

Four examples therefore reported ANTLR errors while the CLI still returned
success and wrote output. Syntactically valid output is not proof of correct
translation. In the supplied output, the loop condition had become `while i`,
and the input example emitted invalid Python. The new regression suite executes
the repaired examples as well as parsing their output.

## Main public changes

| Problem found in the source | Public change |
|---|---|
| `program` did not consume EOF | Require EOF after the end marker |
| Default error recovery could continue into emission | Throw source diagnostics from both lexer and parser |
| If branches accepted statements but not the examples' blocks | Explicit statement-or-block suites |
| Input was only a statement | Input expression usable in assignment/call/return contexts |
| String rule did not implement the sample's escapes | Defined escape grammar with decoding and Python re-quoting |
| Direct recursion alternatives implied unintended operator precedence | Explicit precedence levels and left-fold emission |
| Visitor omitted most expression grouping | Parenthesize binary expression nodes |
| Empty blocks emitted no body | Emit Python `pass` |
| Source identifiers could be Python keywords/built-in names | Prefix every source name consistently |
| Top-level return and duplicate parameters could generate invalid Python | Reject these constructs before output |
| Only `SMALLER THAN` was recognized | Also accept the original loop sample's `IS SMALLER THAN` |
| Generated sources and tool binaries were mixed with handwritten files | Regenerate from grammar; verify a pinned external dependency |
| CLI silently selected a default file and overwrote output | Explicit input, stdout/default, check-only mode and opt-in overwrite |

The public emitter, build tooling, tests and English documentation were prepared
with AI assistance. Newly added checks and features are public-refactor work,
not historical submission results. The repository's source examples retain
their original purpose; wording-only edits are listed in the examples guide.

## Source fingerprints

These hashes identify the reviewed original files, not the modified public ones.

| Original file | SHA-256 |
|---|---|
| Tabloid.g4 | `cb712871c21d0b8ed641cfb02bcb8ee3f6afbdf1678d6a493a1e56413e42a81d` |
| Tabloid2Python.java | `7b15c3463406d41ddde30e4fdfcf24aa77635760892441c67ff40b8ef27b1872` |
| TabloidToPythonTranslator.java | `db6dcfb4cba3b134c994ac8116e4c8e8740df4475622062ea243f666f74c9925` |

Original assignment documents, archives, personal filesystem paths and generated
IDE artifacts are not included. See [third-party notices](../THIRD_PARTY_NOTICES.md)
for language/tool attribution and [language compatibility](language.md) for
semantic differences from the upstream interpreter.
