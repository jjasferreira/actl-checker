import unittest
from trace_parser import parse_trace_string
from ast_nodes import *

class TestForAllActionEvaluation(unittest.TestCase):

    def test_forall_empty_trace(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllAction(action, Before(Interval("i1"), Interval("i1")))

        trace = Trace()

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_forall_unused_interval(self):
        action = Action(ActionType.JOIN, Interval("unused"), Var("n1"), [])
        formula = ForAllAction(action, Equal(Var("n1"), Var("n1")))

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_true(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllAction(action, Equal(Var("n1"), Var("n2")))

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Store, id-002, node2, key, value
         2000-01-01 12:00:30.00, ReplyStore, id-002, node3
"""

        trace = parse_trace_string(log)

        var_store = {"n2" : "node1"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_forall_false(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllAction(action, Equal(Var("n1"), Var("n2")))

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
"""

        trace = parse_trace_string(log)

        var_store = {"n2" : "node2"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_forall_true_2_intervals(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllAction(action, Or(Equal(Var("n1"), Var("n2")), Equal(Var("n1"), Var("n3"))))

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Store, id-002, node2, key, value
         2000-01-01 12:00:30.00, ReplyStore, id-002, node3

         2000-01-01 12:00:40.00, Join, id-003, node2
         2000-01-01 12:00:50.00, ReplyJoin, id-003
"""

        trace = parse_trace_string(log)

        var_store = {"n2" : "node1", "n3" : "node2"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_forall_false_2_intervals(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllAction(action, Equal(Var("n1"), Var("n2")))

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Join, id-002, node2 
         2000-01-01 12:00:30.00, ReplyJoin, id-002
"""

        trace = parse_trace_string(log)

        var_store = {"n2" : "node1"}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

class TestExistsActionEvaluation(unittest.TestCase):
    def test_exists_empty_trace(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ExistsAction(action, Before(Interval("i1"), Interval("i1")))

        trace = Trace()

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)


    def test_exists_unused_interval(self):
        action = Action(ActionType.JOIN, Interval("unused"), Var("n1"), [])
        formula = ExistsAction(action, Equal(Var("n1"), Var("n1")))

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_exists_true(self):
        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("n2")], [])
        formula = ExistsAction(action, Equal(Var("n1"), Var("n2")))

        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, node1
         2000-01-01 12:00:10.00, ReplyFindNode, id-001,

         2000-01-01 12:00:20.00, FindNode, id-002, node2, key
         2000-01-01 12:00:30.00, ReplyFindNode, id-002, node2
# """

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_exists_false(self):
        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("n2")], [])
        formula = ExistsAction(action, Equal(Var("n1"), Var("n2")))

        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, key
         2000-01-01 12:00:10.00, ReplyFindNode, id-001,

         2000-01-01 12:00:20.00, FindNode, id-002, node2, key
         2000-01-01 12:00:30.00, ReplyFindNode, id-002, node2
# """

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
