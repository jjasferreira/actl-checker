import unittest

from ast_nodes import *

class TestActionEvaluation(unittest.TestCase):

    def test_action_evaluate_true(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["node0", "key0"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["node1", "value0"], "id1"))

        # print(f"{trace = }")
        # print(f"{eval_store = }")
        # print(f"{interval_store = }")
        #
        # print(f"{action = }")

        result = action.evaluate(trace, eval_store, interval_store)

        # print(f"{result = }")

        self.assertTrue(result)


    def test_action_evaluate_false_boundary(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 2)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["node0", "key0"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["node1", "value0"], "id1"))

        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)

    def test_action_evaluate_false_input(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 2)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["node_banana", "key0"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["node1", "value0"], "id1"))

        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)


    def test_action_evaluate_false_output(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 2)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["node0", "key0"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["node_kiwi", "value0"], "id1"))

        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)

    def test_action_evaluate_false_id(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 2)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["node0", "key0"], "id1"))
        trace.append(EndEvent(ActionType.Lookup, ["node1", "value0"], "id2"))

        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)

    def test_action_evaluate_false_type(self):
        action = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 2)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Store, ["node0", "key0"], "id1"))
        trace.append(EndEvent(ActionType.Store, ["node1", "value0"], "id1"))

        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)


    def test_2_actions_evaluate(self):
        action1 = Action(ActionType.Lookup, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        action2 = Action(ActionType.Store, Interval("i2"), [Var("x3"), Var("x4"), Var("x5")], Var("y2"))
        
        eval_store = {
            "x1": "node0", "x2": "key0", "x3": "node2", 
            "x4": "key1", "x5": "value0", "y1": "node1", "y2": "node3"
        }
        
        interval_store = {"i1": IntervalValue(0, 2), "i2": IntervalValue(1, 3)}
        
        trace = Trace()
        trace.append(BeginEvent(ActionType.Lookup,["node0", "key0"], "id1"))
        trace.append(BeginEvent(ActionType.Store,["node2", "key1", "value0"], "id2"))
        trace.append(EndEvent(ActionType.Lookup, ["node1", "value0"], "id1"))
        trace.append(EndEvent(ActionType.Store, ["node3"], "id2"))

        result = action1.evaluate(trace, eval_store, interval_store)

        self.assertTrue(result)

        result = action2.evaluate(trace, eval_store, interval_store)

        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
