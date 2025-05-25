import unittest
from parser import ASTTransformer, parser
from ast_nodes import *


class TestDSLParser(unittest.TestCase):

    def parse_and_transform(self, text :  str):
        tree = parser.parse(text)
        return ASTTransformer().transform(tree)

    def test_constant(self):
        ast = self.parse_and_transform("(a = 'c1)")
        self.assertIsInstance(ast, Equal)
        self.assertIsInstance(ast.left, Var)
        self.assertIsInstance(ast.right, Constant)
        self.assertEqual(ast.right.label, "c1")

    def test_variable(self):
        ast = self.parse_and_transform("(a = b)")
        self.assertIsInstance(ast, Equal)
        self.assertIsInstance(ast.left, Var)
        self.assertIsInstance(ast.right, Var)
        self.assertEqual(ast.left.label, "a")
        self.assertEqual(ast.right.label, "b")

    def test_wildcard(self):
        ast = self.parse_and_transform("(a = -)")
        self.assertIsInstance(ast, Equal)
        self.assertIsInstance(ast.right, Wildcard)

    def test_and_binary_expression(self):
        ast = self.parse_and_transform("(and (a = b) (b = c))")
        self.assertIsInstance(ast, And)
        self.assertEqual(len(ast.expressions), 2)
        self.assertTrue(all(isinstance(x, Equal) for x in ast.expressions))

    def test_and_nary_expression(self):
        ast = self.parse_and_transform("(and (a = b) (b = c) (d = e) (f = g))")
        self.assertIsInstance(ast, And)
        self.assertEqual(len(ast.expressions), 4)
        self.assertTrue(all(isinstance(x, Equal) for x in ast.expressions))

    def test_or_binary_expression(self):
        ast = self.parse_and_transform("(or (a = b) (b = c))")
        self.assertIsInstance(ast, Or)
        self.assertEqual(len(ast.expressions), 2)
        self.assertTrue(all(isinstance(x, Equal) for x in ast.expressions))

    def test_or_nary_expression(self):
        ast = self.parse_and_transform("(or (a = b) (b = c) (d = e) (f = g))")
        self.assertIsInstance(ast, Or)
        self.assertEqual(len(ast.expressions), 4)
        self.assertTrue(all(isinstance(x, Equal) for x in ast.expressions))

    def test_implies(self):
        ast = self.parse_and_transform("(implies (a = b) (b = c))")
        self.assertIsInstance(ast, Implies)

    def test_before(self):
        ast = self.parse_and_transform("(before a b)")
        self.assertIsInstance(ast, Before)

    def test_meets(self):
        ast = self.parse_and_transform("(meets a b)")
        self.assertIsInstance(ast, Meets)

    def test_overlaps(self):
        ast = self.parse_and_transform("(overlaps a b)")
        self.assertIsInstance(ast, Overlaps)

    def test_starts(self):
        ast = self.parse_and_transform("(starts a b)")
        self.assertIsInstance(ast, Starts)

    def test_during(self):
        ast = self.parse_and_transform("(during a b)")
        self.assertIsInstance(ast, During)

    def test_finishes(self):
        ast = self.parse_and_transform("(finishes a b)")
        self.assertIsInstance(ast, Finishes)

    def test_equals(self):
        ast = self.parse_and_transform("(equals a b)")
        self.assertIsInstance(ast, Equals)

    def test_in(self):
        ast = self.parse_and_transform("(in a b)")
        self.assertIsInstance(ast, Or)
        self.assertTrue(all(isinstance(child, (Starts, During, Finishes)) for child in ast.expressions))

    def test_intersects(self):
        ast = self.parse_and_transform("(intersects a b)")
        self.assertIsInstance(ast, Or)

        # Extract all top-level children of the outer Or
        expression = ast.expressions
        self.assertEqual(len(expression), 5)

        # 1. Equals(a, b)
        self.assertIsInstance(expression[0], Equals)

        self.assertEqual(expression[0].left, Interval("a"))
        self.assertEqual(expression[0].right, Interval("b"))

        # 2. Or(Starts(a, b), During(a, b), Finishes(a, b))
        in_ab = expression[1]
        self.assertIsInstance(in_ab, Or)
        self.assertEqual(len(in_ab.expressions), 3)
        self.assertIsInstance(in_ab.expressions[0], Starts)
        self.assertIsInstance(in_ab.expressions[1], During)
        self.assertIsInstance(in_ab.expressions[2], Finishes)

        for rel in in_ab.expressions:
            self.assertEqual(rel.left, Interval("a"))
            self.assertEqual(rel.right, Interval("b"))

        # 3. Or(Starts(b, a), During(b, a), Finishes(b, a))
        in_ba = expression[2]
        self.assertIsInstance(in_ba, Or)
        self.assertEqual(len(in_ba.expressions), 3)
        self.assertIsInstance(in_ba.expressions[0], Starts)
        self.assertIsInstance(in_ba.expressions[1], During)
        self.assertIsInstance(in_ba.expressions[2], Finishes)

        for rel in in_ba.expressions:
            self.assertEqual(rel.left, Interval("b"))
            self.assertEqual(rel.right, Interval("a"))

        # 4. Overlaps(a, b)
        self.assertIsInstance(expression[3], Overlaps)
        self.assertEqual(expression[3].left, Interval("a"))
        self.assertEqual(expression[3].right, Interval("b"))

        # 5. Overlaps(b, a)
        self.assertIsInstance(expression[4], Overlaps)
        self.assertEqual(expression[4].left, Interval("b"))
        self.assertEqual(expression[4].right, Interval("a"))

    def test_forall(self):
        dsl = "(forall lookup i1 (x) (y) (x = y))"
        ast = self.parse_and_transform(dsl)
        self.assertIsInstance(ast, ForAllAction)
        self.assertIsInstance(ast.action, Action)
        self.assertIsInstance(ast.expression, Equal)

    def test_exists(self):
        dsl = "(exists lookup i2 (a) (b) (a = b))"
        ast = self.parse_and_transform(dsl)
        self.assertIsInstance(ast, ExistsAction)
        self.assertIsInstance(ast.expression, Equal)

    def test_nested_quantifier(self):
        dsl = """
        (exists lookup i1 (x) (y)
            (forall lookup i2 (a) (b)
                (a = b)
            )
        )
        """
        ast = self.parse_and_transform(dsl)
        self.assertIsInstance(ast, ExistsAction)
        self.assertIsInstance(ast.expression, ForAllAction)

if __name__ == '__main__':
    unittest.main()
