from __future__ import print_function
import unittest
from llcc.target import TargetInfo

class TestABI(unittest.TestCase):
    def test_x86_64(self):
        ti = TargetInfo.get_host_target()
        ts = ti.typesystem
        args = [ts.get_char(), ts.get_int(), ts.get_float()]
        fnty = ts.get_function(ts.get_void(), args)
        ti.compute_abi_info(fnty)

if __name__ == '__main__':
    unittest.main()
