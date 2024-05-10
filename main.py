from http.server import BaseHTTPRequestHandler, HTTPServer
from subprocess import STDOUT, Popen, PIPE
from pathlib import Path
from datetime import datetime
import socket

def build_site():
    try:
        jekyll = Popen(["bundle exec jekyll build --trace"], shell=True)
        jekyll.wait(180)
        aws_cmds = Popen(["aws s3 sync _site/ s3://troop-website/ --delete"], shell=True)
        aws_cmds.wait(60)
        aws_cmds = Popen(["aws cloudfront create-invalidation --distribution-id=E2G8PJQQYCCCA6 --paths /"], shell=True)
        aws_cmds.wait(60)
    except TimeoutError:
        return False, 412, "Check Logs"

    if jekyll.returncode != 0:
        return False, 503, "Check Logs"
    return True, 201, "Check Logs"

class BuildWebhook(BaseHTTPRequestHandler):
    def do_POST(self):
        print("Got request to build.")
        success, code, fname = build_site()
        if success:
            self.send_response(code)
            print("Build completed.")
        else:
            self.send_error(code)
            print(f"Build failed. {code}")

        self.end_headers()

class IPV6HTTPServer(HTTPServer):
    address_family = socket.AF_INET6

if __name__ == "__main__":
    server = IPV6HTTPServer(("::", 9090), BuildWebhook)
    print("Server starting...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

    print("Server stopped.")
