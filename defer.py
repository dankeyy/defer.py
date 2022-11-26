import ast
import inspect
from functools import partial
from contextlib import ExitStack
from typing import Callable


class RewriteDefer(ast.NodeTransformer):
    def __init__(self, exitstack_name):
        self.exitstack_name = exitstack_name
        super().__init__()

    def visit_AnnAssign(self, node):
        if node.target.id == 'defer':
            post_defer = node.annotation

            if isinstance(post_defer, ast.Call):
                # oblivious to function/ method
                old = post_defer.func
                new = ast.Name('partial', ast.Load())

                post_defer.func = new
                post_defer.args.insert(0, old)
            elif isinstance(post_defer, ast.Lambda):
                # no action needed, just pass the lambda as is to the callback stack
                pass

            else:
                raise Exception("Unimplemented")

            return ast.Expr(value=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id=self.exitstack_name, ctx=ast.Load()),
                                        attr='callback',
                                        ctx=ast.Load(),
                                    ),
                                    args=[post_defer],
                                    keywords=[],
            ))


def defers(func: Callable) -> Callable:

    def wrapped(*args, **kwargs):
        try:
            tree = ast.parse(inspect.getsource(func))
        except OSError:
            return func(*args, **kwargs)

        assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef), "should just be a function wtf"

        stack_name = func.__name__ + "_exitstack"

        RewriteDefer(stack_name).visit(tree.body[0])

        tree.body[0].body.insert(0, ast.Assign(
            targets=[ast.Name(id=stack_name, ctx=ast.Store())],
            value=ast.Call(func=ast.Name(id='ExitStack', ctx=ast.Load()), args=[], keywords=[])
        ))
        # should probably make both those inserts some other way, later..
        tree.body[0].body.insert(0, ast.ImportFrom(
                                        module='defer',
                                        names=[
                                            ast.alias(name='ExitStack'),
                                            ast.alias(name='partial'),
                                        ],
                                        level=0))

        tree.body[0].body.append(ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                        value=ast.Name(id=stack_name, ctx=ast.Load()),
                        attr='close',
                        ctx=ast.Load(),
                ),
                args=[],
                keywords=[],
            )
        ))
        tree = ast.fix_missing_locations(tree)
        func.__code__ = compile(tree, '<ast>', 'exec').co_consts[0]
        return func(*args, **kwargs)

    return wrapped
