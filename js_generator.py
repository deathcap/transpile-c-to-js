# based on: https://github.com/eliben/pycparser/blob/843362984323854f2ee81b529faa20e148915481/pycparser/c_generator.py
#------------------------------------------------------------------------------
# pycparser: c_generator.py
#
# C code generator from pycparser AST nodes.
#
# Copyright (C) 2008-2015, Eli Bendersky
# License: BSD
#------------------------------------------------------------------------------
#from . import c_ast
from pycparser import c_ast


class JavaScriptGenerator(object):
    """ Uses the same visitor pattern as c_ast.NodeVisitor, but modified to
        return a value from each visit method, using string accumulation in
        generic_visit.
    """
    def __init__(self):
        # Statements start with indentation of self.indent_level spaces, using
        # the _make_indent method
        #
        self.indent_level = 0

    def _make_indent(self):
        return ' ' * self.indent_level

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, self.generic_visit)(node)

    def generic_visit(self, node):
        #~ print('generic:', type(node))
        if node is None:
            return ''
        else:
            return ''.join(self.visit(c) for c_name, c in node.children())

    def visit_Constant(self, n):
        return n.value

    def visit_ID(self, n):
        return n.name
    
    def visit_Pragma(self, n):
        ret = '#pragma'
        if n.string:
            ret += ' ' + n.string
        return ret

    def visit_ArrayRef(self, n):
        arrref = self._parenthesize_unless_simple(n.name)
        return arrref + '[' + self.visit(n.subscript) + ']'

    def visit_StructRef(self, n):
        sref = self._parenthesize_unless_simple(n.name)
        # JS: structure->member dereference to structure.member
        #return sref + n.type + self.visit(n.field)
        return sref + '.' + self.visit(n.field)

    def visit_FuncCall(self, n):
        fref = self._parenthesize_unless_simple(n.name)
        return fref + '(' + self.visit(n.args) + ')'

    def visit_UnaryOp(self, n):
        operand = self._parenthesize_unless_simple(n.expr)
        if n.op == 'p++':
            return '%s++' % operand
        elif n.op == 'p--':
            return '%s--' % operand
        elif n.op == 'sizeof':
            # Always parenthesize the argument of sizeof since it can be
            # a name.
            return 'sizeof(%s)' % self.visit(n.expr)
        # JS: *pointer dereference TODO
        elif n.op == '*':
            return '%s' % (operand,)
        # JS: &address of TODO
        elif n.op == '&':
            return '%s' % (operand,)
        else:
            return '%s%s' % (n.op, operand)

    def visit_BinaryOp(self, n):
        lval_str = self._parenthesize_if(n.left,
                            lambda d: not self._is_simple_node(d))
        rval_str = self._parenthesize_if(n.right,
                            lambda d: not self._is_simple_node(d))

        # JS: use strict comparison operators
        if n.op == '==':
            op = '==='
        elif n.op == '!=':
            op = '!=='
        else:
            op = n.op

        return '%s %s %s' % (lval_str, op, rval_str)

    def visit_Assignment(self, n):
        rval_str = self._parenthesize_if(
                            n.rvalue,
                            lambda n: isinstance(n, c_ast.Assignment))
        lval_str = self.visit(n.lvalue)

        # JS: can't translate the *p++ = ... pattern (assignable pointers)
        if '++' in lval_str or '--' in lval_str:
            return '/* FIXME: %s %s %s */0' % (lval_str, n.op, rval_str)

        #return '%s %s %s' % (self.visit(n.lvalue), n.op, rval_str)
        return '%s %s %s' % (lval_str, n.op, rval_str)

    def visit_IdentifierType(self, n):
        return ' '.join(n.names)

    def _visit_expr(self, n):
        if isinstance(n, c_ast.InitList):
            # JS: initializer lists, lets go with array syntax for now TODO: object literal syntax?
            return '[' + self.visit(n) + ']'
            #return '{' + self.visit(n) + '}'
        elif isinstance(n, c_ast.ExprList):
            return '(' + self.visit(n) + ')'
        else:
            return self.visit(n)

    def visit_Decl(self, n, no_type=False):
        # no_type is used when a Decl is part of a DeclList, where the type is
        # explicitly only for the first declaration in a list.
        #
        s = n.name if no_type else self._generate_decl(n)
        if n.bitsize: s += ' : ' + self.visit(n.bitsize)
        if n.init:
            s += ' = ' + self._visit_expr(n.init)
        return s

    def visit_DeclList(self, n):
        s = self.visit(n.decls[0])
        if len(n.decls) > 1:
            s += ', ' + ', '.join(self.visit_Decl(decl, no_type=True)
                                    for decl in n.decls[1:])
        return s

    def visit_Typedef(self, n):
        s = ''
        #if n.storage: s += ' '.join(n.storage) + ' '
        #s += self._generate_type(n.type)
        return s

    def visit_Cast(self, n):
        # JS: no type information in casts, return expression as-is
        #s = '(' + self._generate_type(n.to_type) + ')'
        #return s + ' ' + self._parenthesize_unless_simple(n.expr)
        return self._parenthesize_unless_simple(n.expr)

    def visit_ExprList(self, n):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self._visit_expr(expr))
        return ', '.join(visited_subexprs)

    def visit_InitList(self, n):
        visited_subexprs = []
        for expr in n.exprs:
            visited_subexprs.append(self._visit_expr(expr))
        return ', '.join(visited_subexprs)

    def visit_Enum(self, n):
        s = 'enum'
        if n.name: s += ' ' + n.name
        if n.values:
            s += ' {'
            for i, enumerator in enumerate(n.values.enumerators):
                s += enumerator.name
                if enumerator.value:
                    s += ' = ' + self.visit(enumerator.value)
                if i != len(n.values.enumerators) - 1:
                    s += ', '
            s += '}'
        return s

    def visit_FuncDef(self, n):
        decl = self.visit(n.decl)
        self.indent_level = 0
        body = self.visit(n.body)
        if n.param_decls:
            knrdecls = ';\n'.join(self.visit(p) for p in n.param_decls)
            return decl + '\n' + knrdecls + ';\n' + body + '\n'
        else:
            return decl + '\n' + body + '\n'

    def visit_FileAST(self, n):
        s = ''
        for ext in n.ext:
            if isinstance(ext, c_ast.FuncDef):
                s += self.visit(ext)
            elif isinstance(ext, c_ast.Pragma):
                s += self.visit(ext) + '\n'
            else:
                # JS: skip top-level code, mainly useless - only emit function code TODO
                continue
                # JS: only add non-empty lines
                line = self.visit(ext)
                if len(line) == 0:
                    continue
                # JS: try to avoid emitting function prototypes TODO: how to detect reliably?
                if line.startswith('function') and '\n' not in line:
                    continue
                s += self.visit(ext) + ';\n'
        return s

    def visit_Compound(self, n):
        s = self._make_indent() + '{\n'
        self.indent_level += 2
        if n.block_items:
            s += ''.join(self._generate_stmt(stmt) for stmt in n.block_items)
        self.indent_level -= 2
        s += self._make_indent() + '}\n'
        return s

    def visit_EmptyStatement(self, n):
        return ';'

    def visit_ParamList(self, n):
        return ', '.join(self.visit(param) for param in n.params)

    def visit_Return(self, n):
        s = 'return'
        if n.expr: s += ' ' + self.visit(n.expr)
        return s + ';'

    def visit_Break(self, n):
        return 'break;'

    def visit_Continue(self, n):
        return 'continue;'

    def visit_TernaryOp(self, n):
        s = self._visit_expr(n.cond) + ' ? '
        s += self._visit_expr(n.iftrue) + ' : '
        s += self._visit_expr(n.iffalse)
        return s

    def visit_If(self, n):
        s = 'if ('
        if n.cond: s += self.visit(n.cond)
        s += ')\n'
        s += self._generate_stmt(n.iftrue, add_indent=True)
        if n.iffalse:
            s += self._make_indent() + 'else\n'
            s += self._generate_stmt(n.iffalse, add_indent=True)
        return s

    def visit_For(self, n):
        s = 'for ('
        if n.init: s += self.visit(n.init)
        s += ';'
        if n.cond: s += ' ' + self.visit(n.cond)
        s += ';'
        if n.next: s += ' ' + self.visit(n.next)
        s += ')\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        return s

    def visit_While(self, n):
        s = 'while ('
        if n.cond: s += self.visit(n.cond)
        s += ')\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        return s

    def visit_DoWhile(self, n):
        s = 'do\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        s += self._make_indent() + 'while ('
        if n.cond: s += self.visit(n.cond)
        s += ');'
        return s

    def visit_Switch(self, n):
        s = 'switch (' + self.visit(n.cond) + ')\n'
        s += self._generate_stmt(n.stmt, add_indent=True)
        return s

    def visit_Case(self, n):
        s = 'case ' + self.visit(n.expr) + ':\n'
        for stmt in n.stmts:
            s += self._generate_stmt(stmt, add_indent=True)
        return s

    def visit_Default(self, n):
        s = 'default:\n'
        for stmt in n.stmts:
            s += self._generate_stmt(stmt, add_indent=True)
        return s

    def visit_Label(self, n):
        return n.name + ':\n' + self._generate_stmt(n.stmt)

    def visit_Goto(self, n):
        #return 'goto ' + n.name + ';'
        return '// FIXME: goto ' + n.name + ';'

    def visit_EllipsisParam(self, n):
        # JS: spread parameters, must be named
        return '...args'
        #return '...'

    def visit_Struct(self, n):
        return self._generate_struct_union(n, 'struct')

    def visit_Typename(self, n):
        return self._generate_type(n.type)

    def visit_Union(self, n):
        return self._generate_struct_union(n, 'union')

    def visit_NamedInitializer(self, n):
        s = ''
        for name in n.name:
            if isinstance(name, c_ast.ID):
                s += '.' + name.name
            elif isinstance(name, c_ast.Constant):
                s += '[' + name.value + ']'
        s += ' = ' + self._visit_expr(n.expr)
        return s

    def visit_FuncDecl(self, n):
        return self._generate_type(n)

    def _generate_struct_union(self, n, name):
        """ Generates code for structs and unions. name should be either
            'struct' or union.
        """
        # JS: struct/union to class
        if n.name is None: return '' # anonymous class?
        s = 'class ' + n.name + ' {\n'
        self.indent_level += 1
        s += self._make_indent()
        s += 'constuctor() {'

        #s = name + ' ' + (n.name or '')
        if n.decls:
            s += '\n'
            #s += self._make_indent()
            self.indent_level += 2
            #s += '{\n'
            for decl in n.decls:
                # TODO: change let foo; to this.foo = ???
                s += self._generate_stmt(decl)
            self.indent_level -= 2
        s += self._make_indent() + '}'

        # JS: close constructor
        self.indent_level -= 1
        s += '\n'
        s += self._make_indent() + '}'
        return s

    def _generate_stmt(self, n, add_indent=False):
        """ Generation from a statement node. This method exists as a wrapper
            for individual visit_* methods to handle different treatment of
            some statements in this context.
        """
        typ = type(n)
        if add_indent: self.indent_level += 2
        indent = self._make_indent()
        if add_indent: self.indent_level -= 2

        if typ in (
                c_ast.Decl, c_ast.Assignment, c_ast.Cast, c_ast.UnaryOp,
                c_ast.BinaryOp, c_ast.TernaryOp, c_ast.FuncCall, c_ast.ArrayRef,
                c_ast.StructRef, c_ast.Constant, c_ast.ID, c_ast.Typedef,
                c_ast.ExprList):
            # These can also appear in an expression context so no semicolon
            # is added to them automatically
            #
            return indent + self.visit(n) + ';\n'
        elif typ in (c_ast.Compound,):
            # No extra indentation required before the opening brace of a
            # compound - because it consists of multiple lines it has to
            # compute its own indentation.
            #
            return self.visit(n)
        else:
            return indent + self.visit(n) + '\n'

    def _generate_decl(self, n):
        """ Generation from a Decl node.
        """
        s = ''
        #if n.funcspec: s = ' '.join(n.funcspec) + ' ' # JS: no function specifier (inline, ...)
        #if n.storage: s += ' '.join(n.storage) + ' ' # JS: no storage qualifiers (const, ...)
        s += self._generate_type(n.type)
        return s

    def _generate_type(self, n, modifiers=[]):
        """ Recursive generation from a type node. n is the type node.
            modifiers collects the PtrDecl, ArrayDecl and FuncDecl modifiers
            encountered on the way down to a TypeDecl, to allow proper
            generation from it.
        """
        typ = type(n)
        #~ print(n, modifiers)

        if typ == c_ast.TypeDecl:
            s = ''
            #if n.quals: s += ' '.join(n.quals) + ' ' # JS: no const/extern/etc. qualifiers
            #s += self.visit(n.type) # JS: no types

            nstr = n.declname if n.declname else ''
            isFunction = False
            # Resolve modifiers.
            # Wrap in parens to distinguish pointer to array and pointer to
            # function syntax.
            #
            for i, modifier in enumerate(modifiers):
                if isinstance(modifier, c_ast.ArrayDecl):
                    if (i != 0 and isinstance(modifiers[i - 1], c_ast.PtrDecl)):
                        nstr = '(' + nstr + ')'
                    #nstr += '[' + self.visit(modifier.dim) + ']' # JS: no array [] dimensions
                elif isinstance(modifier, c_ast.FuncDecl):
                    if (i != 0 and isinstance(modifiers[i - 1], c_ast.PtrDecl)):
                        nstr = '(' + nstr + ')'

                    # JS: parameter declaration variables do not have let/const TODO: fix hack, detect parameter context
                    paramDecls = self.visit(modifier.args)
                    paramDecls = paramDecls.replace('let ', '')
                    paramDecls = paramDecls.replace('const ', '')

                    nstr += '(' + paramDecls + ')'
                    nstr = 'function ' + nstr # JS: function
                    isFunction = True
                elif isinstance(modifier, c_ast.PtrDecl):
                    pass
                    # JS: no pointers
                    #if modifier.quals:
                    #    nstr = '* %s %s' % (' '.join(modifier.quals), nstr)
                    #else:
                    #    nstr = '*' + nstr
            #if nstr: s += ' ' + nstr
            # JS: declare local variables
            if not isFunction:
                # TODO: emit const when can, but see https://github.com/deathcap/transpile-c-to-js/issues/2
                #if False and 'const' in n.quals: # TODO: make this smarter, 
                #    # if has a 'const' qualifier try to declare with 'const'
                #    s = 'const ' + s
                # otherwise, ES6 declares new variables with 'let'
                s = 'let ' + s

            if nstr: s += nstr # JS: remove whitespace
            if len(nstr) == 0: s = self.visit(n.type) # JS: if this is _only_ for a type, then emit it - for sizeof() only!
            return s
        elif typ == c_ast.Decl:
            return self._generate_decl(n.type)
        elif typ == c_ast.Typename:
            return self._generate_type(n.type)
        elif typ == c_ast.IdentifierType:
            return ' '.join(n.names) + ' '
        elif typ in (c_ast.ArrayDecl, c_ast.PtrDecl, c_ast.FuncDecl):
        #elif typ in (c_ast.ArrayDecl, c_ast.PtrDecl):
            return self._generate_type(n.type, modifiers + [n])
        else:
            return self.visit(n)

    def _parenthesize_if(self, n, condition):
        """ Visits 'n' and returns its string representation, parenthesized
            if the condition function applied to the node returns True.
        """
        s = self._visit_expr(n)
        if condition(n):
            return '(' + s + ')'
        else:
            return s

    def _parenthesize_unless_simple(self, n):
        """ Common use case for _parenthesize_if
        """
        return self._parenthesize_if(n, lambda d: not self._is_simple_node(d))

    def _is_simple_node(self, n):
        """ Returns True for nodes that are "simple" - i.e. nodes that always
            have higher precedence than operators.
        """
        return isinstance(n,(   c_ast.Constant, c_ast.ID, c_ast.ArrayRef,
                                c_ast.StructRef, c_ast.FuncCall))
