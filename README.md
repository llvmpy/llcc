# Low-Level C Compiler (LLCC)

A llvmpy extension for building C ABI comformant LLVM IR.

## Why?

LLVM provides a machine abstraction but not ABI abstaction, 
which is dependant on language, operating system and processor architecture.
This package aims to solve the ABI problem and provide convenient codegen
features for building common operations following the C specification.

## The Development Plan

The typesystem in LLVM provides machine types.  It is too low-level to carry
sufficient information for generating proper ABI for the C language.  LLCC
implements a minimal C typesystem.  Remember, there are more than one mapping
from a C type to a LLVM machine type.  To comform to the C-ABI, there will be
precall, postcall, prologue and epilogue code to pack/unpack arguments.

## Limitations

* No support for bit-fields
