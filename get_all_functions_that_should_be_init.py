#!/bin/python3
import sys
import subprocess
import pandas as pd
import os
import linecache

# run get_functs.sh first
# this is a script that will, given a list of all of its functions,
# find out if it should be __init or not
# an __init funciton is one that is only called by other __init functions
src_linux = "/home/nick/IBM/linux_kernel/linux-git/arch/powerpc"
function_file = "foo.txt"
out_file = "out.txt"
reasoning_file = "reasoning.txt"

def is_func_init(declaration, name):
    # unfortunately functions like "static int hash__init_new_context(struct mm_struct *mm)" exist
    # this function is not an __init but contains the pattern
    if declaration.count("__init") > name.count("__init"):
        return True
    return False

def is_bad_prototype(name, declaration):
        # special case, ctags does not capture multiline function prototypes
        # things like"
        #int
        #func() {}
        #get recorded as func()
        
        # if the "declaration" starts with the name then we are missing
        # return type and possiblly more information
        if (declaration.startswith(name)):
            return True
        return False
def fixup_bad_prototype(name, line_number, file, declaration):
    # attempt to read the line before the declaration and prepend relevant information to the declaration
    before_line = linecache.getline(file, int(line_number)-1)
    if before_line.isspace() or len(before_line) < 1:
        return declaration
    if before_line.endswith(';') or before_line.endswith('}') or before_line.startswith('#') or before_line.startswith('/'):
        return declaration
    return before_line + declaration

def add_to_reasoning_file(function, callers, file):
    with open(file, "a") as f:
        f.write(f"----------------------------------------------------------------\nfunc:\n{func['name']}\nspecifically:\n{func}\nFound to be called by inits:\n{actual_calling_funcs}\n\n")
def should_be_init(callers, should_be_inits):
    if len(callers) == 0:
        return False
    for i, func in callers.iterrows():
        if not is_func_init(func['declaration'], func['name']) and func['name'] not in should_be_inits['name']:
            print("returning false")
            return False
    print("returning true")
    return True

def filter_results(calling_funcs, database):
    actual_calling_funcs = pd.DataFrame(columns=['name', 'line', 'file', 'declaration'])
    for declaration in calling_funcs:
        #matches = database.loc[database['declaration'].str.contains(declaration)]
        # if not database['declaration'].str.contains(declaration):
        results = database[database['declaration'].str.contains(declaration, regex=False)]
        if len(results) != 0:
        #    print(f'Could not find {declaration} in database')
        #    print("should be adding " + results)
            actual_calling_funcs = actual_calling_funcs.append(results)
    actual_calling_funcs = actual_calling_funcs.drop_duplicates('name')
    print(actual_calling_funcs)
    return actual_calling_funcs


def is_valid_pair(caller, match):
    # good output of our hunt is
    # <file>=function that contains a match
    # <file>:use of match
    loc_colon = caller.find(":")
    loc_equal = caller.find("=")

    # if caller has no equal sign then it is not a calling function statemet
    if loc_equal == -1:
        return False
    # if the colon exists and it happens before the equal sign, not a calling statement
    if loc_equal > loc_colon and loc_colon != -1:
        return False

    # opposite should be true for the match
    loc_colon = match.find(":")
    loc_equal = match.find("=")

    if loc_colon == -1:
        return False
    if loc_colon > loc_equal and loc_equal != -1:
        return False
    
    return True 


# borrowed from https://stackoverflow.com/questions/2170900/get-first-list-index-containing-sub-string, thanks kennytm
def index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
              return i
    return -1

def get_calling_funcs(func):
    #return a list of all the functions that call this function
    # and don't get a list of the function declaration itself
    #print(f"finding all calls to {func['name']} also defined as {func['declaration']}")
    calling_funcs = []
    #git grep -Fp -e "printCertInfo" --and --not -e "int printCertInfo(crypto_x509 *x509)"
    #output = subprocess.check_output(['git', '-C', src_linux, 'grep', '-Fp', '-e', func['name'], '--and', '--not', '-e', func['declaration'], '--', '*.c' ],  encoding='UTF-8')
    # some functions (like setup_kup) are actually only called inside header files... so search in headers too
    command = f'git -C {src_linux} grep -Fp -e "{func["name"]}" --and --not -e "{func["declaration"][func["declaration"].index(func["name"]):]}" -- "*.c" "*.h"'
    print("running command " + command)
    cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    output = (cmd.stdout.read()).decode('utf-8')
    print(f"total out is \n{output}")
    out_list = output.splitlines()
    print("list is " + str(out_list));
    i = 0
    while i  < len(out_list) - 1:
        caller, use = out_list[i], out_list[i+1]
        if (not is_valid_pair(caller, use)):
            i += 1
            continue
        # account for function pointers assignments and function name being used in a bigger function name 
        # ex: mmu_hash_ops.hpte_insert  = pSeries_lpar_hpte_insert;
        # ex: .open  = debugfs_timings_open,
        # and:
        # ex: when looking for use of kvmppc_mmu_flush_segment, dont add kvmppc_mmu_flush_segments calls
        elif  func["name"] +'(' not in use:
            print(f'disregarding {func["name"]} since use: {use} is too confusing')
            # temporary just give up, INOW don't try to investigate `func` any further TODO
            return []
            # if func['name'] + ',' in use or func['name'] + ';' in use:
            #     alias = ""
            #     # this case could be used in several ways
            #     #   1. if the function is assigned to a field of a struct
            #     #   2. if a function is passed as a function argument to another function

            #     # for case 1, check for function alias as .<alias> = <og_function >; or .<alias> = <og_function >,
            #     # for case 2, check for function alias as <alias>(<og_function>, ...)
            #     words = use.split()
            #     func_i = index_containing_substring(words, func["name"])
            #     assert func_i >= 0, f'Could not find {func["name"]} in {use}'
            #     #if case 2, (could also be case 1)
            #     if ',' in words[func_i]:
            #         # work backwords until you find the function that takes our function as an arg
            #         index = func_i
            #         while index >= 0:
            #             if '(' in words[index]:
            #                 alias = words[index][:words[index].find('(')]
            #                 break
            #             index -= 1
            #         print("COULD NO GET ALIAS, alias is " + alias + " with len " + str(len(alias)))
            #     # else case 1
            #     if len(alias) == 0:
            #         #alias is word before the equal sign
            #         after_i = index_containing_substring(words, "=")
            #         if after_i >= 0:
            #          print("ERROR: could not find '=' in " + use)
            #         else:  
            #             alias = words[after_i - 1]
            #             if alias[0] == '.':
            #                 alias = alias[1:]
            #             elif '->' in alias:
            #                 alias = alias[2:]
            #     if len(alias.strip()) != 0:
            #         print("ERROR: alias name from " + use + " could not be extracted")
            #     else:
            #     # command = f'git -C {src_linux} grep -Fp -e "{alias}" --and --not -e "{use}" -- "*.c" "*.h"'
            #     # print(f'running bonus command for alias {alias} of original func {func["name"]} : {command}')
            #     # cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            #     # output = (cmd.stdout.read()).decode('utf-8')
            #     # print(f"total out is \n{output}")
            #     # out_list.append(output.splitlines())
            #     # print("new list is " + str(out_list));

            #     # treat these cases as a caller of the original function name
            #     # consider later, we are appending the function name not declaration
            #         calling_funcs.append(alias)
            # # else this "use" is not an actual use of the function
            # else:
            #     i += 2
            #     continue
        #print("caller = " + str(caller))
        #print("use = " + str(use))
        calling_funcs.append(caller[caller.find("=")+1:])
        # if next entry is another call in the same function
        # only iterate once
        if i+2 < len(out_list) and is_valid_pair(caller, out_list[i+2]):
            print(f'double call in {caller} and {out_list[i+2]}')
            #use the same caller next time
            out_list[i+1] = caller
            i += 1
        # else skip to next function that calls
        else:
            i += 2
    print(f"functions that call {func['name']} are {str(calling_funcs)}")
    return calling_funcs


if (len(sys.argv) > 1):
    func_file = sys.argv[1]
else:
    func_file = function_file 

# [function, line number, file, declaration]
matrix = []
with open(func_file) as f:
    for line in f:
        new_entry = []
        splitz = line.split()
        new_entry.append(splitz[0])
        new_entry += (splitz[2:4])
        new_entry.append(' '.join(splitz[4:]))
        # check that we have a full function declaration and all its info
        # if not, we will try to reoover the relevant missing data
        if is_bad_prototype(new_entry[0], new_entry[3]):
            #reassign declaration to better version
            new_entry[3] = fixup_bad_prototype(new_entry[0], new_entry[1], new_entry[2], new_entry[3])
        
        matrix.append(new_entry)

df = pd.DataFrame(matrix, columns=['name', 'line', 'file', 'declaration'])
print(f'shape is {str(df.shape)}')

#remove old data file before appending
if os.path.isfile(reasoning_file):
    os.remove(reasoning_file)

funcs_that_should_be_init = pd.DataFrame(columns=['name', 'line', 'file', 'declaration'])
for index, func in df.iterrows():
    # get all calling functions
    calling_funcs = get_calling_funcs(func)
    # translate into a data frame, also helps filter non functions
    print(f"---------------------------------\nUSING {func['name']} is called by:\n{calling_funcs}\n==============")
    actual_calling_funcs = filter_results(calling_funcs, df)

    # if functions that call are __init than mark as should be init
    if not is_func_init(func['declaration'], func['name']) and 'inline' not in func['declaration'] and '__ref' not in func['declaration']  and should_be_init(actual_calling_funcs, funcs_that_should_be_init):
        funcs_that_should_be_init = funcs_that_should_be_init.append(func)
        add_to_reasoning_file(func, actual_calling_funcs, reasoning_file)
        print(f"{func['name']} from {func['file']} should be init since it was only found to be called by {str(actual_calling_funcs['name'])}")

print(f"FOUND {str(len(funcs_that_should_be_init))} funtions that should be init:\n{str(funcs_that_should_be_init['name'])}")
# write to csv file
funcs_that_should_be_init.to_csv(out_file, sep='%', index=False)