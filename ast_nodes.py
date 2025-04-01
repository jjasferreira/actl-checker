from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


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
    
class Event(ABC):
    @abstractmethod
    def __init__(self, action_type : ActionType, values):
        self.action_type = action_type
        self.values = values if isinstance(values, list) else [values]

class Begin(Event):
    def __init__(self, action_type : ActionType, values):
        super().__init__(action_type, values)

    def __repr__(self):
        return f"Begin({self.action_type}, {self.values})"

class End(Event):
    def __init__(self, action_type : ActionType, values):
        super().__init__(action_type, values)

    def __repr__(self):
        return f"End({self.action_type}, {self.values})"

class Trace:
    def __init__(self, trace : list[Event] = []):
        if trace:
            self.trace = trace
        else:
            self.trace = []

    def add(self, event : Event):
        self.trace.append(event)

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
        return f"{self.label}"

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
    def __init__(self, begin, end): 
        self.begin = begin
        self.end = end
    
    def evaluate(self, _): #type: ignore
        return self

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, IntervalValue)
            and self.begin == other.begin
            and self.end == other.end
        )

    def __repr__(self):
        return f"({self.begin}, {self.end})"

class Interval(Var):
    def __init__(self, label):
        self.label = label

    def evaluate(self, store) -> IntervalValue:
        if self.label not in store:
            raise ValueError(f"Interval {self.label} not found in store")
        return store[self.label]

    def __repr__(self):
        return f"{self.label}"



class UnaryExpr(Formula, ABC):
    @abstractmethod
    def __init__(self, expr):
        self.expr = expr

class Not(UnaryExpr):
    def __init__(self, expr):
        super().__init__(expr)

    def evaluate(self, store):
        return not self.expr.evaluate(store)

    def __repr__(self):
        return f"¬({self.expr})"



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
        return f"({self.left} ∧ {self.right})"

class Or(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any:
        return self.left.evaluate(store) or self.right.evaluate(store)

    def __repr__(self):
        return f"({self.left} v {self.right})"

class Implies(BinaryExpr):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any:
        return not self.left.evaluate(store) or self.right.evaluate(store)

    def __repr__(self):
        return f"({self.left} => {self.right})"



class Quantifier(Formula, ABC):
    @abstractmethod
    def __init__(self, var, expr):
        self.var = var if isinstance(var, list) else [var]
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
        var_str = ", ".join(map(str, self.var))
        return f"∃({var_str}). ({self.expr})"

class ForAll(Quantifier):
    def __init__(self, var, expr):
        super().__init__(var, expr)

    # TODO: evaluate
    def evaluate(self, _) -> Any: # type: ignore
        raise NotImplementedError

    def __repr__(self):
        var_str = ", ".join(map(str, self.var))
        return f"∀({var_str}). ({self.expr})"




class Action(Formula):
    def __init__(self, action_type: ActionType, interval, inputs, outputs):
        self.action_type = action_type
        self.interval = interval
        self.input = inputs if isinstance(inputs, list) else [inputs]
        self.output = outputs if isinstance(outputs, list) else [outputs]

    # TODO: evaluate, search the whole trace for a matching action
    def evaluate(self, _) -> Any: # type: ignore
        raise NotImplementedError

    def __repr__(self):
        type_str = self.action_type.name.lower()
        input_str = ", ".join(map(str, self.input))
        output_str = ", ".join(map(str, self.output))
        return f"{type_str}[{self.interval}] ({input_str}) -> ({output_str})"



class IntervalPredicate(Formula, ABC):
    @abstractmethod
    def __init__(self, left : Interval, right : Interval):
        self.left = left
        self.right = right

class Before(IntervalPredicate):
    def __init__(self, left : Interval, right : Interval):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.end < right.begin

    def __repr__(self):
        return f"Before({self.left}, {self.right})"

class Meets(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.end == right.begin

    def __repr__(self):
        return f"Meets({self.left}, {self.right})"

class Overlaps(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.begin < right.begin < left.end < right.end

    def __repr__(self):
        return f"Overlaps({self.left}, {self.right})"

class Starts(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.begin == right.begin and left.end < right.end

    def __repr__(self):
        return f"Starts({self.left}, {self.right})"

class During(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return right.begin < left.begin and left.end < right.end

    def __repr__(self):
        return f"During({self.left}, {self.right})"

class Finishes(IntervalPredicate):
    def __init__(self, left, right):
        super().__init__(left, right)

    def evaluate(self, store) -> Any: # type: ignore
        left = self.left.evaluate(store)
        right = self.right.evaluate(store)
        return left.end == right.end and right.begin < left.begin

    def __repr__(self):
        return f"Finishes({self.left}, {self.right})"

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
    action1 = Action(ActionType.Lookup, "i1", ["x1", "x2"], "y1")
    action2 = Action(ActionType.Store, "i2", "x3", "y2")

    expr1 = And(action1, action2)
    expr2 = Not(Or(action1, action2))

    test = """ 
action1 = Action(ActionType.Lookup, "i1", ["x1", "x2"], "y1")
action2 = Action(ActionType.Store, "i2", "x3", "y2")

expr1 = And(action1, action2)
expr2 = Not(Or(action1, action2))
"""

    print(test)
    print(expr1)
    print(expr2)


    expr3 = ForAll(["i1", "x", "y"],\
                    Implies( \
                        Action(ActionType.FindNode, "i1", "x", "y"),  \
                            Exists(["i2"],  \
                                And(Action(ActionType.Member, "i2", [], []), During(Interval("i1"), Interval("i2"))))))
    test3 = '''
ForAll(["i1", "x", "y"],
                Implies( \
                    Action(ActionType.FindNode, "i1", "x", "y"),
                        Exists("i2",
                            And(Action(ActionType.Member, "i2", [], []), During("i1", "i2")))))
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
        "i1": IntervalValue(1, 5),
        "i2": IntervalValue(0, 10),
        "i3": IntervalValue(6, 15),
    }

    exprs = [And(Var("x"), Var("y")),
        Or(Var("x"), Var("y")) ,
        Not(Var("x")) ,
        Implies(Var("x"), Var("y")) ,
        Implies(Var("y"), Var("x")) ,

        Equal(Var("x"), Var("x")),
        Equal(Var("x"), Var("y")) ,

        During(Interval("i1"), Interval("i2")),
        Before(Interval("i1"), Interval("i3")) ,
        Meets(Interval("i1"), Interval("i3")) 
    ]


    print(f"{store = }")
    for expr in exprs:
        print(expr)
        print(expr.evaluate(store))