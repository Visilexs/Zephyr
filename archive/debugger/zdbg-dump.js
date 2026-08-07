// Dump a .zdbg sidecar: header, file table, line entries (summary + samples).
const fs = require("fs");
const b = fs.readFileSync(process.argv[2]);
let p = 0;
const u16 = () => { const v = b.readUInt16LE(p); p += 2; return v; };
const u32 = () => { const v = b.readUInt32LE(p); p += 4; return v; };
const u64 = () => { const v = b.readBigUInt64LE(p); p += 8; return v; };

const magic = b.toString("ascii", 0, 4); p = 4;
const ver = u16();
const imagebase = u64();
const textRva = u32();
const nfiles = u32();
const files = [];
for (let i = 0; i < nfiles; i++) { const len = u16(); files.push(b.toString("utf8", p, p + len)); p += len; }
const nlines = u32();
const lines = [];
for (let i = 0; i < nlines; i++) lines.push({ rva: u32(), file: u32(), line: u32() });
const nfuncs = u32();

console.log("magic:", magic, "ver:", ver, "imagebase: 0x" + imagebase.toString(16), "textRva:", textRva);
console.log("files:", files);
console.log("line entries:", nlines, "| funcs:", nfuncs);
const uniqLines = [...new Set(lines.map((l) => l.line))].sort((a, b) => a - b);
console.log("distinct source lines:", uniqLines.length, "range:", uniqLines[0], "..", uniqLines[uniqLines.length - 1]);
console.log("first 8:", lines.slice(0, 8).map((l) => `rva=0x${l.rva.toString(16)}→L${l.line}`).join("  "));
console.log("last 4:", lines.slice(-4).map((l) => `rva=0x${l.rva.toString(16)}→L${l.line}`).join("  "));
