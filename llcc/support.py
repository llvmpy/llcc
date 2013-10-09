import re

#-------------------------------------------------------------------------------
# Renamer
#-------------------------------------------------------------------------------

rename_regex = re.compile('.*\.(\d+)$')

def rename_until(name, cond):
    while not cond(name):
        m = rename_regex.match(name)
        if m:
            ct = m.group(1)
            s = m.start(1)
            name = name[:s] + str(int(ct) + 1)
        else:
            name = '%s.0' % name
    return name

#-------------------------------------------------------------------------------
# Classifier
#-------------------------------------------------------------------------------

class Classifier(object):
    classes = ()    # a sequence of possible classes
    default = None  # default value of the classifier

    def __init__(self, value=None):
        if value is None:
            value = self.default
        self.set(value)

    def set(self, value):
        assert value in self.classes
        self.value = value

    def get(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, Classifier):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        return not (self == other)
