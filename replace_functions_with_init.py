#!/bin/python3
import sys
import subprocess
import pandas as pd
import os

# run get_all_functions_that_should_be_init.py first
# this functions edits the linux source tree to replace all function declarations in out_file with __init 
src_linux = "/home/nick/IBM/linux_kernel/linux-git/arch/powerpc"
out_file = "out.txt"


def get_replacement_declaration(name, func_dec):
    assert name in func_dec, f"{name} somehow not in declaration: {fuc_dec}"
    # linux/include/linux/init.h tells us format for adding init to functions in source and headers
    i = func_dec.index(name)
    return (func_dec[:i] + "__init " + func_dec[i:], func_dec + " __init") 

def remove_special_characters(string):
    # sed treats * as special character, trying to escape with \* wasnt working
    # so we replace with another special character!
    string = string.replace("*", ".")
    return string

def run_replace_command(old, new, new_protoype):
    # don't change it in header files, bc thats what seems to be the current pattern
    # find . -type f -name "*.c" -exec sed -i 's/foo/bar/g' {} +
    old = remove_special_characters(old)
    # new = remove_special_characters(new)
    # new_protoype = remove_special_characters(new_protoype)
    assert '/' not in old and "/" not in new, f"/ somehow not allowed in {new} or {old}"
    command = f"find {src_linux} -type f -name '*.c' -exec sed -i 's/{old}/{new}/g' {{}} +"
    print("running command " + command)
    os.system(command)
    command = f"find {src_linux} -type f -name '*.h' -exec sed -i 's/{old};/{new_protoype};/g' {{}} +"
    print("running command " + command)
    os.system(command)

def declaration_is_in_source(pattern):
    command = f"grep -Fr {src_linux} --include \*.c --include \*.h -e '{pattern}'"
    print("running command " + command)
    result = os.system(command)
    #return true if declaration is in a C source file
    if result == 0:
        return True
    return False

if (len(sys.argv) > 1):
    file = sys.argv[1]
else:
    file = out_file 

df = pd.read_csv(file, sep='%')

for i, func in df.iterrows():
    print(func)
    replacement_declaration, replacement_header_declaration = get_replacement_declaration(func['name'], func['declaration'])
    #assert declaration_is_in_source(func['declaration']), f"Function {func['name']} with decallaration {func['declaration']} does not exist in a .c or .hfile" 
    if declaration_is_in_source(func['declaration']):
        run_replace_command(func['declaration'], replacement_declaration, replacement_header_declaration)