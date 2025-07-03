from http.server import HTTPServer, SimpleHTTPRequestHandler
import mimetypes

PORT = 8000

# Добавим MIME-тип для .jnlp
mimetypes.add_type('application/x-java-jnlp-file', '.jnlp')

class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Разрешаем запуск из iframe
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

if __name__ == "__main__":
    print(f"🚀 Сервер JNLP запущен на http://localhost:{PORT}")
    HTTPServer(('localhost', PORT), CustomHandler).serve_forever()
