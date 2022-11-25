# defer.py
as usual, q&a:

## q: what
a: this

```py
from defer import defers

@defers
def f():
    print(1)
    defer: print(3)
    print(2)

f()
```

``` console
$ python test.py
1
2
3
```

Basically a go-like (in the future, hopefully more like zig's) defer statement for python.

## q: how
a: So you know how python just ignores all type hints not related to class/module? (literally has no affect, the compiler just ignores it) \
And you know how I like to stupidly abuse shit in python?

What this does, via some ast manipulation is basically, mostly, this:
1. Add a `f_exitstack = contextlib.ExitStack()` declaration to the beginning of the function.
2. Transform that `defer: print(i)` into a callback-able thingy like `partial(print, i)`
and push it unto the stack, so that we end up with `f_exitstack.callback(partial(print, i))`. \
This is done by replacing the AnnAssign annotations node with whatever we came up with.
3. At the end of the function, add a call to `f_exitstack.close()` to resolve our defers.
4. ??
5. profit

## why
a: Because & for the nice guy on reddit who suggested it. Also stop asking me that

## q: should you use it?
a: No

## q: why not
a: Because it sucks

## q: why does this suck
a: Don't be rude

---

Still very early stage, will probably change its behaviour a lot, e.g: 
- Maybe exitstack per loop too (so that unlike in go, if we defer in loop, we'd get the outputs not "in reverse")?
- Maybe take advantage of the incdec encoding trick to relieve users of needing to put a decorator?
> Both of the above will require a much more thorough (+complex?) traversal of the ast, so we'll see
- Make it work for statements?
> Pretty weird to deal with because we can't delay it in the same way as function calls, but open for exploration.
- Add support for any kind of blocked (not one-liner) stuff?
> Any messing around with stuff like that would _probably_ require another initial traversal of the code and fixing the ast, which kinda ruins the whole beauty of this is a valid parse to begin with. But again open for exploration.

That's it \
have a nice day
