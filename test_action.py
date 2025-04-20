import unittest
from ast_nodes import *
from trace_parser import parse_trace_string

class TestActionEvaluation(unittest.TestCase):

    def test_action_evaluate_true(self):
        action = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
        2000-01-01 12:00:10.00, ReplyLookup, id1, node1, value0
"""

        trace = parse_trace_string(log)

        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertTrue(result)


    def test_action_evaluate_false_boundary(self):
        action = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        

        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
        2000-01-01 12:00:10.00, ReplyLookup, id1, node1, value0
"""

        trace = parse_trace_string(log)

        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        #TEST: Interval should be (0, 1)
        interval_store = {"i1": IntervalValue(0, 2)} 
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)

    def test_action_evaluate_false_input(self):
        action = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
        2000-01-01 12:00:10.00, ReplyLookup, id1, node1, value0
"""

        trace = parse_trace_string(log)
        
        #TEST: "x1" should be mapped to "node0"
        eval_store = {
            "x1": "missing_value", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)


    def test_action_evaluate_false_output(self):
        action = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
        2000-01-01 12:00:10.00, ReplyLookup, id1, node1, value0
"""

        trace = parse_trace_string(log)

        #TEST: "y1" should be mapped to "node1"
        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "missing_value"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)


    def test_action_evaluate_true_infinite(self):
        action = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
"""

        trace = parse_trace_string(log)

        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, None)}
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertTrue(result)

    def test_action_evaluate_false_infinite(self):
        action = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
"""

        trace = parse_trace_string(log)

        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        #TEST: Interval should be (0, None)
        interval_store = {"i1": IntervalValue(0, 1)}
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)


    def test_action_evaluate_false_type(self):
        #TEST: ActionType should be LOOKUP
        action = Action(ActionType.STORE, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        
        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
        2000-01-01 12:00:10.00, ReplyLookup, id1, node1, value0
"""

        trace = parse_trace_string(log)

        eval_store = {
            "x1": "node0", "x2": "key0", 
            "x5": "value0", "y1": "node1"
        }
        
        interval_store = {"i1": IntervalValue(0, 1)}
        
        result = action.evaluate(trace, eval_store, interval_store)

        self.assertFalse(result)


    def test_2_actions_evaluate_true(self):
        action1 = Action(ActionType.LOOKUP, Interval("i1"), [Var("x1"), Var("x2")], [Var("y1"), Var("x5")])
        action2 = Action(ActionType.STORE, Interval("i2"), [Var("x3"), Var("x4"), Var("x5")], Var("y2"))
        

        log ="""
        2000-01-01 12:00:00.00, Lookup, id1, node0, key0
        2000-01-01 12:00:10.00, Store, id2, node2, key1, value0
        2000-01-01 12:00:20.00, ReplyLookup, id1, node1, value0
        2000-01-01 12:00:30.00, ReplyStore, id2, node3
"""

        trace = parse_trace_string(log)
        eval_store = {
            "x1": "node0", "x2": "key0", "x3": "node2", 
            "x4": "key1", "x5": "value0", "y1": "node1", "y2": "node3"
        }
        
        interval_store = {"i1": IntervalValue(0, 2), "i2": IntervalValue(1, 3)}
        
        result = action1.evaluate(trace, eval_store, interval_store)

        self.assertTrue(result)

        result = action2.evaluate(trace, eval_store, interval_store)

        self.assertTrue(result)


    def test_action_fail_evaluate_true(self):
        action = Action(ActionType.FAIL, Interval("i1"), Var("n1"), [])

        log ="""
         2000-01-01 12:00:00.00, FAIL, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {"i1" : IntervalValue(0,0)}

        result = action.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
