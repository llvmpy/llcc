import sys
import ctypes
import llvm.ee
import llcc.typesystem

#-------------------------------------------------------------------------------
# ABI convetions
#-------------------------------------------------------------------------------


ABI_WIN32 = {32: 'Win32/i386',
             64: 'Win64/AMD64'}

ABI_SYSTEMV = {32: 'SystemV/i386',
               64: 'SystemV/AMD64'}

#-------------------------------------------------------------------------------
# Target Information
#-------------------------------------------------------------------------------


class TargetInfo(object):
    '''
    Use one of the factory methods to construct a TargetInfo.
    '''
    @staticmethod
    def get_host_target():
        ti = TargetInfo()
        ti.init_match_host()
        return ti

    def init_match_host(self, jit=False):
        '''Initialize target to match host.
        '''
        self.typesystem = llcc.typesystem.CTypeSystem()
        self.typesystem.init_host_type_mapping()

        # use host machine
        self.machine = llvm.ee.TargetMachine.new(cm=llvm.ee.CM_JITDEFAULT)
        self.datalayout = self.machine.target_data
        self.triple = self.machine.triple

        # system ptr size
        self.ptrsize = self.datalayout.pointer_size * 8

        # determine ABI
        if sys.platform.startswith('win32'):
            self.abi = ABI_WIN32[self.ptrsize]
        else:
            # FIXME
            self.abi = ABI_SYSTEMV[self.ptrsize]

        # align and sizeof
        # FIXME: verify that alignment is the same as sizeof?
        self._init_host_sizeofs()
        self.align_table = self.sizeof_table.copy()

    def _init_host_sizeofs(self):
        sizeofs = self.sizeof_table = {}
        tsb = self.typesystem.builtins

        # bool
        sizeofs[tsb.bool_type] = 8

        # char
        sizeofs[tsb.char_type] = 8
        sizeofs[tsb.uchar_type] = 8

        # integer
        int_sizes = 8, 16, 32, 64
        for i in int_sizes:
            sizeofs[tsb['int%d_type' % i]] = i
            sizeofs[tsb['uint%d_type' % i]] = i

        # real
        sizeofs[tsb.float_type] = 32
        sizeofs[tsb.double_type] = 64

    def get_align(self, ty):
        if isinstance(ty, llcc.typesystem.QualType):
            ty = ty.type
        if ty.is_pointer:
            return self.ptrsize
        return self.align_table[ty]

    def get_sizeof(self, ty):
        if isinstance(ty, llcc.typesystem.QualType):
            ty = ty.type
        if ty.is_pointer:
            return self.ptrsize
        return self.sizeof_table[ty]

