from defer import defers


# god level testing
@defers
def test_print():
    print(1)
    defer: print(3)
    print(2)

test_print()
