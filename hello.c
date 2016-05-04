
#include <stdio.h>

int main(int argc, char **argv) {
    int a = 1;
    const double pi = 3.14159;
    static char *s = "foo";

    printf("Hello, world!\n");

    if (a == 2) exit(EXIT_FAILURE);

    return 0;
}
