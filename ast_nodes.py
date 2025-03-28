from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

# TODO: Events
#
# class Event(ABC):
#     pass
#
# class Begin(Event):
#
# class End(Event):

class Trace:
    def __init__(self, trace = None):
        if trace:
            self.trace = trace
        else:
            self.trace = []

    def add(self, expr):
        self.trace.append(expr)

    def __repr__(self):
        return f"Trace({self.trace})"



class Formula(ABC):
    @abstractmethod
    def evaluate(self, store) -> Any:
        pass


class Var(Formula):
    def __init__(self, label):
        self.label = label

    def evaluate(self, store):
        if self.label not in store:
            raise ValueError(f"Variable {self.label} not found in store")
        return store[self.label]

    def __repr__(self):
        return f"VarLabel:{self.label}"

# class VarValue(Formula):
#     def __init__(self, label, value):
#         self.label = label
#         self.value = value
#
#     def evaluate(self, store):
#         return store[self.label]
#
#     def __repr__(self):
#         return f"Var:{self.label}"


class IntervalValue(Formula):
    #TODO: explicit types in init, int or datetime
    def __init__(self, start, end): 
        self.start = start
        self.end = end
    
    def evaluate(self, _): #type: ignore
        return self

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, IntervalValue)
            and self.start == other.start
            and self.end == other.end
        )


    def __repr__(self):
        return f"Interval[{self.start}, {self.end}]"



class Interval(Var):
    def __init__(self, label):
        self.label = label

    def evaluate(self, store) -> IntervalValue:
        return store[self.label]

    def __repr__(self):
        return f"Var:{self.label}"


class Not(Formula):
    def __init__(self, expr):
        self.expr = expr

    def evaluate(self, store):
        return not self.expr.evaluate(store)

    def __repr__(self):
        return f"~({self.expr})"

class BinaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Equal(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any:
        return self.left.evaluate(store) == self.right.evaluate(store)

    def __repr__(self):
        return f"({self.left} == {self.right})"

class And(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    
    def evaluate(self, store) -> Any:
        return self.left.evaluate(store) and self.right.evaluate(store)

    def __repr__(self):
        return f"({self.left} && {self.right})"

class Or(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any:
        return self.left.evaluate(store) or self.right.evaluate(store)

    def __repr__(self):
        return f"({self.left} || {self.right})"


class Implies(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any:
        return not self.left.evaluate(store) or self.right.evaluate(store)

    def __repr__(self):
        return f"({self.left} => {self.right})"


class Quantifier(Formula, ABC):
    def __init__(self, var : list, expr):
        self.var = var # list of vars instead?
        self.expr = expr



class Exists(Quantifier):
    def __init__(self, var, expr):
        super().__init__(var, expr)
    
    # TODO: evaluate
    def evaluate(self, _) -> Any: # type: ignore
        raise NotImplementedError

    # def evaluate(self, store): 
    #     for value in valores possiveis do traço, distinguir entre intervalos e restantes variaveis
    #         new_store = store.copy()
    #         new_store[self.var] = value  
    #         if self.expr.evaluate(new_store):
    #             return True
    #     return False

    def __repr__(self):
        return f"E{self.var}. ({self.expr})"

class ForAll(Quantifier):
    def __init__(self, var, expr):
        super().__init__(var, expr)

    # TODO: evaluate
    def evaluate(self, _) -> Any: # type: ignore
        raise NotImplementedError

    def __repr__(self):
        return f"V{self.var}. ({self.expr})"



class ActionType(Enum):
    Lookup = 1
    Store = 2
    FindNode = 3
    Join = 4
    Leave = 5
    Fail = 6
    Ideal = 7
    Stable = 8
    ReadOnly = 9
    Member = 10
    Responsible = 11

class Action(Formula):
    def __init__(self, action_type: ActionType, inputs, interval, outputs):
        self.action_type = action_type
        self.input = inputs if isinstance(inputs, list) else [inputs]
        self.interval = interval
        self.output = outputs if isinstance(outputs, list) else [outputs]


    # TODO: evaluate, search the whole trace for a matching action
    def evaluate(self, _) -> Any: # type: ignore
        raise NotImplementedError

    def __repr__(self):
        inputs_str = ", ".join(map(str, self.input))
        return f"{self.action_type}({inputs_str}) [{self.interval}] -> ({self.output})"


class IntervalPredicate(Formula, ABC):
    @abstractmethod
    def __init__(self, left : Interval, right : Interval):
        self.left = left
        self.right = right

class During(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)

        return right.start < left.start and left.end < right.end

    def __repr__(self):
        return f"During({self.left}, {self.right})"

class Starts(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.start == right.start and left.end < right.end

    def __repr__(self):
        return f"Starts({self.left}, {self.right})"


class Finishes(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.end == right.end and right.start < left.start

    def __repr__(self):
        return f"Finishes({self.left}, {self.right})"

class Before(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.end < right.start # Ignores gap in ATL definition

    def __repr__(self):
        return f"Before({self.left}, {self.right})"

class Overlap(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.start < right.start < left.end < right.end

    def __repr__(self):
        return f"Overlap({self.left}, {self.right})"

class Meets(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.end < right.start # Ignores gap in ATL definition

    def __repr__(self):
        return f"Meets({self.left}, {self.right})"

class Equals(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left == right

    def __repr__(self):
        return f"Equals({self.left}, {self.right})"

if __name__ == "__main__":
    action1 = Action(ActionType.Lookup, ["x1", "x2"], "[0, 5]", "y1")
    action2 = Action(ActionType.Store, "x3", "[5, 10]", "y2")

    expr1 = And(action1, action2)
    expr2 = Not(Or(action1, action2))

    test = """ 
action1 = Action(ActionType.Lookup, ["x1", "x2"], "[0, 5]", "y1")
action2 = Action(ActionType.Store, "x3", "[5, 10]", "y2")

expr1 = And(action1, action2)
expr2 = Not(Or(action1, action2))
"""

    print(test)
    print(expr1)
    print(expr2)


    expr3 = ForAll(["x", "y", "z1"],\
                    Implies( \
                        Action(ActionType.FindNode, "x", "z1", "y"),  \
                            Exists(["z2"],  \
                                And(Action(ActionType.Member, [], "z2", []), During(Interval("z1"), Interval("z2"))))))
    test3 = '''
ForAll(["x", "y", "z1", 
                Implies( 
                    Action(ActionType.FindNode, "x", "z1", "y"),  
                        Exists("z2",  
                            And(Action(ActionType.Member, [] "z2", []), During("z1", "z2")))))
'''
    print("-"*10)
    print(test3)
    print(expr3)



    print("\n" + "-"*10)
    print("Eval")
    print("-"*10 + "\n")

    store = {"x" : 10, "y" : 20}
    print(f"{store = }")
    expr = Var("x")

    print(expr)
    print(expr.evaluate(store))

    expr = Var("y")

    print(expr)
    print(expr.evaluate(store))

    store = {
        "x": True,
        "y": False,
        "z1": IntervalValue(1, 5),
        "z2": IntervalValue(0, 10),
        "z3": IntervalValue(6, 15),
    }

    exprs = [And(Var("x"), Var("y")),
        Or(Var("x"), Var("y")) ,
        Not(Var("x")) ,
        Implies(Var("x"), Var("y")) ,
        Implies(Var("y"), Var("x")) ,

        Equal(Var("x"), Var("x")),
        Equal(Var("x"), Var("y")) ,

        During(Interval("z1"), Interval("z2")),
        Before(Interval("z1"), Interval("z3")) ,
        Meets(Interval("z1"), Interval("z3")) 
    ]


    print(f"{store = }")
    for expr in exprs:
        print(expr)
        print(expr.evaluate(store))


