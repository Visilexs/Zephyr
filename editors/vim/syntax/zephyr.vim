" Vim syntax file for Zephyr (docs/spec.md §1.1)
if exists("b:current_syntax") | finish | endif

syn keyword zephyrKeyword fn let var const struct enum impl interface type private test extern import as from
syn keyword zephyrConditional if else match
syn keyword zephyrRepeat while for in step break continue
syn keyword zephyrStatement return defer
syn keyword zephyrOperatorWord and or not
syn keyword zephyrBoolean true false
syn keyword zephyrConstant none
syn keyword zephyrSelf self
syn keyword zephyrType int float bool str void i32 u8 f32 f64
syn keyword zephyrBuiltin print panic sqrt emit chr bits floatFromBits args readFile writeFile zeros assert abs min max pow
syn keyword zephyrBuiltin syscall addr load8 load16 load32 load64 store8 store16 store32 store64 callPointer callSysV callSysVFloat
syn keyword zephyrBuiltin dynamicImport stackPointer spawnThread parallelFor cpuCount

syn match zephyrUserType "\<[A-Z][A-Za-z0-9_]*\>"
syn match zephyrConstName "\<[A-Z][A-Z0-9_]\+\>"
syn match zephyrFuncDef "\<fn\s\+\zs[A-Za-z_][A-Za-z0-9_]*"
syn match zephyrFuncCall "\<[a-z_][A-Za-z0-9_]*\ze\s*("
syn match zephyrOperator "->\|\.\.\|?"

syn match zephyrNumber "\<0x[0-9A-Fa-f_]\+\>\|\<0b[01_]\+\>\|\<0o[0-7_]\+\>\|\<[0-9][0-9_]*\>"
syn match zephyrFloat "\<[0-9][0-9_]*\.[0-9][0-9_]*\([eE][+-]\=[0-9]\+\)\=\>\|\<[0-9]\+[eE][+-]\=[0-9]\+\>"
syn match zephyrChar "'\(\\x\x\x\|\\.\|[^\\']\)'"

syn match zephyrEscape contained "\\[ntr0\\\"'{}]\|\\x\x\x"
syn region zephyrInterp contained matchgroup=zephyrInterpDelim start="{" end="}" contains=TOP
syn region zephyrString start=+"+ skip=+\\\\\|\\"+ end=+"+ oneline contains=zephyrEscape,zephyrInterp
syn region zephyrString start=+"""+ end=+"""+ contains=zephyrEscape,zephyrInterp
syn region zephyrRawString start=+r"+ end=+"+ oneline
syn region zephyrRawString start=+r"""+ end=+"""+

syn keyword zephyrTodo contained TODO FIXME XXX NOTE
syn region zephyrComment start="//" end="$" contains=zephyrTodo,@Spell
syn region zephyrComment start="/\*" end="\*/" contains=zephyrComment,zephyrTodo,@Spell

hi def link zephyrKeyword Keyword
hi def link zephyrConditional Conditional
hi def link zephyrRepeat Repeat
hi def link zephyrStatement Statement
hi def link zephyrOperatorWord Operator
hi def link zephyrOperator Operator
hi def link zephyrBoolean Boolean
hi def link zephyrConstant Constant
hi def link zephyrSelf Special
hi def link zephyrType Type
hi def link zephyrUserType Type
hi def link zephyrConstName Constant
hi def link zephyrBuiltin Function
hi def link zephyrFuncDef Function
hi def link zephyrFuncCall Function
hi def link zephyrNumber Number
hi def link zephyrFloat Float
hi def link zephyrChar Character
hi def link zephyrString String
hi def link zephyrRawString String
hi def link zephyrEscape SpecialChar
hi def link zephyrInterpDelim Special
hi def link zephyrComment Comment
hi def link zephyrTodo Todo

let b:current_syntax = "zephyr"
