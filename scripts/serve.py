#!/usr/bin/env python3
"""
serve.py — 本地预览服务器

Windows 上 Python 自带的 http.server 会把 .css/.js 的 MIME 类型报成
application/x-css、application/x-js（读注册表导致的），Chrome 会拒绝加载样式。
这里显式指定正确的类型。

用法：
    python scripts/serve.py [端口]
然后浏览器打开 http://127.0.0.1:8000/
"""
import os
import sys
import functools
import http.server
import socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

MIME = {
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.mjs': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.xml': 'application/xml; charset=utf-8',
    '.txt': 'text/plain; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.pdf': 'application/pdf',
    '.zip': 'application/zip',
    '.bin': 'application/octet-stream',
    '.woff2': 'font/woff2',
}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME}

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        """404 时返回仓库根目录的 404.html，跟 GitHub Pages 行为一致。
        这样 404 里的旧网址跳转表在本地也能测。"""
        if code == 404:
            try:
                with open(os.path.join(ROOT, '404.html'), 'rb') as f:
                    body = f.read()
            except OSError:
                return super().send_error(code, message, explain)
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)
            return
        return super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        pass          # 安静模式


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    handler = functools.partial(Handler, directory=ROOT)
    with Server(('127.0.0.1', PORT), handler) as httpd:
        print('预览地址: http://127.0.0.1:%d/' % PORT)
        print('根目录  : %s' % ROOT)
        print('Ctrl+C 退出')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')
