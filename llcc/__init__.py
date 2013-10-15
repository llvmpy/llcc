from .test_support import TestSystem

def test(verbosity=3, buffer=True):
    import llcc.tests
    tsys = TestSystem()
    tsys.discover(llcc.tests)
    tr = tsys.run(verbosity=verbosity, buffer=buffer)
    return tr.wasSuccessful()

