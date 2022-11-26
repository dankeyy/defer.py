import ast
import inspect
from functools import partial
from contextlib import contextmanager
from contextlib import ExitStack
from typing import Callable

@contextmanager

class RewriteDefer(ast.NodeTransformer):
    def __init__(self, exitstack_name):
        self.exitstack_name = exitstack_name
        super().__init__()

    def visit_AnnAssign(self, node):
        if node.target.id == 'defer':
            post_defer = node.annotation

            if isinstance(post_defer, ast.Call):
                old_defer = post_defer
                post_defer = ast.Call(
                    func=ast.Name('partial', ast.Load()),
                    args=[post_defer.func] + post_defer.args,
                    keywords=post_defer.keywords,
                )
            else:
                raise Exception("Unimplemented")

            new_node = ast.Expr(value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id=self.exitstack_name, ctx=ast.Load()),
                                            attr='callback',
                                            ctx=ast.Load(),
                                        ),
                                        args=[post_defer],
                                        keywords=[],
            )) 
            # TODO: this is terrible.
            if isinstance(node.value, ast.NameConstant):
                new_node.value.args.append(old_defer)
            elif isinstance(node.value, ast.Name):
                new_node.value.args.append(ast.Name(node.value.id, node.value.ctx))
            elif isinstance(node.value, ast.Call):
                new_node.value.args.append(ast.Call(
                    func=node.value.func,
                    args=node.value.args,
                    keywords=node.value.keywords,
                ))
            else:
                raise Exception("Unimplemented.")
            return new_node


def defers(func: Callable) -> Callable:

    def wrapped(*args, **kwargs):
        try:
            tree = ast.parse(inspect.getsource(func))
        except OSError:
            return func(*args, **kwargs)


        stack_name = func.__name__ + "_exitstack"

        RewriteDefer(stack_name).visit(tree.body[0])

        if len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef):
            node = tree.body[0]
        else:
            node = tree.body[0].value # hopefully this is a return, or just a statement.

        node.body.insert(0, ast.Assign(
            targets=[ast.Name(id=stack_name, ctx=ast.Store())],
            value=ast.Call(func=ast.Name(id='ExitStack', ctx=ast.Load()), args=[], keywords=[])
        ))
        # should probably make both those inserts some other way, later..
        node.body.insert(0, ast.ImportFrom(
                                        module='defer',
                                        names=[
                                            ast.alias(name='ExitStack'),
                                            ast.alias(name='partial'),
                                        ],
                                        level=0))

        ))
        node.body.append(ast.Expr(
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

        if isinstance(tree.body[0], ast.FunctionDef):
            func.__code__ = compile(tree, '<ast>', 'exec').co_consts[0]
        else:
            # this is a hack, and is probably really really really bad.
            exec(compile(tree, '<ast>', 'exec'))
            func = eval(func.__name__)

        return func(*args, **kwargs)

    return wrapped
