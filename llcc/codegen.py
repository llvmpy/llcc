from __future__ import print_function
import llvm.core

#-------------------------------------------------------------------------------
# Value
#-------------------------------------------------------------------------------

class Value(object):
    def __init__(self, ty, lv):
        self.type = ty
        self.lv = lv


#-------------------------------------------------------------------------------
# Module
#-------------------------------------------------------------------------------

class Module(object):
    def __init__(self, target, name=''):
        self.target = target
        self.ir = llvm.core.Module.new(name)

    @property
    def typesystem(self):
        return self.target.typesystem

    @property
    def abi(self):
        return self.abi_info

    def add_function(self, fnty, name):
        fnabi = self.abi.get_function_abi(fnty)
        print(fnabi)
        raise NotImplementedError
#        self.ir.add_function()
#        fv = Value(fnty, )
#        return fv
