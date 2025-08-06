# web_app/server.py
# Простой сервер для локальной отладки web app
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = 8000

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def run_server():
    os.chdir('web_app') # Переходим в папку с index.html
    httpd = HTTPServer(('localhost', PORT), CORSRequestHandler)
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()