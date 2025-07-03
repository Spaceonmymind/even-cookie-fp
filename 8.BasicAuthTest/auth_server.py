from http.server import BaseHTTPRequestHandler, HTTPServer
import base64

USERNAME = "user"
PASSWORD = "pass"

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Welcome! Try /protected")
        elif self.path == "/protected":
            if self.headers.get('Authorization') == 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode():
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Access Granted!")
                print("AUTH OK")
            else:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="Test"')
                self.end_headers()
                self.wfile.write(b"Unauthorized")
                print("NO AUTH")
        elif self.path == "/main.html":
            with open("main.html", "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
        elif self.path == "/iframe.html":
            with open("iframe.html", "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print("🚀 Local Auth Server running at http://localhost:8000")
    HTTPServer(("localhost", 8000), AuthHandler).serve_forever()
