## Optimizer

depth = lambda x: isinstance(x, (list, tuple)) and depth(x[0]) + 1

def isArithmetic(tree):
    return tree[0] == 'func' and tree[1] in '+-*/%'

def optimizeNth(n):
    def f(tree):
        r = list(tree)
        if isinstance(r[n], list):
            r[n] = optimizeList(r[n])
        else:
            r[n] = optimizeExpression(r[n])
        return r
    return f

def updateNth(t, n, f):
    r = list(t)
    r[n] = f(r[n])
    return tuple(r)

def optimizeCall(tree):
    if tree[1][0] == 'curry':
        ret = list(tree)
        ret[1] = tree[1][1]
        ret[2] = [optimizeExpression(tree[1][2])] + optimizeList(ret[2])
        return optimizeCall(tuple(ret))
    return ('call', optimizeExpression(tree[1]), optimizeList(tree[2]))

def optimize(tree):
    return [optimizeList(x) for x in tree]

def optimizeList(tree):
    return [optimizeExpression(x) for x in tree]

optimizeExpressions = { 'call': optimizeCall
                      , 'lambda': optimizeNth(2)
                      , 'curry': optimizeNth(2)
                      , 'arithmetic': optimizeNth(2) }

def optimizeExpression(tree):
    if tree[0] in optimizeExpressions:
        return optimizeExpressions[tree[0]](tree)
    return tree

