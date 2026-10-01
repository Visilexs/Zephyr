#!/bin/sh
# Make zc's x86-64 assembly (zc --linux ... out.s) acceptable to GNU as:
# give memory-immediate forms an explicit size, and make .rdata allocatable.
sed -E 's/^(\s+)(cmp|add|sub|mov|and|or|xor|test) (\[[^]]*\]), (-?[0-9]+)\s*$/\1\2 qword ptr \3, \4/; s/^\.section \.rdata$/.section .rdata,"aw"/' "$1"
