import unittest

from ast_nodes import *

class TestQuantifierEvaluation(unittest.TestCase):

    def test_universal_quantifier_single_var_evaluate_true(self):

        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = ForAll(Var("x1"), action)

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
             "x2": "test", 
            "x5": "test", "y1": "test"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertTrue(result)


    def test_universal_quantifier_single_var_evaluate_false(self):

        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = ForAll(Var("x1"), action)

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
             "x2": "test", 
            "x5": "test", "y1": "no"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertFalse(result)

    def test_universal_quantifier_multiple_var_evaluate_true(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = ForAll([Var("x1"), Var("x2")], action)

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
            "x5": "test", "y1": "test"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertTrue(result)


    def test_universal_quantifier_multiple_var_evaluate_false(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = ForAll([Var("x1"), Var("x2")], action)

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
            "x5": "test", "y1": "no"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertFalse(result)


    def test_existential_quantifier_single_var_evaluate_false(self):

        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = Not(Exists(Var("x1"), action))

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
             "x2": "test", 
            "x5": "test", "y1": "test"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertFalse(result)


    def test_existential_quantifier_single_var_evaluate_true(self):

        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = Not(Exists(Var("x1"), action))

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
             "x2": "test", 
            "x5": "test", "y1": "no"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertTrue(result)

    def test_existential_quantifier_multiple_var_evaluate_false(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = Not(Exists([Var("x1"), Var("x2")], action))

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
            "x5": "test", "y1": "test"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertFalse(result)


    def test_existential_quantifier_multiple_var_evaluate_true(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        formula = Not(Exists([Var("x1"), Var("x2")], action))

        # eval_store = {
        #     "x2": "key0", 
        #     "x5": "value0", "y1": "node1"
        # }


        eval_store = {
            "x5": "test", "y1": "no"
        }

        interval_store = {"i1": IntervalValue(0, 1)}


        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["test", "test"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["test", "test"], "id1"))

        #print(f"{trace = }")
        #print(f"{eval_store = }")
        #print(f"{interval_store = }")

        #print(f"{action = }")

        result = formula.evaluate(trace, eval_store, interval_store)

        #print(f"{result = }")

        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
