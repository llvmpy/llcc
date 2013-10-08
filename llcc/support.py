import re

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
