# Execution and trust boundaries

The compiler reads local source and emits Python; it never automatically runs
the generated program. Tests explicitly execute only the repository's authored
fixtures. Inspect unfamiliar source/output before running it.

Generated programs can loop indefinitely, recurse, consume memory, print large
amounts of output or wait for input. Python isolated mode and subprocess timeouts
used in tests are not a general sandbox. Do not expose compilation/execution as
an untrusted public service without separate process isolation and resource limits.

The CLI caps input at 1 MiB and number tokens at 256 characters, fails on lexer
or parser errors, prefixes source identifiers and re-quotes string data. These
are targeted correctness/defensive controls, not a proof of safety for adversarial
sources. Extremely complex expressions can still consume CPU/memory. The Java
stack fallback is not a formal nesting or time bound.

Output files are preserved unless `--force` is explicit. Compile errors occur
before writing. Forced replacement uses a temporary sibling file and atomic
move, which may be unsupported on some filesystems. There is no power-loss
durability guarantee or protection against another local process manipulating
the output directory concurrently.

The build downloads ANTLR only from the specified HTTPS URL and verifies the
pinned SHA-256. Cached mismatches fail closed. Update the version/hash deliberately;
do not bypass integrity checking to accept a different binary. Generated code,
dependencies and build outputs are not committed.

Use public GitHub issues for non-sensitive compiler defects. Do not include
credentials, personal data or private source programs in a report. This
repository does not promise a private vulnerability-reporting service.
