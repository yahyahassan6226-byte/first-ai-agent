import ast
import operator

allowed = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def calculator(expression):

    def solve(node):

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.BinOp):
            return allowed[type(node.op)](
                solve(node.left),
                solve(node.right)
            )

        raise ValueError("Invalid expression")

    tree = ast.parse(expression, mode="eval")

    return str(solve(tree.body))