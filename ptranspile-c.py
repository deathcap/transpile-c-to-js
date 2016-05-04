
import sys
sys.path.extend(['.', 'pycparser'])

# sudo easy_install pycparser
from pycparser import parse_file

import c_generator

def translate(filename):
    ast = parse_file(filename,
        use_cpp=True,
        cpp_path='gcc',
        cpp_args=[
            "-E",
            "-D__FBSDID(x)=", # FreeBSD identifier
            "-D__attribute__(x)=", # attribute extension
            "-D__builtin_va_list=void*", # include/x86/_types.h:154 typedef __builtin_va_list   __va_list; 
            "-D__inline=",
            "-D__asm(x)=",

            "-D_RUNETYPE_H_=1", # skip include/runtype.h
            "-D_RuneLocale=void*", # but it defines this type

            "-D_Noreturn=",

            "-U__BLOCKS__", # no (^) syntax: include/stdlib.h: int  atexit_b(void (^)(void));
            "-U__nonnull", # avoid __nonnull redefinition

            "-nostdinc",
            "-Iinclude", # copy from /usr/include
            #"-Ipycparser/utils/fake_libc_include",
            ])
    generator = c_generator.CGenerator()
    print(generator.visit(ast))

translate(sys.argv[1])
