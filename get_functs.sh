#!/bin/bash


## This script will output all funtion names to a file
## you must have ctags and unifdef to run
## ctags is a program that can locate all functions
## unifdef can modify a file to remove preprocessor conditionals
## this is needed because ONE file (kup.h) was not getting parsed correctly

# since we will be editing the files (to remove some ifdefs) we will need to run git stash
#   after the script to return the input files back to how they were before (sorry)
# in other words, make sure `dirname` is a git repository and all current changes are commited

outputfile=foo.txt
#go download and build ctags, sorry too lazy for README
path_to_func_parser=ctags
#go download and build unifdef, a tool to remove ifdefs from a file
path_to_unifdef=unifdef
dirname=/home/nick/IBM/linux_kernel/linux-git/arch/powerpc/

# FYI some funtions, like those in <linux>/arch/powerpc/include/asm/kup.h are not appearing
# due to only one path of a preprocessor directive being parsed

# To solve this, we must first remove all the #ifdef __ASSEMBLY__ conditionals

# Step 1. for all files in the repository, assume __ASEMBLY__ is undefined
find $dirname -type f -name '*.[ch]' -exec $path_to_unifdef -m -U__ASSEMBLY__ {} ';'
# Step 2, with the modified source tree, find all functions and output to the output file
find $dirname -type f -name '*.[ch]' -exec $path_to_func_parser -x --c-kinds=f {} ';' > $outputfile
# Step 3, return the source tree to how it was
git -C $dirname stash