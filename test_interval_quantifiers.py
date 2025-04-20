import unittest
from trace_parser import parse_trace_string
from ast_nodes import *

class TestForAllIntervalEvaluation(unittest.TestCase):


    def test_forall_empty_trace(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllInterval(Interval("i1"), action)

        trace = Trace()

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    # TEST:
    # Test case for an unused variable in the 'ForAll' quantifier.
    # Since the variable 'unused' is unused in the inner formula, 
    # the result will be the evaluation of the inner formula
    def test_forall_unused_interval(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllInterval(Interval("unused"), action)

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {"i1" : IntervalValue(0,None)}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_true(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllInterval(Interval("i1"), action)

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Store, id-002, node2, key, value
         2000-01-01 12:00:30.00, ReplyStore, id-002, node3
"""

        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_forall_true_2_intervals(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllInterval(Interval("i1"), action)

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Store, id-002, node2, key, value
         2000-01-01 12:00:30.00, ReplyStore, id-002, node3

         2000-01-01 12:00:40.00, Join, id-003, node1
         2000-01-01 12:00:50.00, ReplyJoin, id-003
"""

        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_false(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllInterval(Interval("i1"), action)

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node2
         2000-01-01 12:00:10.00, ReplyJoin, id-001
"""

        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_forall_false_2_intervals(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllInterval(Interval("i1"), action)

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Join, id-002, node2 
         2000-01-01 12:00:30.00, ReplyJoin, id-002, node2
"""

        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

class TestExistsIntervalEvaluation(unittest.TestCase):
    def test_exists_empty_trace(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ExistsInterval(Interval("i1"), action)

        trace = Trace()

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)


    def test_exists_unused_interval(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ExistsInterval(Interval("unused"), action)

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {"i1" : IntervalValue(0,None)}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_exists_true(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("n1")], [])
        formula = ExistsInterval(Interval("i1"), action)


        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, node1
         2000-01-01 12:00:10.00, ReplyFindNode, id-001,

         2000-01-01 12:00:20.00, FindNode, id-002, node2, key
         2000-01-01 12:00:30.00, ReplyFindNode, id-002, node2
"""

        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_exists_false(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("n1")], [])
        formula = ExistsInterval(Interval("i1"), action)


        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, node2
         2000-01-01 12:00:10.00, ReplyFindNode, id-001,
"""

        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
