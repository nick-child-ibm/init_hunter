Hello,

# Nicks Cruddy __init Hunter!

The purpose of this project is to create a series of scripts that can identify functions in the linux source tree that should be labeled with the macro `__init` (defined in `<source>/include/linux/init.h`). 
`__init` functions are placed in the ".init.text" section of the executable. This data is free'd after booting the kernel. 
Functions that should be `__init` are functions that are only called by othe`__init` functions. With this assumption, I have created the following scripts:

 - `get_functs.sh` : Uses existing projects to find all the function declarations in a given source tree. Outputs into a csv file `foo.txt`
 - `get_all_functions_that_should_be_init.py` : Iterates over all the known functions found from `get_functs.sh` and uses `git grep -p` to find all the functions that call that function. If all the calling functions are `__init` than the function being called should also be `__init`. Functions that are in need of `__init`'ing are added to the output file `out.txt`. For debugging, the file `reasoning.txt` lists the functions that were found to call the functions in `out.txt`
  - `replace_functions_with_init.py` : Uses `sed -i` to change the function definition in both header and source files. This will change your linux source tree

## Steps to run stuff

Make sure you have a git clone of the linux source tree. Also, MAKE SURE ALL CHANGES ARE COMMITED BEFORE RUNNING `get_functs.sh`.

In order to run `get_functs.sh`, you will need 2 external projects: `ctags` and `unifdef`. Both of these were provided by my distro package collection (Ubuntu). `ctags` is used to find all the functions, `unifdef` is needed due to an issue where some functions were not being found due to `#ifdef __ASSEMBLY__` occurences. `unifdef` is a tool that is used to temporarily remove those preprocessor conditionals. `git stash` is used at the end of the script to return the `__ASSEMBLY__` bussiniss to as it was before, so make sure all your changes are commited before running this script.

Additionally, you will need to open `get_functs.sh` and add any arguments that match your situation, mainly change `dirname` to the path to where you want to get your functions from. Sorry, I am too lazy to add a config file (TODO)

In order to run `get_all_functions_that_should_be_init.py`, you will again need to set some variables to match your configuration. They are at the top of the file, the important one being `src_linux`. Note: This script does bare minimum when looking for __inits, there are likely much more functions that should be `__init`'ed'  see TODO.

In order to run `replace_functions_with_init.py`, again set `src_linux` as it was in `get_all_functions_that_should_be_init.py`. 

## Findings

As of the initial run, I have found 210 functions in `<src_linux>/arch/powerpc` that could be labeled with `__init`. I was able to build and test the new tree without errors.

It is a bit difficult to tell the section size differences since it seems that the `.init.text` section is always rounded up to the nearest page size.
I found this note in `arch/powerpc/kernel/vmlinux.lds.S` ".init.text might be RO so we must ensure this section ends on a page boundary" . But I  was able to see the `.text` section reduced by about 10 KB (yay).

## TODO

 - A config file would be nice
 - There is a large code section in `get_all_functions_that_should_be_init.py` that has been commented out. This was part of an effort to handle function usage that was not in the standard `function(args)` format. For example, functions can be passed as pointers to structs and other functions. In these cases it can be fishy trying to figure out who calls these functions. I gave it a shot but in the end I decided to just drop those cases (that work is what is commented out)

