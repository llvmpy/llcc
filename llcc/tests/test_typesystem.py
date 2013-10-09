from __future__ import print_function
import unittest
from llcc.target import TargetInfo

class TestTypeSystem(unittest.TestCase):
    def test_exercise(self):
        ti = TargetInfo.get_host_target()
        cts = ti.typesystem

        print('list builtins', cts.builtins)
        self.assertEqual('int64_t', str(cts.get_int(64)),
                        "correct name")
        self.assertEqual('uint32_t', str(cts.get_uint(32)),
                        "correct name")
        self.assertNotEqual(cts.get_int(32), cts.get_uint(32),
                        "signedness diff")
        self.assertEqual(cts.get_int(32), cts.get_int(32),
                        "the same")
        self.assertNotEqual(cts.get_int(64), cts.get_int(32),
                        "int bitsize diff")

        # arrays
        a1 = str(cts.get_array(cts.get_int(32), 5))
        print('a1 =', a1)
        self.assertEqual('int32_t[5]', a1, "array strrep")

        a2 = str(cts.get_array(cts.get_int(64).with_const(), 10))
        print('a2 =', a2)
        self.assertEqual('const int64_t[10]', a2, "qual array strrep")

        # structures
        s1 = cts.get_struct('apple', [('seed', cts.get_int(32)),
                                      ('tree', cts.get_float())])
        print('s1 =', s1)
        print('s1.seed is', s1.type.members.seed)
        print('s1.tree is', s1.type.members.tree)
        self.assertEqual(s1.type.members.seed, cts.get_int(32),
                        "seed is int32")
        self.assertEqual(s1.type.members.tree, cts.get_float(),
                        "tree is float")

        s2 = cts.get_unnamed_struct([('seed', cts.get_int(32)),
                                     ('tree', cts.get_float())])
        print('s2 =', s2)
        self.assertEqual(s2.type.name, '', "is unamed struct")

        s3 = cts.insert_struct('apple')
        print('s3 =', s3)
        self.assertEqual(s3.type.name, 'apple.0', "test auto renaming")

        s4 = cts.insert_struct('apple')
        print('s4 =', s4)
        self.assertEqual(s4.type.name, 'apple.1', "test auto renaming")

        s5 = s4.with_const()
        print('s5 =', s5)
        self.assertEqual(str(s5), 'const struct apple.1',
                        "add const qualifier")

        s6 = s5.without_const()
        print('s6 =', s6)
        self.assertEqual(s6, s4,
                        "removed const qualifier")

        # pointers
        p1 = cts.get_pointer(cts.get_double())
        print('p1 =', p1)
        self.assertEqual('double*', str(p1), "pointer strrep")

        p2 = p1.with_restrict()
        print('p2 =', p2)
        self.assertEqual('restrict double*', str(p2),
                        "restrict pointer strrep")

        # functions
        f1 = cts.get_function(cts.get_void(), [cts.get_int(), cts.get_ulong()])
        self.assertEqual('void(int32_t, uint64_t)', str(f1))

if __name__ == '__main__':
    unittest.main()
