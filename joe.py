#!/usr/bin/env python3

# Test programs:
#  1+1 2 3
#  /+1 2 3
#  

import sys
import functools
import itertools
import random
import math
import marshal
import cmd
from pprint import pprint
from arpeggio.cleanpeg import ParserPEG
from arpeggio import PTNodeVisitor, visit_parse_tree

version = "0.1.2"
MAXRANK = 100

tests = [("""{/+%N)1 2 3 4""", 2.5),
         ("""(/*-,1R)5""", 120),
         ("""(2Lr0 1/,;$:/+@2ER)10""", [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]),
         ("""(VOeM;$C$,-:)"dsaasafd" """, [['a', 3], ['s', 2], ['d', 2], ['f', 1]]),
         ("""M-,~/!R5""", [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]),
         ]

grammar = r"""
    program    = (NL? statement)*
    statement  = (space? expression)+
    expression = call / function
    call       = assignment
               / literal ','? function call
               / function call
               / literal

    function   = conjunction / '(' (assignment / combination) ')'?
               / adverb / bind / primitive / namedfunc
               / tacitb / lambda
    primitive  = r'[\!#%=\?+*<>;|\]-][,:]*'
    namedfunc  = r'[A-W][a-z]*'
    bind       = literal function
    adverb     = ('/' / '~' / 'M' / "\\") advgroup
    advgroup   = '(' (assignment / combination) ')'? / adverb / bind / primitive / namedfunc / tacitb / lambda
    conjunction= conjlvl1 / conjlvl2 / conjlvl3
    conjlvl1   = literal ('^' / '/,') function
    conjlvl2   = literal? (conjlvl3 / conjgroup) (r'[$][,:]*' literal? (conjlvl1 / conjlvl3 / conjgroup))+
    conjlvl3   = literal? conjgroup (r'[@`][,:]*' (literal? conjgroup / literal conjunction))+
    conjgroup  = '(' (assignment / combination) ')'? / adverb / bind / primitive / namedfunc / tacitb / lambda
    tacit      = (function / literal)+
    tacitb     = '{' tacit ')'?
    lambda     = '[' statement ')'?

    assignment = r'[A-W][a-z]*'? space? ':' space? combination
               / r'[X-Z][a-z]*'? space? ':' space? call
    combination= function+

    item       = braces / number / string / variable
    braces     = '(' &call expression ')'?
    
    literal    = list / item
    list       = item (space? item)+
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

def memoize(f): 
    """Memoize any function."""
    cache = {}
    def decorated(*args):
        key = marshal.dumps(args)
        if key in cache:
            return cache[key]
        r = f(*args)
        cache[key] = r
        return r
    return decorated

def memoizef(f):
    cache = {}
    def deco(*args):
        key = tuple(args)
        if key in cache:
            return cache[key]
        r = f(*args)
        cache[key] = r
        return r
    return deco

usermemoize = memoizef

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

depth = lambda x: isinstance(x, (list, tuple)) and (len(x) and depth(x[0])) + 1
foldr = lambda f, xs, s=None: (functools.reduce(f, reversed(xs[:-1] if s is None else xs), xs[-1] if s is None else s) if len(xs) else [])
flip  = lambda f: rank(lambda x, y=None: f(y, x), (f.rank[0], f.rank[2], f.rank[1]))
bind  = lambda f, x: rank(lambda y, _=0: call(f, x, y), rankof(f))
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
    if not isinstance(l, list):
        return l
    r = []
    m = max(depth(x) for x in l)
    for x in l:
        dx = depth(x)
        for _ in range(m - dx):
            x = [x]
        r += [x]
    return r

def nest(x, n):
    for _ in range(n):
        x = [x]
    return x

def split(l, splitter):
    sl = len(splitter)
    r = []
    curr = []
    while len(l):
        if l[:sl] == splitter:
            r += [curr]
            curr = []
            l = l[sl:]
        else:
            curr += [l[0]]
            l = l[1:]
    if len(curr) > 0:
        r += [curr]
    return r

def join(l, j):
    r = []
    for x in l:
        r += x
        r += j
    return r[:-len(j)]

def unique(l, idfun=None):
    if idfun is None:
        idfun = lambda x: x
    seen = {}
    result = []
    for item in l:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def int2base(x, base):
    if x == 0: return [0]
    digits = []
    while x:
        digits.append(x % base[-1])
        x //= base[-1]
        if len(base) > 1:
            base = base[:-1]
    digits.reverse()
    return digits

def base2int(l, base):
    l = l[::-1]
    r = 0
    x = 0
    while len(l):
        r += l[0] * base[0]**x
        x += 1
        if len(base) > 1:
            base = base[1:]
        if l[0] < base[-1]:
            l = l[1:]
        else:
            l[0] = int(l[0] / base[0])
    return r

def padarray(l, lr=0, padder=0):
    l = [x if isinstance(x, list) else [x] for x in l]
    w = max(len(x) for x in l)
    if lr == 0:
        return [[padder]*(w-len(x))+x for x in l]
    else:
        return [x+[padder]*(w-len(x)) for x in l]

@memoizef
def combinations(n, r):
    if r > n:
        return 0
    return int(math.factorial(n) / (math.factorial(n - r) * math.factorial(r)))

def windows(l, w):
    i = 0
    ll = len(l)
    r = []
    if w > 0:
        while i < ll - w + 1:
            r += [l[i:i+w]]
            i += 1
    else:
        w = -w
        while i < ll - w:
            r += [l[i:i+w]]
            i += w
        if i < ll:
            r += [l[i:]]
    return r

# Please remember: x is the right argument and y is the left one.

primitives = {'+': lambda x, y=0: y + x,
              '+,': lambda x, y=[]: y + [x], 
              '+:': lambda x, y=False: +(x or y), 
              '-': lambda x, y=None: x-y if y is not None else -x,
              '*': lambda x, y=None: x * y if y is not None else (x>0)-(x<0),
              '*:': lambda x, y=False: +(x and y), 
              '*,': lambda x, y=2: x ** y, 
              '%': lambda x, y=1: y/x,
              ';': lambda x, y=None: y+x if y is not None else [z for y in x for z in y],
              ';,': lambda x, y=None: [y, x] if y is not None else list(flatten(x)),
              '|': lambda x, y=None: x%y if y is not None else x if x>0 else -x,
              '<': lambda x, y=0: x>y,
              '>': lambda x, y=0: x<y,
              '<:': lambda x, y=0: x>=y, 
              '>:': lambda x, y=0: x<=y, 
              '<,': lambda x, y=None: x if y is None else x if x<y else y,
              '>,': lambda x, y=None: x if y is None else x if x>y else y,
              '=': lambda x, y=0: +(x==y),
              '=,': lambda x, y=None: [+(y==x[i:i+len(y)]) for i in range(len(x)-len(y))]+[0]*len(y),
              '=:': lambda x, y=0: +(x==y),
              ']': lambda x, y=1: nest(x, y), 
              '-,': lambda x, y=[0]: [z for z in x if z not in y], 
              '-:': lambda x, y=None: unique(x) if y is None else [z for z in x if z in y], 
              '?': lambda x, y=None: table([random.random() for _ in range(foldr(lambda x, y: x*y, x))], x)
                                     if y is None
                                     else table([random.uniform(0, y) for _ in range(foldr(lambda x, y: x*y, x))], x), 
              '!': lambda x, y=None: math.factorial(x)
                                     if y is None
                                     else combinations(x, y), 
              '#': lambda x, y=None: ([z for i, z in zip(y, x) for _ in range(i)]
                                      if len(y) > 1
                                      else [z for z in x for _ in range(y)])
                                     if y is not None
                                     else [i for i, z in enumerate(x) if z],
              }
primitives['+'].rank = (0, 0, 0)
primitives['+,'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives['+:'].rank = (0, 0, 0)
primitives['+,'].pad = (0, 1, 0)
primitives['-'].rank = (0, 0, 0)
primitives['*'].rank = (0, 0, 0)
primitives['*,'].rank = (0, 0, 0)
primitives['*:'].rank = (0, 0, 0)
primitives['%'].rank = (0, 0, 0)
primitives[';'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives[';'].pad = (2, 1, 1)
primitives[';,'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives[';,'].pad = (1, 0, 0)
primitives['|'].rank = (0, 0, 0)
primitives['<'].rank = (0, 0, 0)
primitives['>'].rank = (0, 0, 0)
primitives['<:'].rank = (0, 0, 0)
primitives['>:'].rank = (0, 0, 0)
primitives['<,'].rank = (0, 0, 0)
primitives['>,'].rank = (0, 0, 0)
primitives['='].rank = (0, 0, 0)
primitives['=,'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives['=,'].rank = (1, 1, 1)
primitives['=:'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives[']'].rank = (MAXRANK, 0, MAXRANK)
primitives['-,'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives['-,'].pad = (1, 1, 1)
primitives['-:'].rank = (MAXRANK, MAXRANK, MAXRANK)
primitives['-:'].pad = (1, 1, 1)
primitives['?'].rank = (1, 0, 1)
primitives['?'].pad = (1, 0, 1)
primitives['!'].rank = (0, 0, 0)
primitives['#'].rank = (MAXRANK, 1, MAXRANK)
primitives['#'].pad = (1, 1, 1)

adverbs = {'/': lambda f: rank(lambda x, y=None: \
                                   foldr(lambda x, y: call(f, y, x), x) \
                                   if y is None \
                                   else call(f, y, x),
                               (MAXRANK, MAXRANK, -1), (1, 0, 0)),
           '~': lambda f: lambda x, y=None: call(f, x, x) if y is None else call(f, x, y),
           'M': lambda f: rank(lambda x, y=None: call(f, x) if y is None else call(f, y, x),
                               (-1, -1, -1)),
           '\\': lambda f: rank(lambda x, y=None: [call(f, x[:i]) for i in range(1, len(x)+1)]
                                                  if y is None
                                                  else [call(f, i) for i in windows(x, y)],
                                (MAXRANK, 0, MAXRANK), (1, 0, 1)), 
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
                '/,': lambda f, s: rank(lambda x, y=None:
                                            foldr(lambda x, y: call(f, y, x), x, s)
                                            if y is None
                                            else call(f, y, x),
                                        (MAXRANK, MAXRANK, -1), (1, 0, 1)),
                '@': lambda f, g: rank(lambda x, y=None: call(g, call(f, x) if y is None else call(f, y, x)),
                                       (MAXRANK, MAXRANK, MAXRANK))
                                  if not isinstance(g, list)
                                  else rank(lambda x, y=None: agenda(f, g, x, y), rankof(f)),
                '@,': lambda f, g: rank(lambda x, y=None: call(g, call(f, x) if y is None else call(f, y, x)),
                                        rankof(f)),
                '`': lambda f, g: g+[f] if isinstance(g, list) else [g, f],
                '$': lambda f, g: lambda x, y=None: call(g, y, call(f, y, x))
                                                    if y is not None
                                                    else call(g, x, call(f, x)), 
                '$,': lambda f, g: lambda x, y=None: call(g, call(f, y, x), y)
                                                     if y is not None
                                                     else call(g, call(f, x), x), 
                '$:': lambda f, g: lambda x, y=None: call(g, x, call(f, y, x))
                                                     if y is not None
                                                     else call(g, x, call(f, x)),
                }

def partition(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def table(l, dimensions):
    d = functools.reduce(lambda x, y: x*y, dimensions)
    if d == 0:
        return []
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

functions = {'A': lambda x, y=None: x,
             'B': lambda x, y=None: y if y is not None else x,
             'Ba': rank(lambda x, y=[2]: int2base(x, y),
                        (0, 1, 0), (0, 1, 0)), 
             'Bn': rank(lambda x, y=[2]: base2int(x, y),
                        (1, 1, 1), (1, 1, 1)), 
             'C': rank(lambda x, y=1: sum(1 for z in x if z == y),
                       (MAXRANK, -1, MAXRANK), (1, 0, 1)), 
             'Ch': rank(lambda x, y=None: chr(x),
                        (0, MAXRANK, 0)), 
             'Co': rank(lambda x, y=None: ord(x),
                        (0, MAXRANK, 0)), 
             'D': lambda x, y=None: +depth(x),
             'E': rank(lambda x, y=None: (x[-1] if y is None else x[-y:]) if x else x, (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'F': rank(lambda x, y=None: float(x), (1, MAXRANK, 1)),
             'H': rank(lambda x, y=None: x[0] if y is None else x[:y], (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'I': rank(lambda x, y=10: int(''.join(x), y) if isinstance(x, list) else int(x), (0, 0, 1)),
             'Ir': rank(lambda x, y=None: int(x) if x - int(x) < 0.5 else int(x+0.5),
                        (0, MAXRANK, 0)), 
             'J': rank(lambda x, y=['']: join(x, y), (MAXRANK, 1, MAXRANK), (2, 1, 2)), 
             'Ld': rank(lambda x, y=1: x[y:] if len(x) else x, (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'Lr': rank(lambda x, y=1: x[:-y] if len(x) else x, (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'Lt': rank(lambda x, y=None: [[x]], (MAXRANK, MAXRANK, MAXRANK)),
             'N': rank(lambda x, y=None: len(x) if y is None else
                                         x[y] if isinstance(y, int) else x[int(len(x)*y)],
                       (MAXRANK, 0, MAXRANK), (1, 0, 1)),
             'O': rank(lambda x, y=None: [x[i] for i,_ in sorted(enumerate(y), key=lambda x:x[1])]
                                         if y is not None
                                         else sorted(x),
                       (MAXRANK, MAXRANK, MAXRANK), (1, 1, 1)), 
             'P': rank(lambda x, y=0: list(map(list, itertools.zip_longest(*x, fillvalue=y))),
                       (MAXRANK, MAXRANK, MAXRANK), (2, 0, 2)), 
             'Pr': rank(lambda x, y=None: (print(''.join(y).format(*map(str, x))) if y is not None else print(x)) or 0,
                       (MAXRANK, 1, MAXRANK), (1, 1, 1)), 
             'Ps': rank(lambda x, y=None: padarray(x)
                                          if y is None
                                          else [0]*(y-len(x))+x,
                        (MAXRANK, 0, MAXRANK), (2, 0, 1)), 
             'Pe': rank(lambda x, y=None: padarray(x, 1)
                                          if y is None
                                          else x+[0]*(y-len(x)),
                        (MAXRANK, 0, MAXRANK), (2, 0, 1)), 
             'R': rank(lambda x, y=None: list(range(y, x+(x>y or -1), x>y or -1)) \
                                         if y is not None \
                                         else list(range(0, x, x>0 or -1)),
                       (0, 0, 0)),
             'S': rank(lambda x, y=None: list(map(str, x)) if y is None else split(x, y), (1, MAXRANK, MAXRANK), (1, 1, 1)),
             'Sf': rank(lambda x, y=None: list(''.join(y).format(*x)),
                        (MAXRANK, 1, MAXRANK), (1, 1, 1)), # NOT DOCUMENTED
             'T': rank(lambda x, y=None: (table(list(range(functools.reduce(lambda x, y: x*y, x))), x)
                                          if x != [0] else [])
                                         if y is None
                                         else table(x, y),
                       (1, 1, 1), (1, 1, 1)),
             'V': rank(lambda x, y=None: x[::-1],
                       (MAXRANK, MAXRANK, MAXRANK), (1, 0, 1)), 
             'Z': [] 
             }


synonyms = {'Oh': 'O$,MH',
            'Oe': 'O$,ME',
            }

def call(f, x, y=None, xdepth=0, ydepth=0):
    x, y, f = resolve(x), resolve(y), resolve(f)
#    print(f) # In case of "str is not callable"
    rank, lrank, rrank = rankof(f)
    if y is None:
        dx = depth(x)
        if 0 > rank < xdepth or dx > rank >= 0:
            return [call(f, z, None, xdepth-1) for z in x]
#        if not hasattr(f, '__call__'):
#            return f
        pad = padrank(f)[0]
        if dx < pad:
            for _ in range(pad - dx):
                x = [x]
        return f(x)
    dx, dy = depth(x), depth(y)
    xr = isinstance(x, list) and (0 > lrank < xdepth or dx > lrank >= 0)
    yr = isinstance(y, list) and (0 > rrank < ydepth or dy > rrank >= 0)
    if xr and yr and len(x) == len(y):
        return [call(f, a, b, xdepth-1, ydepth-1) for a, b in zip(x, y)]
    if xr:
        return [call(f, z, y, xdepth-1, ydepth) for z in x]
    elif yr:
        return [call(f, x, z, xdepth, ydepth-1) for z in y]
    pad = padrank(f)
    if dx < pad[1]:
        for _ in range(pad[1] - dx):
            x = [x]
    if dy < pad[2]:
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
        if len(children) == 1:
            return children[0]
        if sum(1 for c in children if isinstance(c, tuple) or hasattr(c, '__call__'))>1:
            conjs = [x.value for x in node if x.value in conjunctions]
            children = [c for c in children if c not in conjunctions]
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
        return withConjunction(children[1], children[2], children[0])

    visit_conjlvl1 = visit_conjlvl2 = visit_conjlvl3 = visit_conjunction

    def visit_function(self, node, children):
        return children[0]

    def visit_primitive(self, node, children):
        return primitives[node.value]

    def visit_namedfunc(self, node, children):
        return ('variable', node.value) if node.value not in synonyms else parse(synonyms[node.value])

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
        return list(v[1:-1]) if v[0] == '"' else v[1:]

    def visit_space(self, node, children):
        return None

    def visit_NL(self, node, children):
        return None

    def visit_variable(self, node, children):
        return ('variable', node.value)

    def visit_assignment(self, node, children):
        functions[node[0].value if node[0].value != ':' else 'F'] = resolve(children[-1])
        return children[-1]

    def visit_combination(self, node, children):
        @usermemoize
        def f(x, y=None):
            for f in reversed(children):
                x = call(f, x) if y is None else call(f, y, x)
            return x
        return f

    def visit_tacit(self, node, children):
        def f(x, y=None):
            fs = children[::-1]
            fy = fs[0]
            if len(fs) == 2:
                vy = call(fy, x)
                return call(fs[1], x, vy) if y is None else call(fs[1], y, vy)
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
        if len(children) > 1:
            return f
        return children[0]

    def visit_lambda(self, node, children):
        return ('lambda', children[0])

    def visit_bind(self, node, children):
        return bind(children[1], children[0])

# TODO: Each column should have dffferent width
def printtable(v, w=0):
    dv = depth(v)
    if dv == 0:
        print(v)
    elif dv == 1:
        ls = False
        vl = len(v)
        if w == 0:
            w = [1]*len(v)
        for i, x in enumerate(v):
            s = isinstance(x, str)
            print((' '*(ls and not s))+(('{:'+str(w[i])+'}' if w else '{0}').format(x)), end=' '*(i<vl-1 and not s))
            ls = s
        print()
    elif dv > 1:
        vl = len(v)
        if dv == 2:
            mw = max(map(len, v))
            w = [max(len(str(0 if len(x) <= i else 1 if x[i] == 1 or x[i] == 0 else x[i])) for x in v) for i in range(0, mw)]
        for i, x in enumerate(v):
            printtable(x, w)
            if i < vl-1:
                print('\n'*(dv-2), end='')

parser = ParserPEG(grammar, "program", skipws=False)

def parse(code):
    tree = parser.parse(code+'\n')
    return visit_parse_tree(tree, InterpreterVisitor())[-1]

class REPL(cmd.Cmd):
    prompt = '   '
    intro = "Joe REPL - Version " + version + "\nType exit to quit."
    def parseline(self, line):
        return line

    def onecmd(self, code):
        if code == 'exit':
            return True
        if code.strip() != '':
            try:
                v = parse(code)
                if v is not None and not hasattr(v, '__call__'):
                    if tablemode:
                        printtable(adjust(v))
                    else:
                        try:
                            if len(v) == 0:
                                print('[]')
                            else:
                                print(''.join(v))
                        except:
                            print(v)
            except Exception as e:
                print("Error\n", e)

if __name__ == '__main__':
    tablemode = '-t' in sys.argv
    if '-nm' in sys.argv:
        memoize = memoizef = usermemoize = lambda f: f
    else:
        if '-mf' not in sys.argv:
            usermemoize = lambda f: f
        if '-nmc' in sys.argv:
            memoize = lambda f: f
        if '-nms' in sys.argv:
            memoizef = lambda f: f
    if '-h' in sys.argv or '--help' in sys.argv or len(sys.argv) == 1:
        print("Joe Interpreter - Version " + version)
        print("Uses python 3 and arpeggio module. Install with pip install arpeggio.")
        print()
        print("  python joe.py [options] (-c code | file)")
        print("    -h     show this help")
        print("    -mf    memoize user-defined functions (prevents changing output)")
        print("    -nm    prevents all memoization")
        print("    -nmc   prevents complex memoization")
        print("    -nms   prevents simple memoization")
        print("    -repl  starts REPL")
        print("    -t     prints lists as tables")
        print("    -test  run after making changes to the interpreter to check damages")
    elif '-test' in sys.argv:
        fails = []
        for c, r in tests:
            tree = parser.parse(c+'\n')
            v = visit_parse_tree(tree, InterpreterVisitor())[0]
            if v != r:
                fails += [(c, r, v)]
        if fails:
            print("Failed tests:")
            for c, r, v in fails:
                print("  Code:     " + c)
                print("  Expected: " + str(r))
                print("  Got:      " + str(v))
                print()
        else:
            print("Everything works.")
    elif '-repl' in sys.argv:
        REPL().cmdloop()
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


