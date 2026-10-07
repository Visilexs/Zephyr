#!/bin/sh
# linux_extern.sh -- extern fn on --linux (dynamic ELF, dlopen/dlsym, System V
# calls). Each tests/linux/*.zeph is built baseline and -O2, as an executable
# and as an .o linked with gcc, and its output compared with the .expected file.
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
printf 'extern void zephyrMain(void);\nint main(void) { zephyrMain(); return 0; }\n' > "$work/main.c"
failed=0
for source in "$root"/tests/linux/*.zeph; do
    name="$(basename "$source" .zeph)"
    for opt in "" -O2; do
        "$root/zc" $opt --linux --rt "$source" "$work/$name" && chmod +x "$work/$name"
        "$root/zc" $opt --linux --rt "$source" "$work/$name.o"
        gcc -no-pie "$work/$name.o" "$work/main.c" -o "$work/$name-linked"
        for program in "$work/$name" "$work/$name-linked"; do
            if "$program" | cmp -s - "$root/tests/linux/$name.expected"; then
                echo "ok   $name $opt $(basename "$program")"
            else
                echo "FAIL $name $opt $(basename "$program")"
                failed=1
            fi
        done
    done
done
exit $failed
