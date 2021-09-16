#!/bin/bash

outputfile=foo.txt
#go download and build ctags, sorry too lazy for README
path_to_parser=/home/nick/my_bin/ctags-5.8/ctags
dirname=/home/nick/IBM/linux_kernel/linux-git/arch/powerpc/

find $dirname -type f -name '*.[ch]' -exec $path_to_parser -x --c-kinds=f {} ';' > foo.txt