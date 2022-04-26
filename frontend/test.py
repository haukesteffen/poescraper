#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import base64
import random

def estimate_item_price(): # Implement function that estimates the price. Needs a parameter later on (string)
    return random.randint(1,100)

class S(BaseHTTPRequestHandler):
    estimated_price = ''
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*') # todo das hier anpassen
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        converted = base64.b64decode(post_data)
        converted_dec = converted.decode('UTF-8') # Here is the item as a string
        estimated_price = str(estimate_item_price())
        response = bytes(converted_dec + " " + estimated_price, "utf-8")
        self._set_response()
        self.wfile.write(response)

def run(server_class=HTTPServer, handler_class=S, port=8081):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()