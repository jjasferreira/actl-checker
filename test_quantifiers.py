import unittest
from trace_parser import parse_trace_string
from ast_nodes import *

class TestForAllEvaluation(unittest.TestCase):


    def test_forall_no_action(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), Var("n2"))
        formula = ForAllInterval(Interval("i1"), ForAll(Var("n1"), action))


        log ="""
         # 2000-01-01 11:00:00:00, Lookup, id-000, node1
         # 2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, Join, id-002, node2, 
"""
        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_empty_trace(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAllAction(action, ForAll(Var("n2"), Equal(Var("n1"), Var("n2"))))

        trace = Trace()

        var_store = {}
        interval_store = {}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    # TEST:
    # Test case for an unused variable in the 'ForAll' quantifier.
    # Since the variable 'unused' in the inner formula, 
    # the result will be the evaluation of the inner formula
    def test_forall_unused_var(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAll(Var("unused"), action)

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {"i1" : IntervalValue(0,None)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_single_var_true(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAll(Var("n1"), action)

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Store, id-002, node2, key, value
         2000-01-01 12:00:30.00, ReplyStore, id-002, node3
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_single_var_true_2_actions(self):
        action1 = Action(ActionType.LOOKUP, Interval("i1"), [Var("n1"), Var("k")], [Var("n1"), Var("v")])
        action2 = Action(ActionType.JOIN, Interval("i2"), Var("n2"), [])
        formula = ForAll(Var("n1"), And(action1, action2))

        log = """
        2000-01-01 12:00:00.00, Lookup, id-001, node1, key 
        2000-01-01 12:00:10.00, ReplyLookup, id-001, node1, value
        
        2000-01-01 12:00:20.00, Join, id-002, node2
        2000-01-01 12:00:30.00, ReplyJoin, id-002

        2000-01-01 12:00:40.00, Lookup, id-003, node1, key 
        2000-01-01 12:00:50.00, ReplyLookup, id-003, node1, value
"""

        trace = parse_trace_string(log)

        var_store = { "n2" : "node2", "v" : "value", "k" : "key"}
        interval_store = {
                "i1" : IntervalValue(0,1),
                "i2" : IntervalValue(2,3)
        }

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_forall_single_var_false(self):

        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAll(Var("n1"), action)

        log ="""# 
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001
         #
         2000-01-01 12:00:20.00, Join, id-002, node2 
         2000-01-01 12:00:30.00, ReplyJoin, id-002, node2
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_forall_single_var_false_2_occurences(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = ForAll(Var("n1"), action)

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
         2000-01-01 12:00:10.00, ReplyJoin, id-001

         2000-01-01 12:00:20.00, Join, id-002, node1 
         2000-01-01 12:00:30.00, ReplyJoin, id-002, node1
        
         2000-01-01 12:00:40.00, Join, id-003, node2 
         2000-01-01 12:00:50.00, ReplyJoin, id-003, node2
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_forall_multiple_var_true(self):

        action = Action(ActionType.STORE, Interval("i1"), [Var("n1"), Var("k1"), Var("v1")], Var("y1"))
        formula = ForAll([Var("n1"), Var("k1"), Var("v1"), Var("y1")], action)

        log ="""# 
         2000-01-01 12:00:00.00, Store, id-001, node1, key1, value1
         2000-01-01 12:00:10.00, ReplyStore, id-001, node2
         #
         2000-01-01 12:00:20.00, Store, id-002, node1, key1, value1
         2000-01-01 12:00:30.00, ReplyStore, id-002, node2
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)



    def test_forall_multiple_var_false(self):

        action = Action(ActionType.STORE, Interval("i1"), [Var("n1"), Var("k1"), Var("v1")], Var("y1"))
        formula = ForAll([Var("n1"), Var("k1"), Var("v1"), Var("y1")], action)

        log ="""# 
         2000-01-01 12:00:00.00, Store, id-001, node1, key1, value1
         2000-01-01 12:00:10.00, ReplyStore, id-001, node2
         #
         2000-01-01 12:00:20.00, Store, id-002, node2, key1, value2
         2000-01-01 12:00:30.00, ReplyStore, id-002, node3
"""

        trace = parse_trace_string(log)

        var_store = {}

        interval_store = {"i1": IntervalValue(0, 1)}

        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)



class TestExistsEvaluation(unittest.TestCase):
    def test_exists_empty_trace(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = Exists(Var("n1"), action)

        trace = Trace()

        var_store = {}
        interval_store = {}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)


    def test_exists_unused_var(self):
        action = Action(ActionType.JOIN, Interval("i1"), Var("n1"), [])
        formula = Exists(Var("unused"), action)

        log ="""
         2000-01-01 12:00:00.00, Join, id-001, node1
"""
        trace = parse_trace_string(log)

        var_store = {"n1" : "node1"}
        interval_store = {"i1" : IntervalValue(0,None)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_exists_single_var_true(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("n1")], [])
        formula = Exists(Var("n1"), action)


        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, node1
         2000-01-01 12:00:10.00, ReplyFindNode, id-001,
         
         2000-01-01 12:00:20.00, FindNode, id-002, node2, key
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)


    def test_exists_single_var_false(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("n1")], [])
        formula = Exists(Var("n1"), action)


        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, node2
         2000-01-01 12:00:10.00, ReplyFindNode, id-001,
         2000-01-01 12:00:20.00, Lookup, id-002, node2, key
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_exists_multiple_var_true(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("k1")], [Var("n2"), Var("n2")])
        formula = Exists([Var("n1"), Var("k1"), Var("n2")], action)


        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, key
         2000-01-01 12:00:10.00, ReplyFindNode, id-001, node2, node2
         2000-01-01 12:00:20.00, Lookup, id-002, node2, key
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_exists_multiple_var_true_equal_vars(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("k1")], [Var("n2"), Var("n3")])
        formula = Exists([Var("n1"), Var("k1"), Var("n2"), Var("n3")], And(action,  Equal(Var("n2"), Var("n3"))))

        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, key
         2000-01-01 12:00:10.00, ReplyFindNode, id-001, node2, node2
         2000-01-01 12:00:20.00, Lookup, id-002, node2, key
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertTrue(result)

    def test_exists_multiple_var_false(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("k1")], [Var("n2"), Var("n2")])
        formula = Exists([Var("n1"), Var("k1"), Var("n2")], action)


        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, key
         2000-01-01 12:00:10.00, ReplyFindNode, id-001, node2, node3
         2000-01-01 12:00:20.00, Lookup, id-002, node2, key
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

    def test_exists_multiple_var_false_equal_vars(self):

        action = Action(ActionType.FINDNODE, Interval("i1"), [Var("n1"), Var("k1")], [Var("n2"), Var("n3")])
        formula = Exists([Var("n1"), Var("k1"), Var("n2"), Var("n3")], And(action,  Equal(Var("n2"), Var("n3"))))

        log ="""
         2000-01-01 12:00:00.00, FindNode, id-001, node1, key
         2000-01-01 12:00:10.00, ReplyFindNode, id-001, node2, node3
         2000-01-01 12:00:20.00, Lookup, id-002, node2, key
"""

        trace = parse_trace_string(log)

        var_store = {}
        interval_store = {"i1" : IntervalValue(0,1)}
        
        result = formula.evaluate(trace, var_store, interval_store)

        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
