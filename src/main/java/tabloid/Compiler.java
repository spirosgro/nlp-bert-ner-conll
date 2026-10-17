package tabloid;

import org.antlr.v4.runtime.*;
import tabloid.parser.TabloidLexer;
import tabloid.parser.TabloidParser;

/** Parse the whole input, reject errors, then emit Python. Never execute the output. */
public final class Compiler {
    private Compiler() { }
    public static String compile(String source) {
        if (source.length() > 1_048_576) throw new CompileException("Source exceeds the 1 MiB character limit");
        BaseErrorListener errors = new BaseErrorListener() {
            @Override public void syntaxError(Recognizer<?, ?> recognizer, Object symbol, int line, int column,
                    String message, RecognitionException cause) {
                throw new CompileException(line + ":" + (column + 1) + ": " + message);
            }
        };
        TabloidLexer lexer = new TabloidLexer(CharStreams.fromString(source));
        lexer.removeErrorListeners(); lexer.addErrorListener(errors);
        TabloidParser parser = new TabloidParser(new CommonTokenStream(lexer));
        parser.removeErrorListeners(); parser.addErrorListener(errors);
        try {
            return new PythonEmitter().visitProgram(parser.program());
        } catch (StackOverflowError error) {
            throw new CompileException("Program nesting exceeds the available compiler stack");
        }
    }
}
