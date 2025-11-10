from ast_nodes import *

def print_action_creation():
    action1 = Action(ActionType.Lookup, "i1", [Var("x1"), Var("x2")], Var("y1"))
    action2 = Action(ActionType.Store, "i2", Var("x3"), Var("y2"))
    expr1 = And(action1, action2)
    expr2 = Not(Or(action1, action2))
    
    print("Action Creation Test:")
    print(expr1)
    print(expr2)
    print("-" * 10)

def print_quantifiers():
    expr3 = ForAll(["i1", "x", "y"],
                    Implies(
                        Action(ActionType.FindNode, "i1", Var("x"), Var("y")),
                        Exists(["i2"],
                               And(Action(ActionType.Member, "i2", [], []), During(Interval("i1"), Interval("i2"))))))
    
    print("Quantifier Test:")
    print(expr3)
    print("-" * 10)

def print_variable_evaluation():
    store = {"x": 10, "y": 20}
    trace = Trace()
    interval_store = {}
    
    print("-" * 10)
    print("Variable Evaluation Test:")
    for var in ["x", "y"]:
        expr = Var(var)
        print(expr, "=", expr.evaluate(trace, store, interval_store))

def test_logical_expressions():
    var_store = {
        "x": True,
        "y": False,
    }

    interval_store = {
        "i1": IntervalValue(1, 5),
        "i2": IntervalValue(0, 10),
        "i3": IntervalValue(6, 15),
    }


    trace = Trace()
    
    exprs = [
        (And(Var("x"), Var("y")), False),
        (Or(Var("x"), Var("y")), True),
        (Not(Var("x")), False),
        (Implies(Var("x"), Var("y")), False),
        (Implies(Var("y"), Var("x")), True),
        (Equal(Var("x"), Var("x")), True),
        (Equal(Var("x"), Var("y")), False),
        (During(Interval("i1"), Interval("i2")), True),
        (During(Interval("i2"), Interval("i3")), False),
        (Before(Interval("i1"), Interval("i3")), True),
        (Before(Interval("i2"), Interval("i2")), False),
        # (Meets(Interval("i1"), Interval("i3")), True),
    ]

    print("-" * 10)
    print("Logical Expressions Test:")
    print(var_store)
    for expr, result in exprs:
        print(expr, "=", expr.evaluate(trace, var_store, interval_store))
        assert expr.evaluate(trace, var_store, interval_store) == result, \
            f"Failed for {expr}.\nExpected {result}, got {expr.evaluate(trace, var_store, interval_store)}"

if __name__ == "__main__":
    print_action_creation()
    print_quantifiers()
    print_variable_evaluation()
    test_logical_expressions()
