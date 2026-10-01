#!/usr/bin/env python3
"""Conservative scan: which struct types are never field-assigned after construction?
A write `.f =`, `.f +=` (any compound op) to a field name marks every struct that
has a field with that name as mutated, since types are not resolved here.
Usage: immutable_scan.py files...
"""
import re, sys
structs = {}
writes = set()
for path in sys.argv[1:]:
    text = open(path, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'(?m)^\s*(?:private\s+)?struct\s+(\w+)(?:\[[^\]]*\])?\s*\{([^}]*)\}', text):
        fields = re.findall(r'(\w+)\s*:', m.group(2))
        structs[(m.group(1), path)] = fields
    for m in re.finditer(r'\.(\w+)\s*(?:\[[^\]]*\]\s*)?(?:\+|-|\*|/|%|&|\||\^|<<|>>)?=(?!=)', text):
        writes.add(m.group(1))
immutable = [(n, p) for (n, p), f in structs.items() if not any(x in writes for x in f)]
print(f'{len(structs)} struct types, {len(immutable)} never field-assigned (conservative)')
for n, p in sorted(immutable): print('  immutable:', n, '(' + p + ')')
for (n, p), f in sorted(structs.items()):
    if (n, p) not in immutable: print('  mutated:  ', n, [x for x in f if x in writes], '(' + p + ')')
