package tabloid;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

public final class Main {
    private Main() { }
    public static void main(String[] args) { System.exit(run(args)); }
    private static int run(String[] args) {
        Path input = null, output = null;
        boolean force = false, check = false;
        try {
            for (int i = 0; i < args.length; i++) {
                switch (args[i]) {
                    case "--help", "-h" -> {
                        System.out.println("Usage: tabloid INPUT.tbd [-o OUTPUT.py] [--force] [--check]");
                        System.out.println("Default: Python to stdout. --check validates without emitting. Output files are not overwritten without --force.");
                        return 0;
                    }
                    case "-o", "--output" -> {
                        if (output != null || ++i >= args.length) throw new IllegalArgumentException("Output requires one path");
                        output = Path.of(args[i]);
                    }
                    case "--force" -> force = true;
                    case "--check" -> check = true;
                    default -> {
                        if (input != null || args[i].startsWith("-")) throw new IllegalArgumentException("Unexpected argument: " + args[i]);
                        input = Path.of(args[i]);
                    }
                }
            }
            if (input == null || !input.toString().endsWith(".tbd")) throw new IllegalArgumentException("Supply a .tbd input file");
            if (check && (output != null || force)) throw new IllegalArgumentException("--check cannot be combined with output options");
            if (force && output == null) throw new IllegalArgumentException("--force requires an output path");
            if (output != null) {
                if (!output.toString().endsWith(".py")) throw new IllegalArgumentException("Output must end with .py");
                if (Files.exists(output) && Files.isSameFile(input, output)) throw new IllegalArgumentException("Input and output must differ");
            }
            String source;
            try (InputStream stream = Files.newInputStream(input)) {
                byte[] bytes = stream.readNBytes(1_048_577);
                if (bytes.length > 1_048_576) throw new CompileException("Input exceeds the 1 MiB byte limit");
                source = StandardCharsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)).toString();
            }
            if (source.startsWith("\uFEFF")) source = source.substring(1);
            String python = Compiler.compile(source);
            if (check) { System.err.println("Validated " + input.getFileName()); return 0; }
            if (output == null) {
                System.out.write(python.getBytes(StandardCharsets.UTF_8)); System.out.flush();
            } else {
                if (Files.isSymbolicLink(output)) throw new IOException("Refusing to replace an output symlink");
                if (!force) Files.writeString(output, python, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
                else {
                    Path absolute = output.toAbsolutePath();
                    Path temporary = Files.createTempFile(absolute.getParent(), ".tabloid-", ".tmp");
                    try {
                        Files.writeString(temporary, python, StandardCharsets.UTF_8);
                        Files.move(temporary, absolute, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
                    } finally { Files.deleteIfExists(temporary); }
                }
                System.err.println("Wrote " + output.getFileName());
            }
            return 0;
        } catch (CompileException exception) {
            System.err.println((input == null ? "source" : input.getFileName()) + ":" + exception.getMessage()); return 1;
        } catch (IOException | IllegalArgumentException exception) {
            System.err.println("error: " + exception.getMessage()); return 2;
        }
    }
}
