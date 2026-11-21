import ast
import operator as op

OPERATORS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
    ast.USub: op.neg, ast.UAdd: op.pos
}

def calculate(expression):
    expression = expression.strip()
    if not expression:
        raise ValueError("Enter an expression")
    if len(expression) > 200:
        raise ValueError("Expression is too long")
    try:
        node = ast.parse(expression, mode="eval").body
    except (SyntaxError, ValueError) as exc:
        raise ValueError("Invalid expression") from exc
    return evaluate(node)

def evaluate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate(node.left)
        right = evaluate(node.right)
        if isinstance(node.op, ast.Pow):
            if abs(left) > 1e100 or abs(right) > 1000:
                raise ValueError("Exponent is too large")
        if isinstance(node.op, ast.Mod) and right == 0:
            raise ValueError("Division by zero")
        if isinstance(node.op, ast.Div) and right == 0:
            raise ValueError("Division by zero")
        try:
            result = OPERATORS[type(node.op)](left, right)
        except (ArithmeticError, OverflowError) as exc:
            raise ValueError("Invalid arithmetic operation") from exc
        if isinstance(result, float) and (result != result or result in (float("inf"), float("-inf"))):
            raise ValueError("Result is outside the supported range")
        return result
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.operand))
    raise ValueError("Unsupported expression")