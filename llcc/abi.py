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

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, self.describe())

    def describe(self):
        return ''

class DirectArgInfo(ArgInfo):
    is_direct = True

    def __init__(self, coerce_type=None, offset=0):
        self.coerce_type = coerce_type
        self.offset = offset

    def describe(self):
        return 'type=%s offset=%s' % (self.coerce_type, self.offset)

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

    def __str__(self):
        buf = ['ArgInfo %s {' % type(self).__name__]
        buf.append('    return %s' % (self.return_info,)    )
        buf.append('    args:')
        for idx, arg in enumerate(self.arg_infos):
            buf.append('    %4d: %s' % (idx, arg))
        buf.append('}')
        return '\n'.join(buf)

#------------------------------------------------------------------------------
# X86-32 ABI Info
#------------------------------------------------------------------------------

class X86_32ABIInfo(ABIInfo):
    MIN_ABI_STACK_ALIGN = 4    # bytes


#------------------------------------------------------------------------------
# X86-64 ABI Info
#------------------------------------------------------------------------------


class X86_64ABIClasses(support.Classifier):
    # initializer in algorithm.  For padding and empty structures and unions.
    NO_CLASS    = 'no_class'
    # integers that fits into GP-register
    INTEGER     = 'integer'
    # floats, decimals, vectors fit into vector registers
    SSE         = 'sse'
    # upper bytes of vector register; MSB of 128-bits floats/decimal
    SSEUP       = 'sseup'
    # x87 FPU (long double's 64-bit mantissa)
    X87         = 'x87'
    # x87 FPU upper register (long double's 16-bit exponent + 48-bit padding)
    X87UP       = 'x87up'
    # complex long double
    COMPLEX_X87 = 'complex_x87'
    # stack memory
    MEMORY      = 'memory'

    classes = NO_CLASS, INTEGER, SSE, SSEUP, X87, X87UP, COMPLEX_X87, MEMORY
    default = NO_CLASS

class X86_64Classifier(object):
    honorsRevision0_98 = True

    def __init__(self, target, ty, offset):
        self.hi = self.lo = X86_64ABIClasses.NO_CLASS
        self._active_lo = offset < 64
        self.target = target
        self.type = ty
        self.offset = offset

    @property
    def current(self):
        if self._active_lo:
            return self.lo
        else:
            return self.hi

    @current.setter
    def current(self, val):
        if self._active_lo:
            self.lo = val
        else:
            self.hi = val

    def classify(self):
        self.current = X86_64ABIClasses.MEMORY
        # classify lo
        if self.type.is_void:
            self.current = X86_64ABIClasses.NO_CLASS
        elif self.type.is_scalar:
            if self.type.is_integer:
                if self.target.get_sizeof(self.type) > 64:
                    raise NotImplementedError
                else:
                    self.current = X86_64ABIClasses.INTEGER
            elif self.type.is_float:
                if self.target.get_sizeof(self.type) > 64:
                    raise NotImplementedError
                else:
                    self.current = X86_64ABIClasses.SSE
        elif self.type.is_pointer:
            self.current = X86_64ABIClasses.INTEGER
        elif self.type.is_struct:
            sizeof = self.target.get_sizeof(self.type)

            # larger than 4 eightbytes
            if sizeof > 4 * 8 * 8:
                return

            self.current = X86_64ABIClasses.NO_CLASS

            # classify each field
            for fieldname, fieldty in self.type.fields():
                fieldty = fieldty.type
                field_offset = self.type.get_field_offset(name=fieldname,
                                                   target=self.target)


                classifier = X86_64Classifier(self.target, fieldty,
                                              offset=field_offset)
                classifier.classify()
                fldhi, fldlo = classifier.hi, classifier.lo

                self.lo = self.merge(self.lo, fldlo)
                self.hi = self.merge(self.hi, fldhi)
                if self.lo is self.hi is X86_64ABIClasses.MEMORY:
                    break;

            self.postmerge(sizeof)

    def postmerge(self, sizeof):
        if self.hi is X86_64ABIClasses.MEMORY:
            self.lo = X86_64ABIClasses.MEMORY
        if (self.hi is X86_64ABIClasses.X87UP and
                self.lo is not X86_64ABIClasses.X87 and
                self.honorsRevision0_98):
            self.lo = X86_64ABIClasses.MEMORY
        if sizeof > 128 and (self.lo is not X86_64ABIClasses.SSE and
                             self.hi is not X86_64ABIClasses.SSEUP):
            self.lo = X86_64ABIClasses.MEMORY
        if (self.hi is X86_64ABIClasses.SSEUP and
                self.lo is not X86_64ABIClasses.SSE):
            self.hi = X86_64ABIClasses.SSE

    def merge(self, accum, field):
        assert accum is not X86_64ABIClasses.MEMORY
        assert accum is not X86_64ABIClasses.COMPLEX_X87

        if accum is field:
            return accum
        elif field in (X86_64ABIClasses.MEMORY,
                     X86_64ABIClasses.NO_CLASS):
            return field
        elif (accum is X86_64ABIClasses.INTEGER or
              field is X86_64ABIClasses.INTEGER):
            return X86_64ABIClasses.INTEGER
        elif (field in (X86_64ABIClasses.X87, X86_64ABIClasses.X87UP,
                        X86_64ABIClasses.COMPLEX_X87) or
              accum in (X86_64ABIClasses.X87, X86_64ABIClasses.X87UP)):
            return X86_64ABIClasses.MEMORY
        else:
            return X86_64ABIClasses.SSE


class X86_64ABIInfo(ABIInfo):
    '''This ABI is used by most opensource OSes, various *nix flavours
    
    AMD-64 ABI Ch 3.2.3
    Reference http://www.x86-64.org/documentation/abi.pdf
    '''
    MIN_ABI_STACK_ALIGN = 16   # bytes

    def classify_return_type(self, retty):
        if isinstance(retty, llcc.typesystem.QualType):
            retty = retty.type

        hi, lo = self.classify(retty, offset=0)

        if hi is lo is X86_64ABIClasses.NO_CLASS:
            return IgnoreArgInfo()

        assert False, 'TODO'

    def classify_argument_type(self, argty):
        if isinstance(argty, llcc.typesystem.QualType):
            argty = argty.type

        hi, lo = self.classify(argty, offset=0)
        print('argty', hi, lo)
        assert (not hi is X86_64ABIClasses.MEMORY or
                lo is X86_64ABIClasses.MEMORY)
        assert (not hi is X86_64ABIClasses.SSEUP or
                lo is X86_64ABIClasses.MEMORY.SSE)
        restype = None

        regct = 0       # GP-register needed
        ssect = 0       # SSE register needed

        # Lo class
        if lo is X86_64ABIClasses.NO_CLASS:
            if hi is X86_64ABIClasses.NO_CLASS:
                return IgnoreArgInfo()
        elif lo in (X86_64ABIClasses.X87, X86_64ABIClasses.COMPLEX_X87):
            assert False, 'TODO'
        elif lo in (X86_64ABIClasses.SSEUP, X86_64ABIClasses.X87UP):
            raise AssertionError("invalid ABI classification")
        elif lo is X86_64ABIClasses.INTEGER:
            regct += 1
            resty = self.get_integer_type(argty, offset=0)
            if (hi == X86_64ABIClasses.NO_CLASS and resty.is_scalar and
                resty.is_integer and resty.is_promotable):
                return ExtendArgInfo()
        elif lo is X86_64ABIClasses.SSE:
            ssect += 1
            resty = self.get_sse_type(argty, offset=0)

        # Hi class
        if hi is X86_64ABIClasses.NO_CLASS:
            pass
        elif hi is X86_64ABIClasses.SSE:
            highpart = self.get_sse_type(argty, offset=8)
            if lo is X86_64ABIClasses.NO_CLASS:
                return DirectArgInfo(highpart, offset=8)
        else:
            assert False, "TODO"

        return DirectArgInfo(coerce_type=resty)

    def classify(self, typ, offset):
        classifier = X86_64Classifier(self.target, typ, offset)
        classifier.classify()
        return classifier.hi, classifier.lo

    def get_integer_type(self, ty, offset):
        if offset == 0:
            if self.target.ptrsize == 64 and ty.is_pointer:
                return ty
            if (ty.is_scalar and ty.is_integer and
                (ty.bitwidth in (8, 16, 32) or ty.is_pointer)):
                return ty
        assert False, "TODO"

    def get_sse_type(self, ty, offset):
        if ty.is_scalar and (ty.is_float or ty.is_double):
            return ty

        ts = self.target.typesystem
        if ty.is_aggregate and len(ty) == 2:

            float_t = ts.get_float()
            floatat0 = ty.has_type_at_offset(float_t, offset=0,
                                             target=self.target)
            floatat4 = ty.has_type_at_offset(float_t, offset=4,
                                             target=self.target)
            if floatat0 and floatat4:
                vecty = ts.get_vector(ts.get_float(), 2)
                return vecty
        else:
            assert ty.is_struct
            assert all(ts.get_float() == fty
                       for fty in ty.fieldtypes())
            return

ABI_INFOS = {
    'SystemV/x86_64': X86_64ABIInfo
}
