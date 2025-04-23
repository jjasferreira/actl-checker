DEBUG = False

from lark import Lark, Token, Tree, Transformer
from ast_nodes import *

grammar = r"""
    ?start: expression
    ?expression: not_
               | or_
               | and_
               | implies
               | forall
               | exists
               | equal
               | relation

    ?not_: "(" "not" expression ")"
    ?or_: "(" "or" expression expression ")"
    ?and_: "(" "and" expression expression ")"
    ?implies: "(" "implies" expression expression ")"
    ?forall: "(" "forall" action_type interval any_variables any_variables expression ")"
    ?exists: "(" "exists" action_type interval any_variables any_variables expression ")"
    ?equal: "(" "equal" variable variable ")"
    ?relation: "(" relation_type interval interval ")"

    ?action_type: CNAME -> action_type
    ?relation_type: CNAME
    ?interval: CNAME -> interval
    ?variable: CNAME -> variable
    ?any_variables: "(" variable* ")"
    ?some_variables: "(" variable+ ")"

    %import common.CNAME
    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="start")

class Transformer(Transformer):
    
    def not_(self, items):
        return Not(items[0])

    def or_(self, items):
        return Or(items[0], items[1])

    def and_(self, items):
        return And(items[0], items[1])

    def implies(self, items):
        return Implies(items[0], items[1])

    def forall(self, items):
        return ForAll(Action(items[0], items[1], items[2], items[3]), items[1])

    def exists(self, items):
        return Exists(Action(items[0], items[1], items[2], items[3]), items[1])

    def equal(self, items):
        return Equal(items[0], items[1])
    
    def relation(self, items):
        if items[0] == "before":
            return Before(items[1], items[2])
        elif items[0] == "meets":
            return Meets(items[1], items[2])
        elif items[0] == "overlaps":
            return Overlaps(items[1], items[2])
        elif items[0] == "starts":
            return Starts(items[1], items[2])
        elif items[0] == "during":
            return During(items[1], items[2])
        elif items[0] == "finishes":
            return Finishes(items[1], items[2])
        elif items[0] == "equals":
            return Equals(items[1], items[2])
        else:
            raise ValueError(f"Unknown relation {items[0]}")

    def action_type(self, items):
        if ActionType.has_value(items[0]):
            return ActionType(items[0])
        else:
            raise ValueError(f"Unknown action type {items[0].capitalize()}")
    
    def relation_type(self, items):
        pass

    def interval(self, items):
        return Interval(items[0])

    def variable(self, items):
        return Var(items[0])

    def any_variables(self, items):
        return items

    def some_variables(self, items):
        return items

def print_tree(tree, indent = 0):
    """Recursively prints a Lark tree with indentation for readability."""
    if isinstance(tree, Token):
        print(4 * " " * indent + f"Token({tree.type}, '{tree.value}')")
    elif isinstance(tree, Tree):
        print(4* " " * indent + f"Tree(Token(RULE, {tree.data}))")
        for child in tree.children:
            print_tree(child, indent + 1)

def parse_ast(input : str) -> Formula:
    tree = parser.parse(input)
    if DEBUG:
        print_tree(tree)
        print("-"*30)
    ast = Transformer().transform(tree)
    if DEBUG:
        print(ast) #TODO: print_ast(ast)
        print("-"*30)
    return ast

if __name__ == "__main__":

    input1 = """
    (forall lookup i2 (k2) (v2)
        (exists store i1 (k1 v1) ()
            (and
                (before i1 i2)
                (and
                    (equal k1 k2)
                    (equal v1 v2)
                )
            )
        )
    )
    """

    DEBUG = True
    ast = parse_ast(input1)
