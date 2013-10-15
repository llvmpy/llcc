import os
from distutils.core import setup

setup(
    name = "llcc",
    author = "Continuum Analytics, Inc.",
    author_email = "support@continuum.io",
    url = "http://www.continuum.io",
    license = "BSD",
    description = "LLVM C ABI and interfacing extension",
    packages = [
        'llcc',
        'llcc.tests',
    ],
)

