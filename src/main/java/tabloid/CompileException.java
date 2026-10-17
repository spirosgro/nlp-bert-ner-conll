package tabloid;

/** A source diagnostic, with a one-based line and column. */
public final class CompileException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    public CompileException(String message) { super(message); }
}
