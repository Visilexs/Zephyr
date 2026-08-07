// Host for a Zephyr wasm module. With --rt the module talks to the outside
// world only through env.write / env.exit; the print_* imports are the
// no-runtime fallback used when the module is built without --rt.
const fs = require('fs');

function fmt(v) {                      // match Zephyr's %.15g float printing
  if (!isFinite(v)) return v > 0 ? "inf" : (v < 0 ? "-inf" : "nan");
  let s = v.toPrecision(15);
  if (s.indexOf('e') < 0 && s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, '');
  return s;
}

class ExitSignal extends Error { constructor(code) { super('exit'); this.code = code } }

let mem = null;
const dec = new TextDecoder();

const imports = { env: {
  print_i64: v => console.log(v.toString()),
  print_f64: v => console.log(fmt(v)),
  print_bool: v => console.log(v ? 'true' : 'false'),
  write: (fd, ptr, len) => {
    const bytes = new Uint8Array(mem.buffer, Number(ptr), Number(len));
    const s = dec.decode(bytes);
    if (Number(fd) === 2) process.stderr.write(s); else process.stdout.write(s);
  },
  exit: code => { throw new ExitSignal(Number(code)) },
}};

const inst = new WebAssembly.Instance(
  new WebAssembly.Module(fs.readFileSync(process.argv[2])), imports);
mem = inst.exports.memory;
try {
  inst.exports.main();
} catch (e) {
  if (e instanceof ExitSignal) process.exit(e.code);
  throw e;
}
