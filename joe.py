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
import re
from pprint import pprint

version = "0.2.0"
MAXRANK = 100
DEBUG = False

def debugprint(type, text):
    """Used to print debug-statements."""
    if DEBUG:
        print(type + ':', text)

tests = [("""{/+%N)1 2 3 4""", 2.5), # Median 
         ("""(/*-,1R)5""", 120), # Factorial
         ("""(2Lr0 1/,;$:/+@2ER)10""", [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]), # Fibonacci sequence
         ("""(VOeM;$C$,-:)"dsaasafd" """, [['a', 3], ['s', 2], ['d', 2], ['f', 1]]), # Counting occurences
         ("""M-,~/!R5""", [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]), # Pascal triangle
         ]

code = '~/*1R10'

whitespace = ' \t'
newline = '\n'
ignore = lambda words, l: [x for x in l if not any(x == w for w in words)]

def unescape(text): # Taken somewhere from Stack Overflow
    regex = re.compile(b'\\\\(\\\\|[0-7]{1,3}|x.[0-9a-f]?|[\'"abfnrt]|.|$)')
    def replace(m):
        b = m.group(1)
        if len(b) == 0:
            raise ValueError("Invalid character escape: '\\'.")
        i = b[0]
        if i == 120:
            v = int(b[1:], 16)
        elif 48 <= i <= 55:
            v = int(b, 8)
        elif i == 34: return b'"'
        elif i == 39: return b"'"
        elif i == 92: return b'\\'
        elif i == 97: return b'\a'
        elif i == 98: return b'\b'
        elif i == 102: return b'\f'
        elif i == 110: return b'\n'
        elif i == 114: return b'\r'
        elif i == 116: return b'\t'
        else:
            s = b.decode('ascii')
            raise UnicodeDecodeError(
                'stringescape', text, m.start(), m.end(), "Invalid escape: %r" % s
            )
        return bytes((v, ))
    return regex.sub(replace, text)

def memoize(f): 
    """Memoize any function.
       Be careful about the memory footprint."""
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
    """Memoize a function accepting only hashable arguments."""
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

# Resolve the depth of a list
depth = lambda x: isinstance(x, (list, tuple)) and (len(x) and depth(x[0])) + 1
# Fold from the right
foldr = lambda f, xs, s=None: (functools.reduce(f, reversed(xs[:-1] if s is None else xs), xs[-1] if s is None else s) if len(xs) else [])
# Flip the arguments of a function
flip  = lambda f: rank(lambda x, y=None: f(y, x), (f.rank[0], f.rank[2], f.rank[1]))
# Bind the left argument of a function.
bind  = lambda f, x: rank(lambda y, _=None: call(f, x, y), MAXRANK)
# Combine two functions into one.
#  combine(f, g)(1)    == f(g(1))
#  combine(f, g)(1, 2) == f(2, g(2, 1))
combine = lambda f, g: rank(lambda x, y=None: (call(f, call(g, x))
                                               if y is None
                                               else call(f, y, call(g, y, x))),
                            MAXRANK)
tacit = lambda f, g, h: rank(lambda x, y=None: (call(g, call(f, x), call(h, x))
                                                if y is None
                                                else call(g, call(f, y, x), call(h, y, x))),
                             MAXRANK)

def rank(f, r, p=(0, 0, 0)):
    """Set the rank of a function."""
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
    """Resolve the rank of a function."""
    f = resolve(f)
    if hasattr(f, 'rank'):
        return f.rank
    return (MAXRANK, MAXRANK, MAXRANK)
def applyN(f, n, x, y):
    """Apply a function n times."""
    for _ in range(n):
        x = call(f, x, y)
    return x
def padrank(f):
    """Resolves the padding rank of a function."""
    try:
        return f.pad
    except:
        return (0, 0, 0)
def resolve(x):
    """Resolves the value from a data-tuple."""
    if isinstance(x, tuple):
        if x[0] == 'function':
            if isinstance(x[1], str):
                x = functions[x[1]]
            else:
                x = x[1]
        elif x[0] in ('value', 'list'):
            x = x[1]
        elif x[0] == 'variable':
            x = variables[x[1]]
        else:
            raise Exception('Unexpected tuple ' + str(x) + ' - blame the developer')
    return x
def orderrank(f, m, l, r):
    """Reorders the rank of a function."""
    rank = rankof(f)
    return (rank[m], rank[l], rank[r])

def adjust(l):
    """Adjust every element of a list to have the same depth."""
    if not isinstance(l, list) or len(l) == 0:
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
    """Nests the list/value n times."""
    for _ in range(n):
        x = [x]
    return x

def split(l, splitter):
    """Split the list at the splitter. Splitter should be a list of values."""
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
    """Joins the items of l with j."""
    r = []
    for x in l:
        r += x
        r += j
    return r[:-len(j)]

def unique(l, idfun=None):
    """Select unique items from a list, optionally using a selector function."""
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
    """Convert an integer to a different base."""
    basel = len(base)
    if x == 0: return [0] * basel
    digits = []
    while x:
        digits.append(x % base[-1])
        x //= base[-1]
        if len(base) > 1:
            base = base[:-1]
    digits.reverse()
    return [0] * (basel - len(digits)) + digits

def base2int(l, base):
    """Convert from a different base to a base-10 integer."""
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
    """Pad a list to vbe rectangular (does not adjust the depth)."""
    l = [x if isinstance(x, list) else [x] for x in l]
    w = max(len(x) for x in l)
    if lr == 0:
        return [[padder]*(w-len(x))+x for x in l]
    else:
        return [x+[padder]*(w-len(x)) for x in l]

@memoizef
def combinations(n, r):
    """Calvulates the possible combinations to pick r items from a group of n items.
       Memoized for efficiency."""
    if r > n:
        return 0
    return int(math.factorial(n) / (math.factorial(n - r) * math.factorial(r)))

def windows(l, w):
    """Takes windows of width w from the given list.
       If the width is negative, the windows won't overlap. May cause the last window to be smaller."""
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

adverbs = {'/': # foldr
                lambda f: rank(lambda x, y=None: \
                                   foldr(lambda x, y: call(f, y, x), x) \
                                   if y is None \
                                   else call(f, y, x),
                               (MAXRANK, MAXRANK, -1), (1, 0, 0)),
           '~': # flip
                lambda f: lambda x, y=None: call(f, x, x) if y is None else call(f, x, y),
           'M': # map
                lambda f: rank(lambda x, y=None: call(f, x) if y is None else call(f, y, x),
                               (-1, -1, -1)),
           '\\': # apply to windows
                lambda f: rank(lambda x, y=None: [call(f, x[:i]) for i in range(1, len(x)+1)]
                                                 if y is None
                                                 else [call(f, i) for i in windows(x, y)],
                               (MAXRANK, 0, MAXRANK), (1, 0, 1)), 
           }

def agendaf(f, a):
    """Creates a conditive function (selects the function to run according to f)."""
    f = resolve(f)
    def F(x, y=None):
        v = a[call(f, x) if y is None else call(f, y, x)]
        if y is None:
            return call(v, x)
        return call(v, y, x)
    F.rank = rankof(f)
    debugprint("Agenda rank", F.rank)
    return F

conjunctions = {'^': lambda f, n: rank(lambda x, y=None: \
                                           call(f, x) \
                                           if y is None \
                                           else call(f, y, x),
                                       n),
                '/:': lambda f, s: rank(lambda x, y=None: # FIXDOC /, -> new name
                                            foldr(lambda x, y: call(f, y, x), x, s)
                                            if y is None
                                            else call(f, y, x),
                                        (MAXRANK, MAXRANK, -1), (1, 0, 1)),
                '@': lambda f, g: rank(lambda x, y=None: call(g, call(f, x) if y is None else call(f, y, x)),
                                       (MAXRANK, MAXRANK, MAXRANK))
                                  if not isinstance(resolve(g), list)
                                  else agendaf(f, g),
                '@,': lambda f, g: rank(lambda x, y=None: call(g, call(f, x) if y is None else call(f, y, x)),
                                        rankof(f)),
                '`': lambda f, g: g+[f] if isinstance(g, list) else [g, f],
                '$': lambda f, g: lambda x, y=None: call(g, y, call(f, y, x))
                                                    if y is not None
                                                    else call(g, x, call(f, x)), 
                '$r': lambda f, g: lambda x, y=None: call(g, call(f, y, x), y)
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

functions = {'+': lambda x, y=0: y + x,
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
             'A': lambda x, y=None: x,
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
             'R': rank(lambda x, y=None: list(range(int(y), int(x)+(x>y or -1), x>y or -1)) \
                                         if y is not None \
                                         else list(range(0, x, x>0 or -1)),
                       (0, 0, 0)),
             'S': rank(lambda x, y=None: list(str(x)) if y is None else split(x, y), (MAXRANK, MAXRANK, MAXRANK), (0, 1, 1)),
             'Sf': rank(lambda x, y=None: list(''.join(y).format(*x)),
                        (MAXRANK, 1, MAXRANK), (1, 1, 1)), # NOT DOCUMENTED
             'T': rank(lambda x, y=None: (table(list(range(functools.reduce(lambda x, y: x*y, x))), x)
                                          if x != [0] else [])
                                         if y is None
                                         else table(x, y),
                       (1, 1, 1), (1, 1, 1)),
             'V': rank(lambda x, y=None: x[::-1],
                       (MAXRANK, MAXRANK, MAXRANK), (1, 0, 1))
             }
functions['+'].rank = (0, 0, 0)
functions['+,'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions['+:'].rank = (0, 0, 0)
functions['+,'].pad = (0, 1, 0)
functions['-'].rank = (0, 0, 0)
functions['*'].rank = (0, 0, 0)
functions['*,'].rank = (0, 0, 0)
functions['*:'].rank = (0, 0, 0)
functions['%'].rank = (0, 0, 0)
functions[';'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions[';'].pad = (2, 1, 1)
functions[';,'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions[';,'].pad = (1, 0, 0)
functions['|'].rank = (0, 0, 0)
functions['<'].rank = (0, 0, 0)
functions['>'].rank = (0, 0, 0)
functions['<:'].rank = (0, 0, 0)
functions['>:'].rank = (0, 0, 0)
functions['<,'].rank = (0, 0, 0)
functions['>,'].rank = (0, 0, 0)
functions['='].rank = (0, 0, 0)
functions['=,'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions['=,'].rank = (1, 1, 1)
functions['=:'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions[']'].rank = (MAXRANK, 0, MAXRANK)
functions['-,'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions['-,'].pad = (1, 1, 1)
functions['-:'].rank = (MAXRANK, MAXRANK, MAXRANK)
functions['-:'].pad = (1, 1, 1)
functions['?'].rank = (1, 0, 1)
functions['?'].pad = (1, 0, 1)
functions['!'].rank = (0, 0, 0)
functions['#'].rank = (MAXRANK, 1, MAXRANK)
functions['#'].pad = (1, 1, 1)

synonyms = {'Oh': 'O$,MH',
            'Oe': 'O$,ME',
            }

variables = {'Z': []
            }

def call(f, x, y=None, xdepth=0, ydepth=0):
    x, y, f = resolve(x), resolve(y), resolve(f)
    debugprint("Call:", (f, x, y))
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

nameEndAlphabet = 'abcdefghijklmnopqrstuvwyxz'
nameStartAlphabet = 'ABCDEFGHIJKLMNOPQRSTUVWYXZ^!#%=?+*<>;|]-`/$@`~m\\'
startAlphabet = nameStartAlphabet
typeSynonyms = {'value': ('list', 'variable'),
                'name': ('function', 'variable')}

class Interpreter:
    def __init__(self):
        self.stack = []
        self.overhead = (None, None)
        self.code = ""

    def peekName(self):
        c = self.code[-1]
        if c in startAlphabet:
            return c
        if c in nameEndAlphabet:
            count = 1
            while self.code[-count-1] not in startAlphabet:
                count += 1
                c += self.code[-count]
            c += self.code[-count-1]
            return c[::-1]
        return False

    def readName(self):
        n = self.peekName()
        if n is not False:
            self.code = self.code[:-len(n)]
        return n

    def peekLiteral(self):
        c = self.code[-1]
        if len(self.code) > 1 and self.code[-2] == "'":
            return ('single', c)
        elif c == '"':
            count = 2
            s = ""
            while True:
                c = self.code[-count]
                if c == '"':
                    i = 1
                    t = False
                    while len(self.code) > count + i and self.code[-count-i] == '\\':
                        t = not t
                        i += 1
                    if not t:
                        break
                s += c
                count += 1
            return ('string', unescape(s[::-1].encode()).decode())
        elif c in '1234567890.':
            count = 2
            s = c
            while len(self.code) >= count and self.code[-count] in '1234567890.':
                if self.code[-count] == '.' and '.' in s:
                    break
                s += self.code[-count]
                count += 1
            s = s[::-1]
            if len(self.code) >= count and self.code[-count] == '_':
                s = '-' + s
            return ('number', float(s) if '.' in s else int(s), len(s))
        return False

    def peek(self):
        if len(self.code):
            c = self.peekLiteral()
            if c:
                return c
            c = self.code[-1]
            if c in ' ({[)':
                return c
            elif c == ':':
                return ('assign', c)
            c = self.peekName()
            if c:
                if c in functions:
                    return ('function', c)
                elif c in conjunctions:
                    return ('conjunction', c)
                elif c in adverbs:
                    return ('adverb', c)
                elif c in variables:
                    return ('variable', c)
                return ('name', c)
        return False

    def read(self):
        x = self.peek()
        if x is not False:
            if isinstance(x, tuple):
                if x[0] == 'single':
                    self.code = self.code[:-2]
                elif x[0] == 'string':
                    x = ('string', list(x[1]))
                    self.code = self.code[:-len(x[1])-2]
                elif x[0] == 'number':
                    self.code = self.code[:-x[2]]
                else:
                    self.code = self.code[:-len(x[1])]
            else:
                self.code = self.code[:-len(x)]
        return x

    def peekNth(self, n):
        ocode = self.code
        for _ in range(n+1):
            r = self.read()
        self.code = ocode
        return r

    def parseLine(self, code):
        self.code = code
        self.stack = []
        while len(self.code):
            self.parseExpression()
        return self.stack[-1]

    def parseExpression(self, until=()):
        while self.readStep(until):
            p = self.peek()
            if len(self.stack):
                self.overhead = self.stack.pop()
            while True:
                debugprint('Stack', self.stack + ([self.overhead] if self.overhead[0] else []))
                if self.pattern(['name', 'assign', 'function']): # Function assignment
                    n = self.stack.pop()[1]
                    self.stack.pop()
                    f = self.stack[-1]
                    functions[n] = resolve(f)
                elif self.pattern(['value', 'conjunction', 'assign', 'function']): # Assignment with conjunction
                    v = resolve(self.stack.pop())
                    c = self.stack.pop()[-1]
                    a = self.stack.pop()
                    f = withConjunction(c, resolve(self.stack.pop()), v)
                    self.stack.append(('function', f))
                    self.stack.append(a)
                elif self.pattern(['adverb', 'assign', 'function']): # Assignment with an adverb
                    c = self.stack.pop()[-1]
                    a = self.stack.pop()
                    f = withAdverb(c, resolve(self.stack.pop()))
                    self.stack.append(('function', f))
                    self.stack.append(a)
                elif self.pattern(['name', 'assign', 'value']): # Value assignment
                    n = self.stack.pop()[1]
                    self.stack.pop()
                    v = self.stack[-1]
                    variables[n] = resolve(v)
                elif self.pattern(['adverb', 'function']): # Adverb application
                    a = self.stack.pop()[1]
                    f = self.stack.pop()
                    self.stack.append(('function', withAdverb(a, f)))
                elif self.pattern(['function', 'conjunction', 'function'], ('value', 'adverb')):
                    f1 = resolve(self.stack.pop()) # 2-function conjunction application
                    c = self.stack.pop()[1]
                    f2 = resolve(self.stack.pop())
                    self.stack.append(('function', withConjunction(c, f2, f1)))
                elif self.pattern(['value', 'conjunction', 'function'], ('value',)):
                    v = resolve(self.stack.pop()) # value-function conjunction application
                    c = self.stack.pop()[1]
                    f = resolve(self.stack.pop())
                    self.stack.append(('function', withConjunction(c, f, v)))
                elif self.pattern(['value', 'list']): # prepend a value to a list (basically a cheat to build lists)
                    v = resolve(self.stack.pop())
                    l = self.stack.pop()[1]
                    self.stack.append(('list', [v] + l))
                elif self.pattern(['value', 'value']): # turn two values to a list
                    v1 = resolve(self.stack.pop())
                    v2 = resolve(self.stack.pop())
                    self.stack.append(('list', [v1, v2]))
                elif self.pattern(['value', 'function', 'value'], ('value',)): # Apply a function to two values
                    l = resolve(self.stack.pop())
                    f = self.stack.pop()
                    r = resolve(self.stack.pop())
                    self.stack.append(('value', call(f, l, r)))
                elif self.pattern(['function', 'value'], ('value', 'adverb')): # Apply a function to two values
                    f = self.stack.pop()
                    r = resolve(self.stack.pop())
                    self.stack.append(('value', call(f, r)))
                elif self.pattern(['value', 'function'], ('value',)): # Bind a funvtion with a value
                    v = resolve(self.stack.pop())
                    f = resolve(self.stack.pop())
                    self.stack.append(('function', bind(f, v)))
                elif self.pattern(['function', 'function'], ('value', 'adverb', 'conjunction')):
                    f1 = resolve(self.stack.pop()) # Combine two functions
                    f2 = resolve(self.stack.pop())
                    self.stack.append(('function', combine(f1, f2)))
                else:
                    if (not p or p in until) and self.overhead[0]:
                        self.stack.append(self.overhead)
                        self.overhead = (None, None)
                    else:
                        break
            if self.overhead[0]:
                if self.overhead[0] != 'close':
                    self.stack.append(self.overhead)
                self.overhead = (None, None)
        if self.stack[-1][0] == 'list':
            self.stack.append(('value', self.stack.pop()[1]))

    def parseTacit(self, until=()):
        while self.readStep(until):
            p = self.peek()
            if len(self.stack):
                self.overhead = self.stack.pop()
            while True:
                debugprint('Stack', self.stack + ([self.overhead] if self.overhead[0] else []))
                if self.pattern(['name', 'assign', 'function']): # Function assignment
                    n = self.stack.pop()[1]
                    self.stack.pop()
                    f = self.stack[-1]
                    functions[n] = resolve(f)
                elif self.pattern(['value', 'conjunction', 'assign', 'function']): # Assignment with conjunction
                    v = resolve(self.stack.pop())
                    c = self.stack.pop()[-1]
                    a = self.stack.pop()
                    f = withConjunction(c, resolve(self.stack.pop()), v)
                    self.stack.append(('function', f))
                    self.stack.append(a)
                elif self.pattern(['adverb', 'assign', 'function']): # Assignment with an adverb
                    c = self.stack.pop()[-1]
                    a = self.stack.pop()
                    f = withAdverb(c, resolve(self.stack.pop()))
                    self.stack.append(('function', f))
                    self.stack.append(a)
                elif self.pattern(['name', 'assign', 'value']): # Value assignment
                    n = self.stack.pop()[1]
                    self.stack.pop()
                    v = self.stack[-1]
                    variables[n] = resolve(v)
                elif self.pattern(['adverb', 'function']): # Adverb application
                    a = self.stack.pop()[1]
                    f = self.stack.pop()
                    self.stack.append(('function', withAdverb(a, f)))
                elif self.pattern(['function', 'conjunction', 'function'], ('value', 'adverb')):
                    f1 = resolve(self.stack.pop()) # 2-function conjunction application
                    c = self.stack.pop()[1]
                    f2 = resolve(self.stack.pop())
                    self.stack.append(('function', withConjunction(c, f2, f1)))
                elif self.pattern(['value', 'conjunction', 'function'], ('value',)):
                    v = resolve(self.stack.pop()) # value-function conjunction application
                    c = self.stack.pop()[1]
                    f = resolve(self.stack.pop())
                    self.stack.append(('function', withConjunction(c, f, v)))
                elif self.pattern(['value', 'list']): # prepend a value to a list (basically a cheat to build lists)
                    v = resolve(self.stack.pop())
                    l = self.stack.pop()[1]
                    self.stack.append(('list', [v] + l))
                elif self.pattern(['value', 'value']): # turn two values to a list
                    v1 = resolve(self.stack.pop())
                    v2 = resolve(self.stack.pop())
                    self.stack.append(('list', [v1, v2]))
                elif self.pattern(['value', 'function'], ('value',)): # Bind a funvtion with a value
                    v = resolve(self.stack.pop())
                    f = resolve(self.stack.pop())
                    self.stack.append(('function', bind(f, v)))
                elif self.pattern(['function', 'function', 'function'], ('value', 'adverb', 'conjunction')):
                    f1 = resolve(self.stack.pop())
                    f2 = resolve(self.stack.pop())
                    f3 = resolve(self.stack.pop())
                    self.stack.append(('function', tacit(f1, f2, f3)))
                elif self.pattern(['function', 'function'], ('value', 'adverb', 'conjunction', 'function')):
                    f1 = resolve(self.stack.pop()) # Combine two functions
                    f2 = resolve(self.stack.pop())
                    self.stack.append(('function', combine(f1, f2)))
                else:
                    if (not p or p in until) and self.overhead[0]:
                        self.stack.append(self.overhead)
                        self.overhead = (None, None)
                    else:
                        break
            if self.overhead[0]:
                if self.overhead[0] != 'close':
                    self.stack.append(self.overhead)
                self.overhead = (None, None)
        if self.stack[-1][0] == 'list':
            self.stack.append(('value', self.stack.pop()[1]))

    def readStep(self, until):
        p = self.peek()
        while p == ' ':
            self.read()
            p = self.peek()
        if p in until:
            self.read()
            return False
        if p is False:
            return False
        if p == '(':
            self.read()
            self.stack.append(('close', '('))
        elif p == ')':
            t = self.findBraceType()
            self.read()
            if t == '(':
                stack = self.stack
                self.stack = []
                self.parseExpression(('(',))
                self.stack = stack + self.stack
            elif t == '{':
                stack = self.stack
                self.stack = []
                self.parseTacit(('{',))
                self.stack = stack + self.stack
        else:
            self.stack.append(self.parseOne())
        return True

    def parseOne(self):
        x = self.read()
        if isinstance(x, tuple):
            if x[0] in ('single', 'string', 'number'):
                return ('value', x[1])
        return x

    def pattern(self, pat, oh=None):
        if (oh
            and self.overhead[0]
            and (self.overhead[0] in oh
                 or any(x in typeSynonyms
                        and self.overhead[0] in typeSynonyms[x]
                        for x in oh))):
            return False
        if len(self.stack) < len(pat):
            return False
        for i, x in enumerate(pat, 1):
            if (x != 'any'
                and self.stack[-i][0] != x
                and not (x in typeSynonyms
                         and self.stack[-i][0] in typeSynonyms[x])):
                return False
        return True

    def findBraceType(self):
        ocode = self.code
        count = 0
        while True:
            p = self.read()
            if p == ')':
                count += 1
            elif isinstance(p, str) and p in '({[':
                count -= 1
            if count == 0:
                break
        self.code = ocode
        return p

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
            print((' '*(ls and not s))+(('{:'+str(w[i])+'}' if w else '{0}').format(str(x))), end=' '*(i<vl-1 and not s))
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

parser = Interpreter()

def parseLine(code):
    return parser.parseLine(code)

def runLine(code):
    res = parseLine(code)
    if res[0] == 'value':
        printtable(res[1])

class REPL(cmd.Cmd):
    prompt = '   '
    intro = "Joe REPL - Version " + version + "\nType exit to quit."
    def parseline(self, line):
        return line

    def onecmd(self, code):
        global DEBUG
        if code == 'exit':
            return True
        if len(code) > 4 and code[:5] == 'debug':
            if len(code) > 6 and code[6:8] == 'on':
                DEBUG = True
                print("Debug output on.")
            else:
                DEBUG = False
                print("debug output off.")
        elif code.strip() != '':
            try:
                v = runLine(code)
                if v is not None and not hasattr(v, '__call__'):
                    printtable(adjust(v))
            except Exception as e:
                print("Error\n", e)
                raise

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
    if '-debug' in sys.argv:
        DEBUG = True
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
        print("    -debug Enables debug output")
        print("    -test  run after making changes to the interpreter to check damages")
    elif '-test' in sys.argv:
        fails = []
        for c, r in tests:
            v = runLine(c)
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
            printtable(v[-1])


