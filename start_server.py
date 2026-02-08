#!/usr/bin/env python3
"""简易HTTP服务器 - 双击运行即可启动网站"""
import http.server
import socketserver
import webbrowser
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
PORT = 8080

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"网站已启动: http://localhost:{PORT}")
    print("按 Ctrl+C 停止服务器")
    webbrowser.open(f"http://localhost:{PORT}")
    httpd.serve_forever()
