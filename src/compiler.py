#!/bin/env python2

import sys
from pprint import pprint
import parser
import optimizer

usedBuiltins = set()
funcTranslate = { '+': 'add'
                , '-': 'sub'
                , '*': 'mul'
                , '/': 'div'
                , 'M': 'map'
                , 'F': 'reduce'
                , 'Z': 'zip'
                , 'J': 'join'
                , 'S': 'split'
                , 'p': 'print_'
                , '~': '(lambda*a:None)'
                , 'I': 'raw_input'
                , ':': 'swap'
                , 'i': 'int_'
                , 'f': 'float_'
                , 's': 'str' }

builtins = { '+': 'add = lambda x, y: depth(x) > depth(y) and [add(z, y) for z in x] or depth(y) > depth(x) and [add(x, z) for z in y] or x + y'
           , '-': 'sub = lambda x, y: depth(x) > depth(y) and [sub(z, y) for z in x] or depth(y) > depth(x) and [sub(x, z) for z in y] or x - y'
           , '*': 'mul = lambda x, y: depth(x) > depth(y) and [mul(z, y) for z in x] or depth(y) > depth(x) and [mul(x, z) for z in y] or x * y'
           , '/': 'div = lambda x, y: depth(x) > depth(y) and [div(z, y) for z in x] or depth(y) > depth(x) and [div(x, z) for z in y] or x / y'
           , 'J': 'join = lambda x, y: x.join(str(z) for z in y)'
           , 'S': 'split = lambda x, y: y.split(str(x))'
           , ':': 'swap = lambda f: lambda x, y: f(y, x)'
           , 'i': 'int_ = lambda x: isinstance(x, list) and [int_(y) for y in x] or int(x)'
           , 'f': 'float_ = lambda x: isinstance(x, list) and [float_(y) for y in x] or float(x)'
           , 'p': 'def print_(x):\n    if x != None: print(x)\n    return x' }

def call(tree):
    return select(tree[1]) + '(' + ','.join(str(select(x)) for x in tree[2]) + ')'

def builtin(tree):
    usedBuiltins.add(tree[1])
    return funcTranslate.get(tree[1], tree[1])

def curry(tree):
    return 'curry(' + select(tree[1]) + ',' + select(tree[2]) + ')'

def literal(tree):
    return '[' + ','.join(map(select, tree[1])) + ']' if isinstance(tree[1], list) else (tree[1] if isinstance(tree[1], basestring) else str(tree[1]))

def variable(tree):
    return '_' + str(ord(tree[1]))

def makeLambda(tree):
    return '(lambda _' + str(ord(tree[1][1])) + ': ' + select(tree[2]) + ')'

def compose(tree):
    return '(lambda *args:' + ''.join(select(x) + '(' for x in tree[1]) + '*args' + ')' * (len(tree[1])+1)

def arithmetic(tree):
    return select(tree[2][0]) + tree[1] + select(tree[2][1])

compileFuncs = { 'call': call
               , 'func': builtin
               , 'curry': curry
               , 'literal': literal
               , 'lambda': makeLambda
               , 'variable': variable
               , 'compose': compose
               , 'arithmetic': arithmetic }

def select(tree):
    return compileFuncs[tree[0]](tree)

def transform(tree):
    result = ''
    for line in tree:
        for expr in line:
            result += select(expr) + '\n'
    return result

def headers():
    static =  'depth = lambda x: isinstance(x, (list, tuple)) and depth(x[0]) + 1\n'
    static += 'curry = lambda f, x: lambda *args: f(x, *args)\n'
    return static + ''.join(builtins[x] + '\n' for x in usedBuiltins if x in builtins)

def compile(code, showoptparsed, showparsed, example, run, minify):
    tree = parser.parse(code)
    opttree = optimizer.optimize(tree)
    if not example:
        if showparsed:
            print "Abstract Syntax Tree:"
            pprint(tree)
        if showoptparsed:
            print "Optimized Abstract Syntax Tree:"
            pprint(opttree)
        if showoptparsed or showparsed:
            return
    prog = transform(opttree)
    head = headers()
    if minify == 1:
        head = 'exec """' + head.encode('zlib').encode('base64') + '""".decode("base64").decode("zlib")\n'
    if minify == 2:
        prog = 'exec """' + prog.encode('zlib').encode('base64') + '""".decode("base64").decode("zlib")'
    if example:
        print "Code:"
        print code
        if code[-1] != '\n': print
        if showparsed:
            print "Abstract Syntax Tree:"
            pprint(tree)
            print
        if showoptparsed:
            print "Optimized Abstract Syntax Tree:"
            pprint(opttree)
            print
            print "Unoptimized Output code:"
            print transform(tree)
        print "%sOutput code:" % ('Optimized ' if showoptparsed else '')
        print prog
        if prog[-1] != '\n': print
        if run:
            print "Functionality:"
    if run:
        exec head + prog in {}
    if run or example:
        return
    return head + prog

def main():
    if '-c' in sys.argv:
        code = sys.argv[-1]
    else:
        with open(sys.argv[-1], 'r') as f:
            code = f.read()
    parsed = '-p' in sys.argv
    optparsed = '-op' in sys.argv
    example = '-i' in sys.argv
    run = '-r' in sys.argv
    minify = '-m' in sys.argv and 2 or '-mh' in sys.argv and 1
    prog = compile(code, optparsed, parsed, example, run, minify)
    if prog:
        print prog


if __name__ == '__main__':
    main()