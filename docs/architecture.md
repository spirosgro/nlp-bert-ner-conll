# Architecture and design choices

## Build

`tools/build.py` downloads one pinned ANTLR 4.13.1 complete JAR, checks its SHA-256
and generates the lexer/parser/visitor base from `grammar/Tabloid.g4`. Generation
happens in a unique temporary build directory. Stale generated Java is not
checked into Git or reused on the next build.

Generated ANTLR sources compile with lint disabled because the generator's
templates can trigger warnings introduced by newer JDKs. Handwritten Java
compiles separately with `--release 17 -Xlint:all -Werror`. Both use the same
ANTLR runtime. Python's standard ZIP support packages a thin executable JAR,
so a separate `jar` launcher is not required on PATH.

The build replaces the previous compiler JAR only after successful generation,
compilation and packaging. A failed build therefore leaves the previous JAR in
place; do not mistake that old artifact for a newly built compiler.

## Front end

`Compiler.compile` attaches a throwing error listener to both lexer and parser.
There is no parse-error recovery followed by emission. The program rule consumes
EOF, so trailing statements after the end marker cannot be silently ignored.
Nesting that exhausts the Java stack becomes a compilation diagnostic; this is
an implementation limit rather than a formal complexity guarantee.

Expression levels are separate grammar rules. This avoids the accidental
precedence introduced by ordering direct-left-recursive alternatives incorrectly.
The visitor emits parentheses around each binary node, preserving grouping and
left associativity when Python later parses the output.

## Emission and checks

`PythonEmitter` tracks indentation and function depth. Empty suites receive
`pass`. It rejects returns outside functions, duplicate parameters and oversized
number literals. All user names are prefixed; built-in print/input cannot be
shadowed by an identically spelled source variable. Strings are decoded and
quoted as values rather than inserted as raw executable fragments.

This is a direct parse-tree visitor, not a separate typed intermediate
representation. It deliberately has no optimizer or full symbol-table pass.
Runtime semantic errors remain Python errors, as documented in the language
contract. Generated line numbers do not map back to original source lines.

## CLI output lifecycle

The CLI validates arguments and UTF-8, then compiles entirely before writing an
output file. Ordinary `-o` uses CREATE_NEW to avoid replacement. Explicit
`--force` writes a sibling temporary file and requests atomic replacement;
unsupported filesystems can reject that operation. Output symlinks are rejected.
Parent directories must exist. Stdout emits UTF-8 Python without status chatter;
status messages and diagnostics use stderr.

`--check` performs the compiler's parse/semantic checks only. It does not invoke
Python, prove that runtime names exist or guarantee successful execution.

## Why the tests execute Python

A syntactically valid Python file can still have incorrect branch grouping,
operator binding or loop conditions. The suite therefore compiles test inputs,
parses emitted Python with `ast.parse`, and executes authored cases in separate
Python processes with a timeout and expected stdout. Six checked-in reference
outputs also detect accidental emitter changes. Negative cases verify that
errors do not produce or overwrite output files.

These subprocesses are for trusted test fixtures. Isolated Python mode and a
timeout are not an operating-system sandbox for arbitrary user programs.
