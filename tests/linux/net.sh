#!/usr/bin/env bash
# tests/linux/net.sh WORK -- std/net, std/http (plain and through libcurl) and
# HTTPS, against the local servers in tests/net/server.py (no internet).
# Builds each tests/net/*.zeph at baseline and -O2 with WORK/zc-linux and
# compares the output with its .expected file. The libcurl and TLS parts are
# skipped (with a note) when libcurl.so.4 or openssl is missing.
set -u
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="${1:?usage: net.sh WORK}"
zc="$work/zc-linux"
command -v python3 >/dev/null || { echo "net: no python3, skipped"; exit 0; }
tmp="$(mktemp -d "$work/net.XXXXXX")"
have_curl=0
if ldconfig -p 2>/dev/null | grep -q 'libcurl\.so\.4 ' || [ -e /usr/lib/libcurl.so.4 ] || [ -e /usr/lib/x86_64-linux-gnu/libcurl.so.4 ]; then have_curl=1; fi
server_args=()
if [ "$have_curl" = 1 ] && command -v openssl >/dev/null &&
   openssl req -x509 -newkey rsa:2048 -nodes -keyout "$tmp/key.pem" -out "$tmp/cert.pem" -days 1 \
       -subj /CN=localhost -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" >/dev/null 2>&1; then
    server_args=("$tmp/cert.pem" "$tmp/key.pem")
fi
mkfifo "$tmp/stdin"
python3 "$root/tests/net/server.py" "${server_args[@]}" <"$tmp/stdin" >"$tmp/ports" 2>"$tmp/server.log" &
server=$!
exec 7>"$tmp/stdin"            # holding the fifo open keeps the server alive
cleanup() { exec 7>&-; kill "$server" 2>/dev/null; wait "$server" 2>/dev/null; rm -rf "$tmp"; }
trap cleanup EXIT
for _ in $(seq 100); do [ -s "$tmp/ports" ] && break; sleep 0.1; done
read -r echo_port dns_port http_port https_port <"$tmp/ports" || { echo "net: server did not start"; cat "$tmp/server.log"; exit 1; }

failed=0
# check NAME EXPECTED ARGS...: build tests/net/NAME.zeph at both tiers and run it
check() {
    local name="$1" expected="$2" tier flag
    shift 2
    for tier in base O2; do
        flag=""
        [ "$tier" = O2 ] && flag="-O2"
        if ! timeout 300 "$zc" --linux $flag "$root/tests/net/$name.zeph" "$tmp/$name.$tier" >"$tmp/$name.$tier.log" 2>&1; then
            echo "FAIL net/$name:$tier (compile)"; cat "$tmp/$name.$tier.log"; failed=1; continue
        fi
        if ! timeout 60 "$tmp/$name.$tier" "$@" </dev/null >"$tmp/$name.$tier.out" 2>>"$tmp/$name.$tier.log"; then
            echo "FAIL net/$name:$tier ($*: exit $?)"; cat "$tmp/$name.$tier.log"; failed=1; continue
        fi
        if ! diff -u "$root/tests/net/$expected" "$tmp/$name.$tier.out"; then
            echo "FAIL net/$name:$tier ($*: output differs from $expected)"; failed=1; continue
        fi
        echo "ok   net/$name:$tier $*"
    done
}
check std_net std_net.expected "$echo_port" "$dns_port" "$http_port"
check std_http std_http.expected "$echo_port" "$dns_port" "$http_port"
if [ "$have_curl" = 1 ]; then
    check std_http std_http_curl.expected "$echo_port" "$dns_port" "$http_port" curl
else
    echo "note: libcurl.so.4 not found, libcurl transport not tested"
fi
if [ "$https_port" != 0 ]; then
    check std_https std_https.expected "$https_port" "$tmp/cert.pem"
else
    echo "note: no libcurl or openssl, https not tested"
fi
[ "$failed" = 0 ] && echo "net: all passed"
exit "$failed"
