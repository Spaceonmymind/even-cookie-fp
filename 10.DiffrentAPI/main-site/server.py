from http.server import SimpleHTTPRequestHandler, HTTPServer

if __name__ == "__main__":
    print("Main site: http://localhost:8000")
    HTTPServer(("localhost", 8000), SimpleHTTPRequestHandler).serve_forever()
