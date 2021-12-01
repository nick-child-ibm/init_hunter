#!/bin/python3
import sys
import subprocess
import pandas as pd
import re
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

def parse_grep(txt, seperator):
    # this function parses grep output of the format:
    # <file><seperator><line_no><seperator><source_code>
    # and returns file, line_no, source code
    x = re.findall(seperator+'\d+'+seperator, txt)
    arr = txt.split(x[0])
    file, use = arr[0], arr[1]
    l_numb = x[0].replace(seperator, "")
    use = use.replace(";", "")
    return [str(file), str(l_numb), str(use)]
def run_replace_command_multi_line(func):
    # these functions should
    # 1. exist
    #   a. check by finding line1 and line2 of the declaration, they should be next to each other
    # 2. replace
    #   a. insertion of __init should happen on line 1
    # 3. attempt to do normal conversion in case other header or source declaration exist
    expect_l1 = func["declaration"][:func["declaration"].index(func["name"]) - 1]
    expect_l2 = func["declaration"][func["declaration"].index(func["name"]):]
    single_line_version = func["declaration"].replace("\n", " ")
    # print 1 line around line 2 od multiline declaration, should include line 1
    command = f"grep -Frn {src_linux} --include \*.c --include \*.h -e '{expect_l2}' -1"
    print("Looking for multiline declaration: " + command)
    output = subprocess.check_output(command, shell=True).split(b'\n')
    assert len(output) >= 3, f'Could not find multiline function declaration of {func["name"]} in source' 
    for i in range(0,len(output), 4):
        # output is <file><seperator><line_no><seperator><source_code>
        # turn this into [<file>, <line_no>. <source>]
        before_line = parse_grep(output[i].decode('UTF-8'), '-')
        declaration_line = parse_grep(output[i+1].decode('UTF-8'), ":")
        # check if match is single line occurence
        print(f'working with {declaration_line[2]}\nshould equal {single_line_version} or {expect_l1} and {before_line[2]}={expect_l2}')
        if declaration_line[2] == single_line_version:
            # if we find a single line declaration of this function, handle it like a normal function
            replacement_declaration, replacement_header_declaration = get_replacement_declaration(func['name'], single_line_version)
            run_replace_command(single_line_version, replacement_declaration, replacement_header_declaration)
            assert not declaration_is_in_source(single_line_version), f"Failed to subsitute __init into {single_line_version}"
        elif declaration_line[2] == expect_l2 and before_line[2] == expect_l1:
            print("Found multiline declaration of " + func["name"])
            command = "sed -i '"+before_line[1]+"s/"+remove_special_characters(expect_l1)+"/"+expect_l1+" __init/' "+ before_line[0]
            os.system(command)
            print("replacing multiline of " + func["name"] + " with command " + command)
            # ensure subisitution was success
            with open(before_line[0]) as f:
                new_line = f.readlines()[int(before_line[1]) - 1]
                assert new_line == (expect_l1 + " __init\n") , "could not replace multiline of " + func["name"] + " with command " + command + "\n found: " + new_line
        else:
            assert False, f'Could not parse output {output}'
if (len(sys.argv) > 1):
    file = sys.argv[1]
else:
    file = out_file 

df = pd.read_csv(file, sep='%').drop_duplicates('name')


for i, func in df.iterrows():
    print(func)
    # in get_all_funcs_that_should_be_init.py we added some multiline function declarations
    # like:
    # int
    # foo void {
    # these appear in out data file as <line_1>\n<line_2>
    # grepping over multiple lines is hard so we will handle these
    # special cases differently
    if func["declaration"].find('\n') != -1:
            run_replace_command_multi_line(func)
    else:
        replacement_declaration, replacement_header_declaration = get_replacement_declaration(func['name'], func['declaration'])
        #assert declaration_is_in_source(func['declaration']), f"Function {func['name']} with decallaration {func['declaration']} does not exist in a .c or .hfile" 
        assert declaration_is_in_source(func['declaration']), f'cannot find {func["declaration"]} in source'
        run_replace_command(func['declaration'], replacement_declaration, replacement_header_declaration)
        # assert at leastthe declaration in the source has been changed
        assert  declaration_is_in_source(replacement_declaration), f'Failed to subsitute __init into {func["declaration"]}'