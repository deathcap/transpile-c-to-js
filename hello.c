
#include <stdio.h>

int main(int argc, char **argv) {
    int a = 1;
    const double pi = 3.14159;
    static char *s = "foo";

    printf("Hello, world's!\n");

    if (a == 2) exit(1);

    return 0;
}
