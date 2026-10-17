# Attribution and external components

## Tabloid

The original Tabloid programming language was created by Linus Lee
([thesephist/tabloid](https://github.com/thesephist/tabloid)). This repository
implements a documented coursework dialect and credits the language's origin.
It does not bundle the upstream JavaScript interpreter. Upstream materials
retain their [MIT license](https://github.com/thesephist/tabloid/blob/master/LICENSE).

## ANTLR

ANTLR is the parser generator and Java runtime used by the build. Version
**4.13.1** is downloaded from the [official ANTLR site](https://www.antlr.org/download.html),
not included in the source upload. It retains its
[BSD 3-clause license](https://github.com/antlr/antlr4/blob/4.13.1/LICENSE.txt).

Pinned SHA-256 of `antlr-4.13.1-complete.jar`:

```text
bc13a9c57a8dd7d5196888211e5ede657cb64a3ce968608697e4f668251a8487
```

ANTLR-generated Java is recreated from this project's grammar during each build.
If distributing ANTLR or a runtime-bundled application in a future binary
release, retain the applicable upstream notices and licenses. The source ZIP
does not redistribute the complete ANTLR JAR.

## Reference documentation

- [ANTLR left recursion and precedence](https://github.com/antlr/antlr4/blob/master/doc/left-recursion.md).
- [Original Tabloid README](https://github.com/thesephist/tabloid), used to identify compatibility boundaries.

Java and Python installations are external prerequisites. They are not included
or relicensed by this repository.
