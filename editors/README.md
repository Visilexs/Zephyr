# Zephyr syntax highlighting

Definitions for the editors and viewers used with Zephyr, all following the
token rules in `docs/spec.md` §1.1: nested `/* */` comments, `"…{expr}…"`
interpolation and escapes, raw `r"…"` and multi-line `"""…"""` strings,
`'c'` byte literals, `0x`/`0b`/`0o` and `_`-separated numbers, keywords,
built-in types and functions.

| path | for |
|---|---|
| `vim/` | vim: syntax, filetype detection, 4-space indent and `//` comments |
| `micro/zephyr.yaml` | micro |
| `nano/zephyr.nanorc` | nano (interpolation isn't coloured: nano can't scope a rule to strings) |
| `sublime/Zephyr.sublime-syntax` | bat (and `less` through bat), Sublime Text |
| `textmate/Zephyr.tmLanguage.json` | GitHub's highlighter (via a github-linguist PR) and any TextMate-based editor (VS Code) |
| `highlightjs/zephyr.js` | highlight.js; `install.sh` adds it to pi's `/export` HTML |

```sh
./install.sh        # installs all of them for the current user; safe to re-run
```

pi's own terminal UI can't be extended: its highlighter is compiled into the
pi binary. pi-desk highlights Zephyr itself, including unlabeled code blocks
that look like Zephyr.
