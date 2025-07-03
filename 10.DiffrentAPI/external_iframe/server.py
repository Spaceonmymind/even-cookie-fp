from http.server import SimpleHTTPRequestHandler, HTTPServer

if __name__ == "__main__":
    print("External iframe: http://localhost:8001")
    HTTPServer(("localhost", 8001), SimpleHTTPRequestHandler).serve_forever()
