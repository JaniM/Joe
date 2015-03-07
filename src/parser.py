from pprint import pprint
from arpeggio.cleanpeg import ParserPEG
from arpeggio import PTNodeVisitor, visit_parse_tree

grammar = """
    program    = NL? statement+
    statement  = expression+ NL?
    expression = space? (call / curry / parameter)
    call       = lambdacall / modifierC / F0call / F1call / F2call
    curry      = lambda / compose / F1 / F2curry / modifier / func
    braces     = lambda / '(' expression ')'
    lambda     = '(' variable expression ')'
    compose    = '@' (curry / braces)+ ')'

    parameter  = literal / variable / braces
    literal    = number / string / list

    F0call     = F0
    F1call     = F1 expression
    F2call     = F2f (curry / expression) expression
               / F2curry expression
               / F2 expression expression
    F2curry    = parameter (F2 / modifier)
    lambdacall = variable expression+ ';'
               / braces !space expression
               / lambda !space expression

    modifierC  = F1m call
    modifier   = F1m func
    variable   = 'x' / 'y' / 'z' / '$' r'.'
    func       = F1 / F2 / F2f
    F0         = 'I'
    F1         = 'p' / 'i' / 'f' / 's' / '~'
    F1m        = ':'
    F2         = '+' / '-' / '*' / '/' / 'Z' / 'J' / 'S'
    F2f        = 'M' / 'F'

    NL         = ('\r' / '\n')+
    space      = (' ' / '\t')+
    number     = r'\d*\.\d+|\d+'
    string     = r'".*?"' / r'\\'.'
    list       = '[' expression* ']'
"""

whitespace = ' \t'
newline = '\n'
node = lambda f: lambda self, node, children: f(node.value)
ignore = lambda words, l: [x for x in l if not any(x == w for w in words)]

class GrammarVisitor(PTNodeVisitor):
    def visit_program(self, node, children):
        return ignore(newline, children)

    def visit_statement(self, node, children):
        children = ignore(newline, children)
        return children[:-1] + [('call', ('func', 'p'), [children[-1]])]

    def visit_expression(self, node, children):
        return children[-1]

    def visit_lambda(self, node, children):
        return ('lambda', children[0], children[1])

    def visit_compose(self, node, children):
        return ('compose', children)

    def visit_F0call(self, node, children):
        return ('call', self.visit_F0(node, children), [])

    def visit_F1call(self, node, children):
        return ('call', children[0], children[1:])

    def visit_F2call(self, node, children):
        return ('call', children[0], children[1:])

    def visit_F2curry(self, node, children):
        return ('curry', children[1], children[0])

    def visit_lambdacall(self, node, children):
        return ('call', children[0], children[1:])

    def visit_modifierC(self, node, children):
        return ('call', ('call', children[0], children[1][1]), [children[1][2]])

    def visit_modifier(self, node, children):
        return ('call', children[0], [children[1]])

    def visit_func(self, node, children):
        return children[0]

    visit_F0 = visit_F1 = visit_F2 = visit_F1m = visit_F2f = node(lambda x: ('func', x))
    
    def visit_variable(self, node, children):
        return ('variable', children[0])

    def visit_literal(self, node, children):
        return ('literal', children[0])

    def visit_number(self, node, children):
        return float(node.value)

    def visit_string(self, node, children):
        return '"' + (node.value[1:-1] if node.value[0] == '"' else node.value[1]) + '"'

    def visit_list(self, node, children):
        return children

def parse(code):
    code = code.replace('\r', '\n')
    code = '\n'.join(line for line in code.split('\n') if len(line) > 1 and line[:2] != '--')
    parser = ParserPEG(grammar, "program", skipws=False)
    parser.eolterm = True
    try:
        tree = parser.parse(code)
    except Exception as e:
        raise e
    return visit_parse_tree(tree, GrammarVisitor())

if __name__ == '__main__':
    print 'If you want to print the parsed tree, run'
    print '    compiler.py -p (-c "code" | file)'

