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
    is_array = False
    is_struct = False
    is_pointer = False

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, self.describe())

    def describe(self):
        return '"please override"'

class CScalarType(CType):
    is_scalar = True

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '%s' % self.name

    def describe(self):
        return self.name

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

    def __str__(self):
        return '%s*' % self.basetype

    def describe(self):
        return str(self.basetype)

class CAggregateType(CType):
    is_aggregate = True

class CArrayType(CAggregateType):
    is_array = True

    def __init__(self, basetype, size):
        self.basetype = QualType(basetype)
        self.size = size

    def __eq__(self, other):
        return (isinstance(other, CArray) and
                self.basetype == other.basetype and
                self.size == other.size)

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return '%s[%d]' % (self.basetype, self.size)

    def describe(self):
        return '%s x %d' % (self.basetype, self.size)

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

    def describe_members(self):
        mms = ['%s %s' % (self.members[name], name) for name in self.members]
        return '; '.join(mms)

    def describe(self):
        return '%s %s' % (self.name, self.describe_members())

    def layout_equal(self, other):
        return all(self.members[a] == other.members[b]
                   for a, b in zip(self.members, other.members))

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

        # signed integer
        self.builtins.int8_type  = CScalarType(name='int8_t')
        self.builtins.int16_type = CScalarType(name='int16_t')
        self.builtins.int32_type = CScalarType(name='int32_t')
        self.builtins.int64_type = CScalarType(name='int64_t')

        # unsigned integer
        self.builtins.uint8_type  = CScalarType(name='uint8_t')
        self.builtins.uint16_type = CScalarType(name='uint16_t')
        self.builtins.uint32_type = CScalarType(name='uint32_t')
        self.builtins.uint64_type = CScalarType(name='uint64_t')

        # real
        self.builtins.float_type = CScalarType(name='float')
        self.builtins.double_type = CScalarType(name='double')
        self.builtins.longdouble_type = CScalarType(name='long double')

        # create mapping to ctypes
        cm = {
            'void_type': None,

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

    def init_with_ctypes(self):
        self.load_sys_independ_builtins()
        cm = {
            'int_type':       ctypes.c_int,
            'uint_type':      ctypes.c_uint,
            'long_type':      ctypes.c_long,
            'ulong_type':     ctypes.c_ulong,
            'longlong_type':  ctypes.c_longlong,
            'ulonglong_type': ctypes.c_ulonglong,
        }
        for lt, ct in cm.items():
            self.builtins[lt] = self.cmappings[ct]

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

    def get_long(self, bits=None):
        if bits:
            return QualType(self.builtins['long_type'])
        else:
            return QualType(self.builtins.long_type)

    def get_ulong(self, bits=None):
        if bits:
            return QualType(self.builtins['ulong_type'])
        else:
            return QualType(self.builtins.long_type)

    def get_longlong(self, bits=None):
        if bits:
            return QualType(self.builtins['longlong_type'])
        else:
            return QualType(self.builtins.longlong_type)

    def get_ulonglong(self, bits=None):
        if bits:
            return QualType(self.builtins['ulonglong_type'])
        else:
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
    possibilities = 'const', 'restrict', 'volatile', 'register'

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

    def __str__(self):
        if self.qualifiers:
            qs = '%s ' % self.qualifiers
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
        return self._with('const')

    def without_const(self):
        return self._without('const')

    def with_restrict(self):
        return self._with('restrict')

    def without_restrict(self):
        return self._without('restrict')
