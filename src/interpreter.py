#!/usr/bin/env python3

# Test programs:
#  1+1 2 3
#  /+1 2 3
#  

import sys
import functools
from pprint import pprint
from arpeggio.cleanpeg import ParserPEG
from arpeggio import PTNodeVisitor, visit_parse_tree

version = "0.0.0"
MAXRANK = 100

grammar = r"""
    program    = (NL? statement)*
    statement  = (space? expression)+
    expression = call / function
    call       = assignment
               / literal ','? function call
               / function call
               / literal

    function   = conjunction / '(' (assignment / conjunction / adverb) ')'
               / primitive / namedfunc / adverb / bind
               / tacitb / lambda
    primitive  = r'[\!%=\?+*;|-][,:]*'
    namedfunc  = r'[A-W][a-z]*'
    bind       = literal function
    adverb     = ('/' / '~') advgroup
    advgroup   = '(' (conjunction / adverb) ')' / adverb / bind / primitive / namedfunc / tacitb / lambda
    conjunction= literal '^' function / literal? conjgroup (r'[@`][,:]*' literal? conjgroup)+
    conjgroup  = '(' (conjunction / adverb) ')' / adverb / bind / primitive / namedfunc / tacitb / lambda
    tacit      = (function / literal)+
    tacitb     = '{' tacit '}'
    lambda     = '[' statement ']'

    assignment = r'[A-W][a-z]*' space? ':' space? tacit
               / r'[X-Z][a-z]*' space? ':' space? call

    item       = braces / number / string / variable
    braces     = '(' &call expression ')'
    
    literal    = list / item
    list       = item (space? item / space? braces)+
    number     = r'_?\d*\.\d*|_?\d+'
    string     = r'"(?:\\.|[^"\\])*?"' / r'\'(?:.)'
    variable   = r'[X-Z][a-z]*'

    space      = (' ' / '\t')+
    NL         = ('\r' / '\n')+
"""

code = '~/*1R10'

whitespace = ' \t'
newline = '\n'
node = lambda f: lambda self, node, children: f(node.value)
ignore = lambda words, l: [x for x in l if not any(x == w for w in words)]

# For printing the AST.
class SyntaxVisitor(PTNodeVisitor):
    def visit_program(self, node, children):
        return ignore(newline, children)

    def visit_statement(self, node, children):
        return children

    def visit_expression(self, node, children):
        return children[0]

    def visit_call(self, node, children):
        if len(children) == 4:
            return ('call', children[2], children[0], children[3])
        elif len(children) == 3:
            return ('call', children[1], children[0], children[2])
        elif len(children) == 2:
            return ('call', children[0], children[1])
        return children[0]

    def visit_adverb(self, node, children):
        return ('adverb', node[0].value, children[1])

    def visit_conjunction(self, node, children):
        return ('conjunction', [x.value for x in node[1::2]], children)

    def visit_function(self, node, children):
        return children[0] if len(children) == 1 else children[1]

    def visit_primitive(self, node, children):
        return node.value

    def visit_namedfunc(self, node, children):
        return ('function', node.value)

    def visit_item(self, node, children):
        return children[0]

    def visit_braces(self, node, children):
        return children[0]

    def visit_literal(self, node, children):
        return children[0]

    def visit_list(self, node, children):
        return ignore(whitespace, children)

    def visit_number(self, node, children):
        v = node.value.replace('_', '-')
        return float(v) if '.' in v else int(v)

    def visit_string(self, node, children):
        return node.value.decode('string-escape')

    def visit_space(self, node, children):
        return node.value

    def visit_NL(self, node, children):
        return node.value

    def visit_variable(self, node, children):
        return ('variable', node.value)

    def visit_assignment(self, node, children):
        return ('assign', node[0].value, children[-1])

    def visit_tacit(self, node, children):
        return ('tacit', children)

    def visit_lambda(self, node, children):
        return ('lambda', children[0])

depth = lambda x: isinstance(x, str) \
                  or isinstance(x, (list, tuple)) and (len(x) and depth(x[0])) + 1
foldr = lambda f, xs: functools.reduce(f, reversed(xs))
flip  = lambda f: rank(lambda x, y=None: f(y, x), (f.rank[0], f.rank[2], f.rank[1]))
bind  = lambda f, x: lambda y, _=0: call(f, x, y)
def rank(f, r, p=(0, 0, 0)):
    if not isinstance(r, (tuple, list)):
        r = (r, r, r)
    elif len(r) == 1:
        r = (r[0], r[0], r[0])
    elif len(r) == 2:
        r = (r[1], r[0], r[1])
    f.rank = r
    f.pad = p
    return f
def rankof(f):
    f = resolve(f)
    if hasattr(f, 'rank'):
        return f.rank
    return (MAXRANK, MAXRANK, MAXRANK)
def applyN(f, n, x, y):
    for _ in range(n):
        x = call(f, x, y)
    return x
def padrank(f):
    try:
        return f.pad
    except:
        return (0, 0, 0)
def resolve(x):
    if isinstance(x, tuple):
        if x[0] == 'variable':
            x = functions[x[1]]
        else:
            raise 'Unexpected tuple ' + x + ' - blame the developer'
    return x
def orderrank(f, m, l, r):
    rank = rankof(f)
    return (rank[m], rank[l], rank[r])

def adjust(l):
    r = []
    m = max(depth(x) for x in l)
    for x in l:
        dx = depth(x)
        for _ in range(m - dx):
            x = [x]
        r += [x]
    return r

# Please remember: x is the right argument and y is the left one.

primitives = {'+': lambda x, y=0: y + x,
              '-': lambda x, y=None: x-y if y is not None else -x,
              '*': lambda x, y=None: x * y if y is not None else (x>0)-(x<0),
              '%': lambda x, y=1: y/x,
              ';': lambda x, y=None: y+x if y is not None else [z for y in x for z in y],
              ';,': lambda x, y=None: [y, x] if y is not None else list(flatten(x)),
              '|': lambda x, y=None: x%y if y is not None else x if x>0 else -x
              }
primitives['+'].rank = (0, 0, 0)
primitives['-'].rank = (0, 0, 0)
primitives['*'].rank = (0, 0, 0)
primitives['%'].rank = (0, 0, 0)
primitives[';'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives[';'].pad = (2, 1, 1)
primitives[';,'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives[';,'].pad = (1, 0, 0)
primitives['|'].rank = (0, 0, 0)

adverbs = {'/': lambda f: rank(lambda x, y=None: \
                                   foldr(lambda x, y: call(f, y, x), x) \
                                   if y is None \
                                   else call(f, y, x),
                               (MAXRANK, MAXRANK, -1)),
           '~': lambda f: lambda x, y=None: call(f, x, x) if y is None else call(f, x, y),
           }

def agenda(f, a, x, y):
    v = a[call(f, x) if y is None else call(f, y, x)]
    if y is None:
        return call(v, x)
    return call(v, y, x)

conjunctions = {'^': lambda f, n: rank(lambda x, y=None: \
                                           call(f, x) \
                                           if y is None \
                                           else call(f, y, x),
                                       n),
                '@': lambda f, g: rank(lambda x, y=None: call(g, call(f, x) if y is None else call(f, y, x)),
                                       (MAXRANK, MAXRANK, MAXRANK)),
                '`': lambda f, g: g+[f] if isinstance(g, list) else [g, f],
                '@,': lambda f, a: rank(lambda x, y=None: agenda(f, a, x, y), rankof(f))
                }

def partition(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def table(l, dimensions):
    d = functools.reduce(lambda x, y: x*y, dimensions)
    while len(l) < d:
        l = l + l
    l = l[:d]
    for x in dimensions:
        l = partition(l, x)
    return l[0]

def flatten(l):
    for el in l:
        if isinstance(el, list) and not isinstance(el, str):
            for sub in flatten(el):
                yield sub
        else:
            yield el

functions = {'R': rank(lambda x, y=None: list(range(y, x+(x>y or -1), x>y or -1)) \
                                         if y is not None \
                                         else list(range(x)),
                       (0, 0, 0)),
             'T': rank(lambda x, y=None: table(list(range(functools.reduce(lambda x, y: x*y, x))), x)
                                         if y is None
                                         else table(x, y),
                       (1, 1, 1), (1, 1, 1)),
             'D': lambda x, y=None: +depth(x),
             'L': lambda x, y=None: len(x),
             'S': rank(lambda x, y=' ': x.split(y), (1, 1, 1)),
             'A': lambda x, y=None: x,
             'B': lambda x, y=None: y if y is not None else x,
             'Ld': rank(lambda x, y=1: x[y:], (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'Lr': rank(lambda x, y=1: x[:-y], (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'Lt': rank(lambda x, y=None: [[x]], (MAXRANK, MAXRANK, MAXRANK)),
             'H': rank(lambda x, y=None: x[0] if y is None else x[:y], (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'E': rank(lambda x, y=None: x[-1] if y is None else x[y:], (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'N': rank(lambda x, y=0: x[y],
                       (1, 0, MAXRANK), (1, 0, 1)),
             'P': rank(lambda x, y=None: (print(y.format(*x)) if y is not None else print(x)) or 0,
                       (MAXRANK, 1, MAXRANK), (0, 0, 1))
             }

def call(f, x, y=None, xdepth=0, ydepth=0):
    x, y, f = resolve(x), resolve(y), resolve(f)
    rank, lrank, rrank = rankof(f)
    if y is None:
        dx = depth(x)
        if 0 > rank < xdepth or dx > rank >= 0:
            return [call(f, z, None, xdepth-1) for z in x]
#        if not hasattr(f, '__call__'):
#            return f
        pad = padrank(f)[0]
        if dx < pad and isinstance(x, str) != pad:
            for _ in range(pad - dx):
                x = [x]
        return f(x)
    dx, dy = depth(x), depth(y)
    xr = 0 > lrank < xdepth or dx > lrank >= 0
    yr = 0 > rrank < ydepth or dy > rrank >= 0
    if xr and yr:
        return [call(f, a, b, xdepth-1, ydepth-1) for a, b in zip(x, y)]
    elif xr:
        return [call(f, z, y, xdepth-1, ydepth) for z in x]
    elif yr:
        return [call(f, x, z, xdepth, ydepth-1) for z in y]
    pad = padrank(f)
    if dx < pad[1] != isinstance(x, str):
        for _ in range(pad[1] - dx):
            x = [x]
    if dy < pad[2] != isinstance(y, str):
        for _ in range(pad[2] - dy):
            y = [y]
#    if not hasattr(f, '__call__'):
#        return f
    return f(y, x)

def withAdverb(a, f):
    return adverbs[a](f)

def withConjunction(c, f, x):
    return conjunctions[c](f, x)

class InterpreterVisitor(PTNodeVisitor):
    def visit_program(self, node, children):
        return ignore(newline, children)

    def visit_statement(self, node, children):
        return children[-1]

    def visit_expression(self, node, children):
        return children[0]

    def visit_call(self, node, children):
        if len(children) == 4:
            return call(children[2], children[0], children[3])
        elif len(children) == 3:
            return call(children[1], children[0], children[2])
        elif len(children) == 2:
            return call(children[0], children[1])
        return children[0]

    def visit_adverb(self, node, children):
        return withAdverb(node[0].value, children[1])

    def visit_conjunction(self, node, children):
        if sum(1 for c in children if isinstance(c, tuple) or hasattr(c, '__call__'))>1:
            conjs = [x.value for x in node if x.value in conjunctions]
            children = [c for c in children if c not in conjunctions]
            print(conjs, children)
            g = children[0]
            if not hasattr(resolve(g), '__call__'):
                g = bind(children[1], g)
                children = children[1:]
            while len(children)>1:
                f = children[1]
                if not hasattr(resolve(f), '__call__'):
                    f = bind(children[2], f)
                    children = children[1:]
                g = conjunctions[conjs[0]](f, g)
                children = children[1:]
                conjs = conjs[1:]
            return g
        return withConjunction(node[1].value, children[1], children[0])

    def visit_function(self, node, children):
        return children[0]

    def visit_primitive(self, node, children):
        return primitives[node.value]

    def visit_namedfunc(self, node, children):
        return ('variable', node.value)

    def visit_item(self, node, children):
        return children[0]

    def visit_braces(self, node, children):
        x = children[0]
        try:
            return [c for c in x if c != []]
        except:
            return x

    def visit_literal(self, node, children):
        return children[0]

    def visit_list(self, node, children):
        return ignore([None], children)

    def visit_number(self, node, children):
        v = node.value.replace('_', '-')
        return float(v) if '.' in v else int(v)

    def visit_string(self, node, children):
        v = node.value.encode().decode('unicode_escape')
        return v[1:-1] if v[0] == '"' else v[1:]

    def visit_space(self, node, children):
        return None

    def visit_NL(self, node, children):
        return None

    def visit_variable(self, node, children):
        return ('variable', node.value)

    def visit_assignment(self, node, children):
        functions[node[0].value] = resolve(children[-1])
        return children[-1]

    def visit_tacit(self, node, children):
        def f(x, y=None):
            fs = children[::-1]
            fy = fs[0]
            vy = call(fy, y, x) if y is not None else call(fy, x)
            while len(fs)>1:
                fx = fs[2]
                ff = fs[1]
                if hasattr(resolve(fx), '__call__'):
                    vx = call(fx, y, x) if y is not None else call(fx, x)
                else:
                    vx = fx
                vy = call(ff, vx, vy)
                fs = fs[2:]
            return vy
        f.rank = (MAXRANK, MAXRANK, MAXRANK)
        if len(children) > 2:
            return f
        elif len(children) != 1:
            raise 'Invalid tacit expression'
        return children[0]

    def visit_lambda(self, node, children):
        return ('lambda', children[0])

    def visit_bind(self, node, children):
        return bind(children[1], children[0])

# TODO: Each column should have dffferent width
def printtable(v, w=0):
    dv = depth(v)
    if dv == 0 or isinstance(v, str):
        print(v)
    elif dv == 1:
        for x in v:
            print(('{:'+str(w)+'}').format(x), end=' ')
        print()
    elif dv > 1:
        vl = len(v)
        if w == 0:
            w = max(len(str(x)) for x in flatten(v))
        for i, x in enumerate(v):
            printtable(x, w)
            if i < vl-1:
                print('\n'*(dv-2), end='')

if __name__ == '__main__':
    parser = ParserPEG(grammar, "program", skipws=False)
    tablemode = '-t' in sys.argv
    if '-repl' in sys.argv:
        print("Joe REPL - Version " + version)
        print("Run Help for help.")
        while True:
            code = input('   ')
            if code == 'exit':
                break
            if code.strip() != '':
                try:
                    tree = parser.parse(code)
                    v = visit_parse_tree(tree, InterpreterVisitor())[0]
                    if v is not None and not hasattr(v, '__call__'):
                        if tablemode:
                            printtable(v)
                        else:
                            print(v)
                except Exception as e:
                    print("Error\n", e)
    else:
        if '-c' in sys.argv:
            code = sys.argv[sys.argv.index('-c')+1]
        tree = parser.parse(code)
        if '-ast' in sys.argv:
            pprint(visit_parse_tree(tree, SyntaxVisitor()))
        else:
            v = visit_parse_tree(tree, InterpreterVisitor())
            if tablemode:
                printtable(v[-1])
            else:
                print(v[-1])


