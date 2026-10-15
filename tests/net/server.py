#!/usr/bin/env python3
"""Local servers for the std/net and std/http tests (no internet needed).

Starts, on 127.0.0.1 with kernel-chosen ports: a TCP echo server, a fake DNS
server (answers A queries for *.zephyr.test), and an HTTP/1.1 server with
Content-Length, chunked, close-delimited, SSE and slow endpoints. Given
CERT and KEY arguments it also serves the same endpoints over TLS. Prints
"echo dns http https" ports on one line (https is 0 without a cert), then
serves until stdin closes.
"""
import http.server
import socket
import socketserver
import ssl
import struct
import sys
import threading
import time


class Echo(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data = self.request.recv(65536)
            if not data:
                return
            self.request.sendall(data)


class Tcp(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def dns_server(sock):
    while True:
        data, peer = sock.recvfrom(4096)
        ident = data[:2]
        at, labels = 12, []
        while data[at]:
            labels.append(data[at + 1:at + 1 + data[at]].decode())
            at += data[at] + 1
        question = data[12:at + 5]
        name = ".".join(labels)
        if name.endswith("zephyr.test"):
            answer = b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + bytes([127, 0, 0, 1])
            answer += b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + bytes([10, 1, 2, 3])
            header = ident + b"\x81\x80" + struct.pack(">HHHH", 1, 2, 0, 0)
            sock.sendto(header + question + answer, peer)
        elif name == "silent.test":
            continue
        else:
            header = ident + b"\x81\x83" + struct.pack(">HHHH", 1, 0, 0, 0)
            sock.sendto(header + question, peer)


class Http(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def body(self):
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            out = b""
            while True:
                size = int(self.rfile.readline().strip().split(b";")[0], 16)
                if size == 0:
                    self.rfile.readline()
                    return out
                out += self.rfile.read(size)
                self.rfile.readline()
        return self.rfile.read(int(self.headers.get("Content-Length", "0")))

    def send_plain(self, status, text, extra=()):
        data = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(data)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def chunked(self, content_type, pieces, pause=0.0):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for piece in pieces:
            data = piece.encode()
            self.wfile.write(b"%x\r\n%s\r\n" % (len(data), data))
            self.wfile.flush()
            if pause:
                time.sleep(pause)
        self.wfile.write(b"0\r\n\r\n")

    def do_GET(self):
        self.route("GET", b"")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", "11")
        self.end_headers()

    def do_POST(self):
        self.route("POST", self.body())

    def do_PUT(self):
        self.route("PUT", self.body())

    def route(self, method, body):
        path = self.path
        if path == "/hello":
            self.send_plain(200, "hello world", [("X-Server", "zephyr-test")])
        elif path == "/echo":
            text = "%s %s|%s|%s" % (method, path, self.headers.get("X-Test", "-"), body.decode())
            self.send_plain(200, text)
        elif path == "/chunked":
            self.chunked("text/plain", ["first,", "second,", "third"])
        elif path == "/big":
            self.send_plain(200, "0123456789" * 30000)
        elif path == "/close":
            self.send_response(200)
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(b"until the end")
            self.close_connection = True
        elif path == "/sse":
            events = [
                ": a comment\n\n",
                "event: start\ndata: {\"n\": 1}\nid: 1\n\n",
                "data: line one\ndata: line two\n\n",
                "data:no space\r\n\r\n",
                "event: delta\ndata: {\"text\": \"Hel",
                "lo\"}\n\n",
                "data: [DONE]\n\n",
            ]
            self.chunked("text/event-stream", events, 0.01)
        elif path == "/slow":
            time.sleep(3)
            self.send_plain(200, "late")
        elif path == "/missing":
            self.send_plain(404, "no such thing")
        else:
            self.send_plain(500, "unknown path " + path)


def main():
    # clients that stop a stream early make the handler hit a broken pipe
    socketserver.BaseServer.handle_error = lambda self, request, address: None
    echo = Tcp(("127.0.0.1", 0), Echo)
    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns.bind(("127.0.0.1", 0))
    web = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Http)
    web.daemon_threads = True
    targets = [echo.serve_forever, lambda: dns_server(dns), web.serve_forever]
    secure_port = 0
    if len(sys.argv) == 3:
        secure = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Http)
        secure.daemon_threads = True
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(sys.argv[1], sys.argv[2])
        secure.socket = context.wrap_socket(secure.socket, server_side=True)
        secure_port = secure.server_address[1]
        targets.append(secure.serve_forever)
    for target in targets:
        threading.Thread(target=target, daemon=True).start()
    print(echo.server_address[1], dns.getsockname()[1], web.server_address[1], secure_port, flush=True)
    sys.stdin.read()


main()
