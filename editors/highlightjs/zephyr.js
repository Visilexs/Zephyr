// highlight.js language definition for Zephyr. Load after highlight.js:
//   hljs.registerLanguage("zephyr", zephyrLanguage)   (done below when hljs is global)
function zephyrLanguage(hljs) {
  const KEYWORDS = {
    keyword: "fn let var const struct enum impl interface type private test extern import as from if else match while for in step break continue return defer and or not",
    literal: "true false none",
    built_in: "print panic sqrt emit chr bits floatFromBits args readFile writeFile zeros assert abs min max pow syscall addr load8 load16 load32 load64 store8 store16 store32 store64 callPointer callSysV callSysVFloat dynamicImport stackPointer spawnThread parallelFor cpuCount",
    type: "int float bool str void i32 u8 f32 f64",
    variable: "self",
  };
  const INTERP = { className: "subst", begin: /\{/, end: /\}/, keywords: KEYWORDS, contains: [] };
  const ESCAPE = { className: "char.escape", begin: /\\(x[0-9A-Fa-f]{2}|[ntr0\\"'{}])/ };
  const STRINGS = {
    className: "string",
    variants: [
      { begin: /r"""/, end: /"""/ },
      { begin: /r"/, end: /"/, illegal: /\n/ },
      { begin: /"""/, end: /"""/, contains: [ESCAPE, INTERP] },
      { begin: /"/, end: /"/, illegal: /\n/, contains: [ESCAPE, INTERP] },
    ],
  };
  const NUMBER = {
    className: "number",
    variants: [
      { begin: /\b0x[0-9A-Fa-f_]+\b/ }, { begin: /\b0b[01_]+\b/ }, { begin: /\b0o[0-7_]+\b/ },
      { begin: /\b[0-9][0-9_]*(\.[0-9][0-9_]*)?([eE][+-]?[0-9]+)?\b/ },
    ],
  };
  const COMMENT_BLOCK = hljs.COMMENT(/\/\*/, /\*\//, { contains: ["self"] });
  INTERP.contains = [STRINGS, NUMBER, hljs.C_LINE_COMMENT_MODE];
  return {
    name: "Zephyr",
    aliases: ["zeph", "zp"],
    keywords: KEYWORDS,
    contains: [
      hljs.C_LINE_COMMENT_MODE,
      COMMENT_BLOCK,
      STRINGS,
      { className: "string", begin: /'(\\x[0-9A-Fa-f]{2}|\\.|[^\\'])'/ },
      NUMBER,
      { begin: [/\bfn/, /\s+/, /[A-Za-z_][A-Za-z0-9_]*/], beginScope: { 1: "keyword", 3: "title.function" } },
      { begin: [/\b(?:struct|enum|interface|type)/, /\s+/, /[A-Za-z_][A-Za-z0-9_]*/], beginScope: { 1: "keyword", 3: "title.class" } },
      { className: "variable.constant", begin: /\b[A-Z][A-Z0-9_]+\b/ },
      { className: "title.class", begin: /\b[A-Z][A-Za-z0-9_]*\b/ },
      { className: "title.function.invoke", begin: /\b[a-z_][A-Za-z0-9_]*(?=\s*\()/, keywords: KEYWORDS },
      { className: "operator", begin: /->|\.\.|\?/ },
    ],
  };
}
if (typeof hljs !== "undefined") hljs.registerLanguage("zephyr", zephyrLanguage);
if (typeof module !== "undefined") module.exports = zephyrLanguage;
