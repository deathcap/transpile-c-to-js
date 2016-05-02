'use stritct';

const lexer = require('node-c-lexer');
const fs = require('fs');

const tokenStream = lexer.lexUnit.tokenize(fs.readFileSync('hello.c'));
//console.log(tokenStream);
for (let token of tokenStream) {
  //process.stdout.write(token.lexeme + ' ');
  console.log(token.lexeme, token.tokenClass);
  // TODO: convert C syntax to JavaScript syntax
  /* example:

   int n = 0;
   char *s = "foo";

   int main(int argc, char **argv) {
      printf("Hello, world!\n");
      return 0;
   }

   should convert to:


   let n = 0;
   let s = "foo";

   function main(argc, argv) {
      printf('Hello, world!\n');
      return 0;
   }


   notably: remove type info, let/const decls, args bare, functions, calls..
   much syntax can be preserved unmodified
   */
}
