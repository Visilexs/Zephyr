#!/bin/sh
# install.sh -- Zephyr syntax highlighting for the editors and viewers on
# this machine: vim, micro, nano, bat (and Sublime Text, which reads the same
# .sublime-syntax). Safe to re-run. pi-desk highlights Zephyr on its own.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"

# vim
for d in syntax ftdetect ftplugin; do
    mkdir -p "$HOME/.vim/$d"
    cp "$here/vim/$d/zephyr.vim" "$HOME/.vim/$d/zephyr.vim"
done
grep -qs "syntax on" "$HOME/.vimrc" || printf 'syntax on\nfiletype plugin indent on\n' >> "$HOME/.vimrc"
echo "vim:   ~/.vim/{syntax,ftdetect,ftplugin}/zephyr.vim"

# micro
mkdir -p "$cfg/micro/syntax"
cp "$here/micro/zephyr.yaml" "$cfg/micro/syntax/zephyr.yaml"
echo "micro: $cfg/micro/syntax/zephyr.yaml"

# nano
mkdir -p "$cfg/nano"
cp "$here/nano/zephyr.nanorc" "$cfg/nano/zephyr.nanorc"
line="include \"$cfg/nano/zephyr.nanorc\""
grep -qsF "$line" "$cfg/nano/nanorc" || echo "$line" >> "$cfg/nano/nanorc"
echo "nano:  $cfg/nano/zephyr.nanorc"

# bat (and less, when bat is the pager)
if command -v bat >/dev/null 2>&1; then
    mkdir -p "$(bat --config-dir)/syntaxes"
    cp "$here/sublime/Zephyr.sublime-syntax" "$(bat --config-dir)/syntaxes/"
    bat cache --build >/dev/null
    echo "bat:   $(bat --config-dir)/syntaxes/Zephyr.sublime-syntax"
fi

# Sublime Text, if present
for d in "$cfg/sublime-text/Packages/User" "$cfg/sublime-text-3/Packages/User"; do
    if [ -d "$d" ]; then cp "$here/sublime/Zephyr.sublime-syntax" "$d/"; echo "sublime: $d"; fi
done

# pi's /export HTML (re-run after updating pi; its terminal UI's highlighter
# is compiled into the binary and can't take new languages)
for dir in "$HOME"/.local/share/pi-v*/export-html; do
    [ -f "$dir/vendor/highlight.min.js" ] || continue
    if ! grep -q "zephyrLanguage" "$dir/vendor/highlight.min.js"; then
        cp -n "$dir/vendor/highlight.min.js" "$dir/vendor/highlight.min.js.before-zephyr"
        { echo; cat "$here/highlightjs/zephyr.js"; } >> "$dir/vendor/highlight.min.js"
    fi
    if ! grep -q "zeph: 'zephyr'" "$dir/template.js"; then
        cp -n "$dir/template.js" "$dir/template.js.before-zephyr"
        sed -i "s|py: 'python', rb: 'ruby', rs: 'rust',|py: 'python', rb: 'ruby', rs: 'rust', zeph: 'zephyr',|" "$dir/template.js"
    fi
    echo "pi:    $dir (HTML export)"
done
