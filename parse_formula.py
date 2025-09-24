DEBUG = False

import os
import sys
import argparse

from lark import Lark, Token, Tree, Transformer
from ast_nodes import *

grammar = r"""
    ?start: expression

    // Top-down precedence (lowest to highest)
    ?expression: implication

    ?implication: "(" "implies" expression expression ")"   -> implies
                | disjunction

    ?disjunction: "(" "or" expression expression+ ")"       -> or_
                | conjunction

    ?conjunction: "(" "and" expression expression+ ")"      -> and_
                | negation

    ?negation: "(" "not" expression ")"                     -> not_
             | quantifier

    ?quantifier: "(" "forall" action_type interval variables variables expression+ ")" -> forall
               | "(" "exists" action_type interval variables variables expression+ ")" -> exists
               | atom

    ?atom: equal
         | relation
         | "(" expression ")"
    ?equal: "(" variable "=" variable ")"
    ?relation: "(" relation_type interval interval ")"

    ?action_type: LABEL -> action_type
    ?relation_type: LABEL
    ?interval: LABEL -> interval
    ?variable: constant
             | LABEL -> variable
             | WILDCARD -> wildcard
    
    constant: "'" LABEL
    LABEL: (DIGIT | LETTER | "_")+
    WILDCARD: "-"

    ?variables: "(" variable* ")"

    %import common.DIGIT
    %import common.LETTER
    %import common.WS
    %ignore WS

    %import common.CPP_COMMENT -> COMMENT_LINE
    # Defined as: /\/\/[^\n]*/

    %import common.C_COMMENT -> COMMENT_BLOCK # Does not allow for nested block comments
    # Defined as: "/*" /(.|\n)*?/ "*/"

    %ignore COMMENT_LINE
    %ignore COMMENT_BLOCK
"""

formula_parser = Lark(grammar, start="start")

class ASTTransformer(Transformer):
    
    def not_(self, items):
        return Not(items[0])

    def or_(self, items):
        return Or(*items)

    def and_(self, items):
        return And(*items)

    def implies(self, items):
        return Implies(items[0], items[1])

    def _quantifier(self, items, quantifier_cls):
        action = Action(items[0], items[1], items[2], items[3])
        exprs = items[4:]
        body = exprs[0] if len(exprs) == 1 else And(*exprs)
        return quantifier_cls(action, body)

    def forall(self, items):
        return self._quantifier(items, ForAllAction)

    def exists(self, items):
        return self._quantifier(items, ExistsAction)

    def equal(self, items):
        return Equal(items[0], items[1])
    

    RELATION_MAP = {
        "before": Before,
        "meets": Meets,
        "overlaps": Overlaps,
        "starts": Starts,
        "during": During,
        "finishes": Finishes,
        "equals": Equals,
    }

    def relation(self, items):
        rel_type = items[0]
        a, b = items[1], items[2]
        
        if rel_type in self.RELATION_MAP:
            return self.RELATION_MAP[rel_type](a, b)
        elif rel_type == "in":
            return Or(Starts(a, b), During(a, b), Finishes(a, b))
        elif rel_type == "intersects":
            return Or(
                Equals(a, b),
                Or(Starts(a, b), During(a, b), Finishes(a, b)),
                Or(Starts(b, a), During(b, a), Finishes(b, a)),
                Overlaps(a, b),
                Overlaps(b, a),
            )
        else:
            raise ValueError(f"Unknown relation {rel_type}")

    def action_type(self, items):
        if ActionType.has_value(items[0].value.upper()):
            return ActionType(items[0].value.upper())
        else:
            raise ValueError(f"Unknown action type {items[0].value}")
    
    def relation_type(self, items):
        pass

    def interval(self, items):
        return Interval(items[0].value)

    def variable(self, items):
        return Variable(items[0].value)

    def constant(self, items):
        return Constant(items[0].value)

    def wildcard(self, items):
        return Wildcard()

    def variables(self, items):
        return items

def print_tree(tree, indent = 0):
    """Recursively prints a Lark tree with indentation for readability."""
    if isinstance(tree, Token):
        print(4 * " " * indent + f"Token({tree.type}, '{tree.value}')")
    elif isinstance(tree, Tree):
        print(4* " " * indent + f"Tree(Token(RULE, {tree.data}))")
        for child in tree.children:
            print_tree(child, indent + 1)

def parse_formula(formula: str) -> Formula:
    try:
        tree = formula_parser.parse(formula)
        if DEBUG:
            print("-"*50, "Tree:", sep="\n")
            print_tree(tree)
        ast = ASTTransformer().transform(tree)
    except Exception as e:
        print(f"Error parsing formula: {e}", file=sys.stderr)
        sys.exit(1)
    return ast

def handle_input(value: str) -> str:
    # If the value is a file path, return its content
    if os.path.isfile(value):
        try:
            with open(value, "r") as file:
                content = file.read()
        except OSError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        if not content:
            print("Error: Input file is empty.", file=sys.stderr)
            sys.exit(1)
        return content
    # If the value is a string, return it directly
    return value

def main():
    parser = argparse.ArgumentParser(description="Parse a formula from string or file")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("-f", "--formula", type=handle_input, help="Path to formula file or formula string")
    args = parser.parse_args()

    global DEBUG
    DEBUG = args.debug
    if args.formula is not None:
        formula = args.formula
    else:
    # If we do not have a formula, read from stdin
        print("Enter formula (Ctrl+D to end input):", file=sys.stderr)
        formula = sys.stdin.read().strip()
    if not formula:
        print("Error: No input provided.", file=sys.stderr)
        sys.exit(1)
    ast = parse_formula(formula)

    # Print the AST that was parsed from the formula
    print("-"*50, "Parsed formula:", ast, "-"*50, sep="\n")

if __name__ == "__main__":
    main()