from pprint import pformat
from collections import MutableMapping, MutableSet, Sequence

class AttrDict(MutableMapping):
    __slots__ = '__kv'
    def __init__(self, dic={}):
        self.__kv = dic.copy()

    def __getattr__(self, k):
        return self.__kv[k]

    def __setattr__(self, k, v):
        if k == '_AttrDict__kv':
            return super(AttrDict, self).__setattr__(k, v)
        self.__kv[k] = v

    def __getitem__(self, k):
        return self.__kv[k]

    def __setitem__(self, k, v):
        self.__kv[k] = v

    def __iter__(self):
        return iter(self.__kv)

    def __delitem__(self):
        del self.__kv[k]

    def __len__(self):
        return len(self.__kv)

    def __repr__(self):
        return pformat(self.__kv)

class OrderedAttrs(Sequence):
    __slots__ = '__seq', '__kv'
    def __init__(self, pairs):
        self.__seq = tuple(k for k, _ in pairs)
        self.__kv = dict(pairs)

    def __getattr__(self, k):
        return self.__kv[k]

    def __getitem__(self, k):
        if isinstance(k, int):
            k = self.__seq[k]
        return self.__kv[k]

    def __iter__(self):
        return iter(self.__seq)

    def __len__(self):
        return len(self.__seq)

class FlagSet(MutableSet):
    '''Represent a set of flags.
    Overide possibilities for defining possible flags.
    '''
    possibilities = ()

    def __init__(self):
        self.flags = [False] * len(self.possibilities)

    def add(self, val):
        i = self.possibilities.index(val)
        self.flags[i] = True

    def discard(self, val):
        i = self.possibilities.index(val)
        self.flags[i] = False

    def __contains__(self, val):
        i = self.possibilities.index(val)
        return self.flags[val]

    def __len__(self):
        '''Not very useful for this class.
        '''
        ct = 0
        for f in self.flags:
            if f:
                ct += 1
        return ct

    def __iter__(self):
        return iter(self.possibilities[i]
                    for i, v in enumerate(self.flags)
                    if v)

    def copy(self):
        fs = type(self)()
        fs.flags = list(self.flags)
        return fs

    def __str__(self):
        return str(tuple(self))

