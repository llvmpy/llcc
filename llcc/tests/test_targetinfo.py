from __future__ import print_function
import unittest
from pprint import pprint
from ctypes import sizeof, c_void_p
from llcc.target import TargetInfo

class TestTargetInfo(unittest.TestCase):
    def test_exercise(self):
        ti = TargetInfo.get_host_target()
        pprint(ti.sizeof_table)
        pprint(ti.align_table)

        intptr = ti.typesystem.get_intptr()

        intptr_align = ti.get_align(intptr)
        self.assertEqual(sizeof(c_void_p) * 8, intptr_align,
                         "intptr alignment")

        intptr_sizeof = ti.get_sizeof(intptr)
        self.assertEqual(sizeof(c_void_p) * 8, intptr_sizeof,
                         "intptr sizeof")

        voidptr = ti.typesystem.get_opaque_ptr()
        voidptr_sizeof = ti.get_sizeof(voidptr)
        self.assertEqual(intptr_sizeof, voidptr_sizeof,
                         "void* sizeof == intptr sizeof")

if __name__ == '__main__':
    unittest.main()
