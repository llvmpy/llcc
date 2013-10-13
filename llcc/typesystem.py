import weakref
import ctypes
from llcc import adt, support

#-------------------------------------------------------------------------------
# Types
#-------------------------------------------------------------------------------

class CType(object):
    is_void = False
    is_scalar = False
    is_aggregate = False
    is_vector = False
    is_array = False
    is_struct = False
    is_pointer = False
    is_function = False

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, self.describe())

    def describe(self):
        return '"please override"'

class CScalarType(CType):
    is_scalar = True
    is_integer = False
    is_decimal = False
    is_float = False

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '%s' % self.name

    def describe(self):
        return self.name

class CIntegerType(CScalarType):
    is_integer = True
    is_signed = False
    is_unsigned = False
    
    def __init__(self, name, bitwidth, promotable=False):
        self.name = name
        self.bitwidth = bitwidth
        self.is_promotable = promotable


class CSignedType(CIntegerType):
    is_signed = True

class CUnsignedType(CIntegerType):
    is_unsigned = True

class CFloatType(CScalarType):
    is_float = True

class CVoidType(CType):
    is_void = True

    def __init__(self):
        self.name = 'void'

    def __str__(self):
        return self.name

    def describe(self):
        return ''

class CPointerType(CType):
    is_pointer = True

    def __init__(self, basetype):
        self.basetype = QualType(basetype)

    def __eq__(self, other):
        return (isinstance(other, CPointerType) and
                self.basetype == other.basetype)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.basetype)

    def __str__(self):
        return '%s*' % self.basetype

    def describe(self):
        return str(self.basetype)

class CAggregateType(CType):
    is_aggregate = True

    def has_type_at_offset(self, ty, offset, target):
        if isinstance(ty, QualType):
            ty = ty.type
        off = 0
        for qualtype in self:
            t = qualtype.type
            if off > offset:
                break
            elif off == offset:
                return ty == t
            off += target.get_sizeof(t)
        return False

class CHomoType(CAggregateType):

    def __init__(self, basetype, size):
        self.basetype = QualType(basetype)
        self.size = size

    def __eq__(self, other):
        return (isinstance(other, CArray) and
                self.basetype == other.basetype and
                self.size == other.size)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.basetype, self.size))

    def __len__(self):
        return self.size

    def __iter__(self):
        return iter([self.basetype] * len(self))

    def __getitem__(self, i):
        if i < 0:
            i = len(self) + i
        if i >= len(self):
            raise IndexError(i)
        return self.basetype

class CArrayType(CHomoType):
    is_array = True
    
    def __str__(self):
        return '%s[%d]' % (self.basetype, self.size)

    def describe(self):
        return '[%s x %d]' % (self.basetype, self.size)

class CVectorType(CHomoType):
    is_vector = True
    
    def __str__(self):
        return '<%s x %d>' % (self.basetype, self.size)

    def describe(self):
        return '<%s x %d>' % (self.basetype, self.size)

class CStructType(CAggregateType):
    is_struct = True

    def __init__(self, name=''):
        self.name = name
        self.members = None

    def define(self, members):
        cvtmm = [(k, QualType(v)) for k, v in members]
        self.members = adt.OrderedAttrs(members)
        return self

    def undefine(self):
        self.members = None

    @property
    def is_defined(self):
        return self.members is not None

    def __len__(self):
        return len(self.members)

    def __iter__(self):
        return iter(self.members)

    def __str__(self):
        head = 'struct %s' % self.name
        if self.members is None:
            return head
        else:
            return '%s{%s}' % (head, self.describe_members())

    def __getitem__(self, i):
        return self.members[i]

    def describe_members(self):
        mms = ['%s %s' % (self.members[name], name) for name in self.members]
        return '; '.join(mms)

    def describe(self):
        return '%s %s' % (self.name, self.describe_members())

    def layout_equal(self, other):
        return all(self.members[a] == other.members[b]
                   for a, b in zip(self.members, other.members))

class CFunctionType(CType):
    is_function = True

    def __init__(self, return_type, args, is_vararg=False):
        self.return_type = QualType(return_type)
        self.args = tuple(QualType(a) for a in args)
        self.is_vararg = is_vararg

    def __eq__(self, other):
        if isinstance(other, CFunctionType):
            return (self.return_type == other.return_type and
                    all(a == b for a, b in zip(self.args, other.args)) and
                    self.is_vararg  and other.is_vararg)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.return_type, self.args, self.is_vararg))

    def describe(self):
        args = [str(a) for a in self.args]
        if self.is_vararg:
            args.append('...')
        return '%s(%s)' % (self.return_type, ', '.join(args))

    def __str__(self):
        return self.describe()

#-------------------------------------------------------------------------------
# Type System
#-------------------------------------------------------------------------------

class CTypeSystem(object):
    def __init__(self):
        self.builtins = adt.AttrDict()
        self.userstructs = adt.AttrDict()
        self.cmappings = {}

    def load_sys_independ_builtins(self):
        # specials
        self.builtins.void_type = CVoidType()
        self.builtins.bool_type  = CUnsignedType(name='_Bool', bitwidth=8,
                                                 promotable=True)
        # chars
        self.builtins.char_type  = CSignedType(name='char', bitwidth=8,
                                               promotable=True)
        self.builtins.uchar_type = CUnsignedType(name='unsigned char',
                                                 bitwidth=8, promotable=True)

        # signed integer
        self.builtins.int8_type  = CSignedType(name='int8_t', bitwidth=8,
                                               promotable=True)
        self.builtins.int16_type = CSignedType(name='int16_t', bitwidth=16,
                                               promotable=True)
        self.builtins.int32_type = CSignedType(name='int32_t', bitwidth=32)
        self.builtins.int64_type = CSignedType(name='int64_t', bitwidth=64)

        # unsigned integer
        self.builtins.uint8_type  = CUnsignedType(name='uint8_t', bitwidth=8,
                                                  promotable=True)
        self.builtins.uint16_type = CUnsignedType(name='uint16_t', bitwidth=16,
                                                  promotable=True)
        self.builtins.uint32_type = CUnsignedType(name='uint32_t', bitwidth=32)
        self.builtins.uint64_type = CUnsignedType(name='uint64_t', bitwidth=64)

        # real
        self.builtins.float_type = CFloatType(name='float')
        self.builtins.double_type = CFloatType(name='double')
        self.builtins.longdouble_type = CFloatType(name='long double')

        # create mapping to ctypes
        cm = {
            'void_type':    None,

            'bool_type':    ctypes.c_bool,

            'char_type':    ctypes.c_char,
            'uchar_type':   ctypes.c_byte,

            'int8_type':    ctypes.c_int8,
            'int16_type':   ctypes.c_int16,
            'int32_type':   ctypes.c_int32,
            'int64_type':   ctypes.c_int64,

            'uint8_type':   ctypes.c_uint8,
            'uint16_type':  ctypes.c_uint16,
            'uint32_type':  ctypes.c_uint32,
            'uint64_type':  ctypes.c_uint64,

            'float_type':   ctypes.c_float,
            'double_type':  ctypes.c_double,
            'longdouble_type': ctypes.c_longdouble,
        }

        for lt, ct in cm.items():
            self.cmappings[ct] = self.builtins[lt]
            
    def init_type_mapping(self, cmap):
        for lt, ct in cmap.items():
            self.builtins[lt] = self.cmappings[ct]

    def init_host_type_mapping(self):
        '''Initialize type mapping with host setting

        Use python ctypes as a guide
        '''
        self.load_sys_independ_builtins()
        cmap = {
            'int_type':       ctypes.c_int,
            'uint_type':      ctypes.c_uint,
            'short_type':     ctypes.c_short,
            'ushort_type':    ctypes.c_ushort,
            'long_type':      ctypes.c_long,
            'ulong_type':     ctypes.c_ulong,
            'longlong_type':  ctypes.c_longlong,
            'ulonglong_type': ctypes.c_ulonglong,
        }
        ptrsize = ctypes.sizeof(ctypes.c_void_p) * 8
        cmap['intptr_type'] = getattr(ctypes, 'c_int%d' % ptrsize)

        self.init_type_mapping(cmap)

    def get_function(self, ret, args, vararg=False):
        return QualType(CFunctionType(ret, args, vararg))

    def get_intptr(self):
        return QualType(self.builtins.intptr_type)

    def get_opaque_ptr(self):
        return self.get_pointer(self.get_void())

    def get_void(self):
        return QualType(self.builtins.void_type)

    def get_int(self, bits=None):
        if bits:
            return QualType(self.builtins['int%d_type' % bits])
        else:
            return QualType(self.builtins.int_type)

    def get_uint(self, bits=None):
        if bits:
            return QualType(self.builtins['uint%d_type' % bits])
        else:
            return QualType(self.builtins.uint_type)

    def get_char(self):
        return QualType(self.builtins.char_type)

    def get_uchar(self):
        return QualType(self.builtins.uchar_type)

    def get_short(self):
        return QualType(self.builtins.short_type)

    def get_ushort(self):
        return QualType(self.builtins.ushort_type)

    def get_long(self):
        return QualType(self.builtins.long_type)

    def get_ulong(self):
        return QualType(self.builtins.ulong_type)

    def get_longlong(self):
        return QualType(self.builtins.longlong_type)

    def get_ulonglong(self):
        return QualType(self.builtins.ulonglong_type)

    def get_float(self):
        return QualType(self.builtins.float_type)

    def get_double(self):
        return QualType(self.builtins.double_type)

    def get_longdouble(self):
        return QualType(self.builtins.longdouble_type)

    def get_array(self, ty, ct):
        return QualType(CArrayType(ty, ct))

    def get_struct(self, name, members=None):
        '''
        if members is None then creates a incomplete structure type.
        else creats a structure type with the given members.
        '''
        if name not in self.userstructs:
            st = self.userstructs[name] = CStructType(name)
        else:
            st = self.userstructs[name]

        if members is not None:
            st.define(members)

        return QualType(st)

    def insert_struct(self, name, members=None):
        '''
        Rename until a unique name is available.
        '''
        name = support.rename_until(name, lambda x: x not in self.userstructs)
        st = self.userstructs[name] = CStructType(name)
        if members is not None:
            st.define(members)
        return QualType(st)

    def get_unnamed_struct(self, members):
        return QualType(CStructType().define(members))

    def get_pointer(self, ty):
        return QualType(CPointerType(ty))

#-------------------------------------------------------------------------------
# Qualified Type
#-------------------------------------------------------------------------------

class Qualifiers(adt.FlagSet):
    CONST    = 'const'
    RESTRICT = 'restrict'
    VOLATILE = 'volatile'

    possibilities = CONST, RESTRICT, VOLATILE

class QualType(object):
    '''Qualified Type

    Ctor returns the same object if the `typ` parameter is am instance of
    QualType.
    '''
    def __new__(cls, typ):
        if isinstance(typ, QualType):
            return typ
        else:
            obj = object.__new__(cls)
            obj._init(typ)
            return obj

    def _init(self, typ):
        self.type = typ
        self.qualifiers = Qualifiers()

    def __eq__(self, other):
        if isinstance(other, QualType):
            return (self.type == other.type and
                    self.qualifiers == other.qualifiers)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.type, self.qualifiers))

    def __str__(self):
        if self.qualifiers:
            qs = '%s ' % ' '.join(str(x) for x in self.qualifiers)
        else:
            qs = ''
        return qs + str(self.type)

    def copy(self):
        qt = QualType(self.type)
        qt.qualifiers = self.qualifiers.copy()
        return qt

    def _with(self, qual):
        cloned = self.copy()
        cloned.qualifiers.add(qual)
        return cloned

    def _without(self, qual):
        cloned = self.copy()
        cloned.qualifiers.discard(qual)
        return cloned

    def with_const(self):
        return self._with(Qualifiers.CONST)

    def without_const(self):
        return self._without(Qualifiers.CONST)

    def with_restrict(self):
        return self._with(Qualifiers.RESTRICT)

    def without_restrict(self):
        return self._without(Qualifiers.RESTRICT)

    def with_volatile(self):
        return self._with(Qualifiers.VOLATILE)

    def without_volatile(self):
        return self._without(Qualifiers.VOLATILE)

