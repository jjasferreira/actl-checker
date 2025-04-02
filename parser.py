from lark import Lark, Transformer
from ast_nodes import  *

grammar = r"""
    ?start: expr
    ?expr: action
         | equals
         | not_
         | and_
         | or_
         | implies
         | forall
         | exists
         | relation
         | "(" expr+ ")"
    ?action: "(" var var "(" var* ")" "(" var* "))"
    ?equals: "(" "equals" var var ")"
    ?not_: "(" "not" expr ")"
    ?and_: "(" "and" expr expr ")"
    ?or_: "(" "or" expr expr ")"
    ?implies: "(" "implies" expr expr ")"
    ?forall: "(" "forall" "(" var+ ")" expr ")"
    ?exists: "(" "exists" "(" var+ ")" expr ")"
    ?relation: "(" var var var ")"
    ?var: CNAME
    %import common.CNAME
    %import common.WS
    %ignore WS
"""

parser = Lark(grammar, start="start")

class Transformer(Transformer):
    def action(self, items):
        return Action(ActionType[items[0].capitalize()], items[1], items[2], items[3])

    def equals(self, items):
        return Equals(items[0], items[1])
    
    def not_(self, items):
        return Not(items[0])

    def and_(self, items):
        return And(items[0], items[1])

    def or_(self, items):
        return Or(items[0], items[1])
    
    def implies(self, items):
        return Implies(items[0], items[1])
    
    def forall(self, items):
        return ForAll(items[0], items[1])

    def exists(self, items):
        return Exists(items[0], items[1])
    
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

    def var(self, items):
        return items[0]



# Testing

input1 = """
(forall (i x y)
  (implies
    (lookup i (x) (y))
    (exists (j)
      (and
        (store j (x y) ())
        (before j i)
      )
    )
  )
)"""

print(Transformer().transform(parser.parse(input1)))