# transpile-c-to-js

An experiment in transpiling C source code to JavaScript using [pycparser](https://github.com/eliben/pycparser)

Unlike [emscriptem](https://github.com/kripken/emscripten), for example, the compiled output is not
low-level/asm.js but intended to resemble the high-level C source code as much as possible.
The resulting JavaScript output is meant to be syntactically valid, but will not meaningfully execute
without further manual porting efforts.

Usage:

    sudo easy_install pycparser
    python ptranspile.py hello.c

Example C input:

```c
#include <stdio.h>

int main(int argc, char **argv) {
    int a = 1;
    const double pi = 3.14159;
    static char *s = "foo";

    printf("Hello, world!\n");

    if (a == 2) exit(1);

    return 0;
}
```

Example JavaScript output:

```javascript
function main(argc, argv)
{
  let a = 1;
  const pi = 3.14159;
  let s = "foo";
  printf("Hello, world!\n");
  if (a === 2)
    exit(1);

  return 0;
}
```

## License

MIT
