from __future__ import print_function
import unittest
from llcc.target import TargetInfo

class TestABI_X86_64(unittest.TestCase):
    def setUp(self):
        self.ti = TargetInfo.get_host_target()
        self.ts = self.ti.typesystem

    def test_scalars(self):
        args = [self.ts.get_char(), self.ts.get_int(), self.ts.get_float()]
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)
        self.assertTrue(abi.return_info.is_ignore)
        self.assertTrue(abi.arg_infos[0].is_extend)
        self.assertTrue(abi.arg_infos[1].is_direct)
        self.assertTrue(abi.arg_infos[2].is_direct)

    def test_ptr(self):
        args = []
        args.append(self.ts.get_opaque_ptr())                   # void*
        args.append(self.ts.get_pointer(self.ts.get_int()))     # int32_t*
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)
        self.assertTrue(abi.return_info.is_ignore)
        self.assertTrue(abi.arg_infos[0].is_direct)
        self.assertEqual(abi.arg_infos[0].coerce_type, args[0].type)
        self.assertTrue(abi.arg_infos[1].is_direct)
        self.assertEqual(abi.arg_infos[1].coerce_type, args[1].type)

    def test_struct_as_floatx2(self):
        args = []
        fty = self.ts.get_float()
        args.append(self.ts.get_unnamed_struct([('f0', fty), ('f2', fty)]))
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)
        self.assertTrue(abi.return_info.is_ignore)

        self.assertTrue(abi.arg_infos[0].is_direct)
        self.assertNotEqual(abi.arg_infos[0].coerce_type, args[0].type)

        vecty = self.ts.get_vector(self.ts.get_float(), 2)
        self.assertEqual(abi.arg_infos[0].coerce_type, vecty)

    def test_3float(self):
        args = []
        fty = self.ts.get_float()
        args.append(self.ts.get_unnamed_struct([('f0', fty), ('f2', fty),
                                                ('f3', fty)]))
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)

        self.assertTrue(abi.return_info.is_ignore)

        # pass as two argument: <float x 2>, float
        first = self.ts.get_vector(fty, 2)
        second = fty

        self.assertTrue(abi.arg_infos[0].is_direct)
        self.assertEqual(abi.arg_infos[0].coerce_type[0], first)
        self.assertEqual(abi.arg_infos[0].coerce_type[1], second)

    def test_4float(self):
        args = []
        fty = self.ts.get_float()
        args.append(self.ts.get_unnamed_struct([fty] * 4))
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)
        
        self.assertTrue(abi.return_info.is_ignore)

        # pass as two argument: <float x 2>, <float x 2>
        vecty = self.ts.get_vector(fty, 2)

        self.assertTrue(abi.arg_infos[0].is_direct)
        self.assertEqual(abi.arg_infos[0].coerce_type[0], vecty)
        self.assertEqual(abi.arg_infos[0].coerce_type[1], vecty)

    def test_5float(self):
        args = []
        fty = self.ts.get_float()
        args.append(self.ts.get_unnamed_struct([fty] * 5))
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)

        # pass on the stack
        self.assertTrue(abi.return_info.is_ignore)
        self.assertTrue(abi.arg_infos[0].is_indirect)

    def test_2double(self):
        args = []
        fty = self.ts.get_double()
        args.append(self.ts.get_unnamed_struct([fty] * 2))
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)

        self.assertTrue(abi.return_info.is_ignore)

        # pass as {double, double}
        self.assertTrue(abi.arg_infos[0].is_direct)
        self.assertEqual(abi.arg_infos[0].coerce_type[0], fty)
        self.assertEqual(abi.arg_infos[0].coerce_type[1], fty)

    def test_3double(self):
        args = []
        fty = self.ts.get_double()
        args.append(self.ts.get_unnamed_struct([fty] * 3))
        fnty = self.ts.get_function(self.ts.get_void(), args)
        abi = self.ti.compute_abi_info(fnty)
        print(abi)

        self.assertTrue(abi.return_info.is_ignore)

        # pass as on the stack
        self.assertTrue(abi.arg_infos[0].is_indirect)



if __name__ == '__main__':
    unittest.main()
