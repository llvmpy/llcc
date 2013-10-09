'''
Provide C ABI information

Reference to 
- http://clang.llvm.org/doxygen/classclang_1_1ABIArgInfo.html
- http://clang.llvm.org/doxygen/CodeGen_2TargetInfo_8cpp_source.html
    See X86_32ABIInfo, computeInfo, classifyArgumentType
'''
from llcc import support
import llcc.typesystem

#-------------------------------------------------------------------------------
# ABI conventions
#-------------------------------------------------------------------------------

ABI_WIN32 = {32: 'Win32/x86',
             64: 'Win64/x86_64'}

ABI_SYSTEMV = {32: 'SystemV/x86',
               64: 'SystemV/x86_64'}

#-------------------------------------------------------------------------------
# ArgInfo
#-------------------------------------------------------------------------------

class ArgInfo(object):
    is_direct = False
    is_extend = False
    is_ignore = False
    is_indirect = False
    is_expand = False

    @property
    def can_have_coerce_to_type(self):
        return self.is_direct or self.is_extend

    @property
    def in_reg(self):
        return self.is_direct or self.is_extend or self.is_indirect

class DirectArgInfo(ArgInfo):
    is_direct = True

    def __init__(self, coerce_type=None, offset=0):
        self.coerce_type = coerce_type
        self.offset = offset

class ExtendArgInfo(ArgInfo):
    is_extend = True

    def __init__(self, coerce_type=None):
        self.coerce_type = coerce_type

class IgnoreArgInfo(ArgInfo):
    is_ignore = True

class IndirectArgInfo(ArgInfo):
    is_indirect = True

    def __init__(self, align=1, byval=False, realign=False):
        self.align = align
        self.byval = byval
        self.realign = realign

class ExpandArgInfo(ArgInfo):
    is_expand = True

#-------------------------------------------------------------------------------
# ABI Info
#-------------------------------------------------------------------------------

class ABIInfo(object):
    @staticmethod
    def get_class(abiname):
        '''Returns a ABIInfo subclass
        '''
        return ABI_INFOS[abiname]

    def __init__(self, target):
        self.target = target

    def compute_info(self, fnty):
        self.return_info = self.classify_return_type(fnty.return_type)
        self.arg_infos = []
        for a in fnty.args:
            info = self.classify_argument_type(a)
            self.arg_infos.append(info)

    def classify_return_type(self, retty):
        raise NotImplementedError

    def classify_argument_type(self, argty):
        raise NotImplementedError

#------------------------------------------------------------------------------
# X86-32 ABI Info
#------------------------------------------------------------------------------

class X86_32ABIInfo(ABIInfo):
    MIN_ABI_STACK_ALIGN = 4    # bytes


#------------------------------------------------------------------------------
# X86-64 ABI Info
#------------------------------------------------------------------------------


class X86_64ABIClasses(support.Classifier):
    NO_CLASS = 'no_class'
    INTEGER = 'integer'
    SSE = 'sse'
    SSEUP = 'sseup'
    X87 = 'x87'
    X87UP = 'x87up'
    COMPLEX_X87 = 'complex_x87'
    MEMORY = 'memory'

    classes = NO_CLASS, INTEGER, SSE, SSEUP, X87, X87UP, COMPLEX_X87, MEMORY
    default = 'no_class'

class X86_64ABIInfo(ABIInfo):
    '''AMD-64 ABI Ch 3.2.3
    Reference http://www.x86-64.org/documentation/abi.pdf
    '''
    MIN_ABI_STACK_ALIGN = 16   # bytes

    def classify_return_type(self, retty):
        if isinstance(retty, llcc.typesystem.QualType):
            retty = retty.type

        cls = self.classify(retty)
        print(retty, '->', cls)

    def classify_argument_type(self, argty):
        if isinstance(argty, llcc.typesystem.QualType):
            argty = argty.type

        cls = self.classify(argty)
        print(argty, '->', cls)

    def classify(self, ty):
        if ty.is_void:
            return X86_64ABIClasses.NO_CLASS
        elif ty.is_scalar:
            if ty.is_integer:
                return X86_64ABIClasses.INTEGER
            elif ty.is_float:
                return X86_64ABIClasses.SSE
        raise NotImplementedError(ty)

ABI_INFOS = {
    'SystemV/x86_64': X86_64ABIInfo
}
