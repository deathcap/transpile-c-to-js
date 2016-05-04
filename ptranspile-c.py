
# sudo easy_install pycparser
from pycparser import parse_file, c_generator

def translate(filename):
    ast = parse_file(filename, use_cpp=True)
    generator = c_generator.CGenerator()
    print(generator.visit(ast))

translate('hello.c')
