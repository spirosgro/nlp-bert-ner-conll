"""Compile real sources, parse emitted Python and execute only authored test programs."""
from pathlib import Path
import ast
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "build/tabloid-compiler.jar"
END = "\nPLEASE LIKE AND SUBSCRIBE\n"


class CompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not JAR.is_file():
            raise RuntimeError("Build first: python tools/build.py")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tabloid-test-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "program.tbd"

    def cli(self, *args):
        return subprocess.run(["java", "-jar", str(JAR), *map(str, args)], capture_output=True,
                              encoding="utf-8", timeout=15)

    def translate(self, source):
        self.source.write_text(source, encoding="utf-8")
        result = self.cli(self.source)
        self.assertEqual(result.returncode, 0, result.stderr)
        ast.parse(result.stdout)
        return result.stdout

    def run_python(self, code, stdin=""):
        script = self.folder / "run.py"
        script.write_text(code, encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, "-I", "-X", "utf8", str(script)], input=stdin,
                              capture_output=True, encoding="utf-8", timeout=5, env=env)

    def executes(self, source, expected, stdin=""):
        result = self.run_python(self.translate(source + END), stdin)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, expected)

    def invalid(self, source, diagnostic=None):
        self.source.write_text(source, encoding="utf-8")
        result = self.cli(self.source)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        if diagnostic:
            self.assertIn(diagnostic, result.stderr)

    def example(self, name, output, stdin=""):
        source = (ROOT / "examples" / f"{name}.tbd").read_text(encoding="utf-8")
        generated = self.translate(source)
        self.assertEqual(generated, (ROOT / "examples/expected" / f"{name}.py").read_text(encoding="utf-8"))
        result = self.run_python(generated, stdin)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, output)

    def test_example_fibonacci(self):
        self.example("fibonacci", "First 10 Fibonacci numbers\n1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n")

    def test_example_factorial(self):
        self.example("factorial", "Hello, World!\nResult is\n3628800\n")

    def test_example_arithmetic(self):
        self.example("arithmetic", "12.3\n11.0\n")

    def test_example_logic(self):
        self.example("logic", "3.1415\nTrue\n")

    def test_example_input(self):
        self.example("input", "Asking for some info here\nWhat's your name? Hello \nAda\n", "Ada\n")

    def test_example_while(self):
        self.example("while_loop", "".join(f"{i}\n" for i in range(10)))

    def test_precedence_and_left_associativity(self):
        self.executes("YOU WON'T WANT TO MISS 20 MINUS 5 MINUS 3\nYOU WON'T WANT TO MISS 20 DIVIDED BY 2 TIMES 5\nYOU WON'T WANT TO MISS 2 PLUS 3 TIMES 4", "12\n50.0\n14\n")

    def test_boolean_precedence_and_short_circuit(self):
        self.executes("YOU WON'T WANT TO MISS TOTALLY RIGHT OR COMPLETELY WRONG AND COMPLETELY WRONG\nYOU WON'T WANT TO MISS COMPLETELY WRONG AND (1 DIVIDED BY 0)", "True\nFalse\n")

    def test_parentheses_unary_and_modulo(self):
        self.executes("YOU WON'T WANT TO MISS (2 PLUS 3) TIMES 4\nYOU WON'T WANT TO MISS MINUS 7 MODULO 3", "20\n2\n")

    def test_empty_program_and_blocks(self):
        self.executes("DISCOVER HOW TO empty WITH RUMOR HAS IT END OF STORY\nWHAT IF TOTALLY RIGHT RUMOR HAS IT END OF STORY\nSTAY TUNED WHILE COMPLETELY WRONG RUMOR HAS IT END OF STORY\nYOU WON'T WANT TO MISS empty OF ()", "None\n")
        self.executes("", "")

    def test_input_expression_and_utf8(self):
        self.executes("EXPERTS CLAIM name TO BE LATEST NEWS ON 'Name: '\nYOU WON'T WANT TO MISS 'Hello, ' PLUS name", "Name: Hello, Zoë\n", "Zoë\n")

    def test_keywords_and_builtins_are_mangled(self):
        self.executes("EXPERTS CLAIM class TO BE 2\nEXPERTS CLAIM print TO BE 3\nEXPERTS CLAIM _t_class TO BE 4\nYOU WON'T WANT TO MISS class PLUS print PLUS _t_class", "9\n")

    def test_nested_calls_with_parenthesized_argument(self):
        self.executes("DISCOVER HOW TO twice WITH x RUMOR HAS IT SHOCKING DEVELOPMENT x TIMES 2 END OF STORY\nDISCOVER HOW TO add WITH x, y RUMOR HAS IT SHOCKING DEVELOPMENT x PLUS y END OF STORY\nYOU WON'T WANT TO MISS add OF (twice OF 3), 4", "10\n")

    def test_nearest_else_and_block_else(self):
        self.executes("WHAT IF TOTALLY RIGHT WHAT IF COMPLETELY WRONG YOU WON'T WANT TO MISS 'bad' LIES! YOU WON'T WANT TO MISS 'inner'\nWHAT IF COMPLETELY WRONG RUMOR HAS IT END OF STORY LIES! RUMOR HAS IT YOU WON'T WANT TO MISS 'block' END OF STORY", "inner\nblock\n")

    def test_strings_escapes_are_data(self):
        self.executes(r"YOU WON'T WANT TO MISS 'a\tb\ncan\'t\\path'", "a\tb\ncan't\\path\n")
        self.executes("YOU WON'T WANT TO MISS '__import__(\'os\')'".replace("'os'", r"\'os\'"), "__import__('os')\n")

    def test_leading_zero_numbers(self):
        self.executes("YOU WON'T WANT TO MISS 00012\nYOU WON'T WANT TO MISS 0001.50", "12\n1.5\n")

    def test_whitespace_comments_and_bom(self):
        self.executes("\ufeffUNCONFIRMED RUMOR: example\nYOU\tWON'T\nWANT TO   MISS 7", "7\n")

    def test_less_than_aliases(self):
        self.executes("YOU WON'T WANT TO MISS 1 SMALLER THAN 2\nYOU WON'T WANT TO MISS 1 IS SMALLER THAN 2", "True\nTrue\n")

    def test_missing_terminator(self):
        self.invalid("YOU WON'T WANT TO MISS 1")

    def test_trailing_input_rejected(self):
        self.invalid("YOU WON'T WANT TO MISS 1" + END + "YOU WON'T WANT TO MISS 2")

    def test_lexer_error_with_location(self):
        self.invalid("YOU WON'T WANT TO MISS @" + END)
        self.assertRegex(self.cli(self.source).stderr, r"program\.tbd:1:\d+:")

    def test_bad_escape(self):
        self.invalid(r"YOU WON'T WANT TO MISS 'bad\q'" + END)

    def test_return_outside_function(self):
        self.invalid("SHOCKING DEVELOPMENT 1" + END, "Return is only valid")

    def test_duplicate_parameters(self):
        self.invalid("DISCOVER HOW TO f WITH x, x RUMOR HAS IT END OF STORY" + END, "Duplicate parameter")

    def test_large_number_rejected(self):
        self.invalid("YOU WON'T WANT TO MISS " + "9" * 257 + END, "256 characters")

    def test_comparison_chains_rejected(self):
        self.invalid("YOU WON'T WANT TO MISS 1 SMALLER THAN 2 SMALLER THAN 3" + END)

    def test_output_not_written_on_invalid_input(self):
        self.source.write_text("WHAT IF" + END)
        output = self.folder / "out.py"
        self.assertEqual(self.cli(self.source, "-o", output).returncode, 1)
        self.assertFalse(output.exists())
        output.write_text("preserve me")
        self.assertEqual(self.cli(self.source, "-o", output, "--force").returncode, 1)
        self.assertEqual(output.read_text(), "preserve me")

    def test_overwrite_requires_explicit_force(self):
        self.source.write_text("YOU WON'T WANT TO MISS 1" + END)
        output = self.folder / "out.py"
        output.write_text("preserve me")
        self.assertEqual(self.cli(self.source, "-o", output).returncode, 2)
        self.assertEqual(output.read_text(), "preserve me")
        self.assertEqual(self.cli(self.source, "-o", output, "--force").returncode, 0)
        ast.parse(output.read_text())

    def test_check_only(self):
        self.source.write_text("YOU WON'T WANT TO MISS 1" + END)
        result = self.cli(self.source, "--check")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("Validated", result.stderr)

    def test_cli_misuse_and_missing_file(self):
        self.assertEqual(self.cli().returncode, 2)
        self.assertEqual(self.cli("absent.tbd").returncode, 2)
        self.assertEqual(self.cli("program.txt").returncode, 2)
        self.assertEqual(self.cli("--help").returncode, 0)
        self.assertEqual(self.cli(self.source, "--check", "--force").returncode, 2)

    def test_source_size_limit(self):
        self.invalid(" " * 1_048_577, "1 MiB")

    def test_undefined_name_is_a_runtime_error(self):
        result = self.run_python(self.translate("YOU WON'T WANT TO MISS missing" + END))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NameError", result.stderr)


if __name__ == "__main__":
    unittest.main()
