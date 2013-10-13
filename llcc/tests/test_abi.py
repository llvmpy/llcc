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

if __name__ == '__main__':
    unittest.main()
