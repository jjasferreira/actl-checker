DEBUG = False

from lark import Lark, Token, Tree, Transformer
from ast_nodes import *

grammar = r"""
    ?start: expression

    // Top-down precedence (lowest to highest)
    ?expression: implication

    ?implication: "(" "implies" expression expression ")"   -> implies
                | disjunction

    ?disjunction: "(" "or" expression expression+ ")"        -> or_
                | conjunction

    ?conjunction: "(" "and" expression expression+ ")"       -> and_
                | negation

    ?negation: "(" "not" expression ")"                     -> not_
             | quantifier

    ?quantifier: "(" "forall" action_type interval any_variables any_variables expression ")" -> forall
               | "(" "exists" action_type interval any_variables any_variables expression ")" -> exists
               | atom

    ?atom: equal
         | relation
         | "(" expression ")"
    ?equal: "(" variable "=" variable ")"
    ?relation: "(" relation_type interval interval ")"

    ?action_type: CNAME -> action_type
    ?relation_type: CNAME
    ?interval: CNAME -> interval
    ?variable: CNAME -> variable
            | CONST -> const
    ?any_variables: "(" variable* ")"
    ?some_variables: "(" variable+ ")"

    %import common.CNAME
    %import common.WS
    %ignore WS
    COMMENT_LINE: "//" /[^\n]*/

    COMMENT_BLOCK : /\/\*(.+?)\*\//s # Does not allow for nested block comments

    %ignore COMMENT_LINE
    %ignore COMMENT_BLOCK

    CONST: "'" CNAME
"""

parser = Lark(grammar, start="start")

class Transformer(Transformer):
    
    def not_(self, items):
        return Not(items[0])

    def or_(self, items):
        return Or(*items)

    def and_(self, items):
        return And(*items)

    def implies(self, items):
        return Implies(items[0], items[1])

    def forall(self, items):
        return ForAllAction(Action(items[0], items[1], items[2], items[3]), items[4])

    def exists(self, items):
        return ExistsAction(Action(items[0], items[1], items[2], items[3]), items[4])

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
        elif items[0] == "in":
            return Or(Starts(items[1], items[2]), During(items[1], items[2]), Finishes(items[1], items[2]))
        elif items[0] == "intersects":
            in_predicate_1 =  Or(Starts(items[1], items[2]), During(items[1], items[2]), Finishes(items[1], items[2]))
            in_predicate_2 =  Or(Starts(items[2], items[1]), During(items[2], items[1]), Finishes(items[2], items[1]))
            return Or(Equal(items[1],items[2]),
                      in_predicate_1,
                      in_predicate_2,
                      Overlaps(items[1], items[2]),
                      Overlaps(items[2],items[1]))
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

    def const(self, items : list[str]):
        return Constant(items[0].strip("\'"))

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
                    (k1 = k2)
                    (v1 = v2)
                )
            )
        )
    )
    """

    DEBUG = True
    ast = parse_ast(input1)
