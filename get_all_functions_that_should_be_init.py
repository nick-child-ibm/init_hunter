#!/bin/python3
import sys
import subprocess
import pandas as pd

#run get_functs.sh first
# this is a script that will, given a list of all of its functions,
# find out if it should be __init or not
# an __init funciton is one that is only called by other __init functions
src_linux = "/home/nick/IBM/linux_kernel/linux-git/arch/powerpc"
function_file = "foo.txt"
out_file = "out.txt"
reasoning_file = "reasoning.txt"


def add_to_reasoning_file(function, callers, file):
    with open(file, "a") as f:
        f.write(f"----------------------------------------------------------------\nfunc:\n{func['name']}\nspecifically:\n{func}\nFound to be called by inits:\n{actual_calling_funcs}\n\n")
def should_be_init(callers, should_be_inits):
    if len(callers) == 0:
        return False
    for i, func in callers.iterrows():
        if "__init" not in func['declaration'] and func['name'] not in should_be_inits['name']:
            print("returning false")
            return False
    print("returning true")
    return True

def filter_results(calling_funcs, database):
    actual_calling_funcs = pd.DataFrame(columns=['name', 'line', 'file', 'declaration'])
    for declaration in calling_funcs:
        declaration = declaration
        #matches = database.loc[database['declaration'].str.contains(declaration)]
        # if not database['declaration'].str.contains(declaration):
        results = database[database['declaration'].isin([declaration])]
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
    if loc_equal == -1:
        return False
    if loc_equal < loc_colon or loc_colon == -1:
        return True
    return False
def get_calling_funcs(func):
    #return a list of all the functions that call this function
    # and don't get a list of the function declaration itself
    #print(f"finding all calls to {func['name']} also defined as {func['declaration']}")
    calling_funcs = []
    #git grep -Fp -e "printCertInfo" --and --not -e "int printCertInfo(crypto_x509 *x509)"
    #output = subprocess.check_output(['git', '-C', src_linux, 'grep', '-Fp', '-e', func['name'], '--and', '--not', '-e', func['declaration'], '--', '*.c' ],  encoding='UTF-8')
    command = f'git -C {src_linux} grep -Fp -e "{func["name"]}" --and --not -e "{func["declaration"]}" -- "*.c"'
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
        #print("caller = " + str(caller))
        #print("use = " + str(use))
        calling_funcs.append(caller[caller.find("=")+1:])
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
        #print(f"adding {new_entry}")
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
    if '__init' not in func['declaration'] and 'inline' not in func['declaration'] and should_be_init(actual_calling_funcs, funcs_that_should_be_init):
        funcs_that_should_be_init = funcs_that_should_be_init.append(func)
        add_to_reasoning_file(func, actual_calling_funcs, reasoning_file)
        print(f"{func['name']} from {func['file']} should be init since it was only found to be called by {str(actual_calling_funcs['name'])}")

print(f"FOUND {str(len(funcs_that_should_be_init))} funtions that should be init:\n{str(funcs_that_should_be_init['name'])}")
# write to csv file
funcs_that_should_be_init.to_csv(out_file, sep='\t')