#!/usr/bin/env python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "¡Hola con HTTPS!"

if __name__ == "__main__":
    app.run(
        ssl_context=("localhost+3.pem", "localhost+3-key.pem"),
        host="0.0.0.0",
        port=11443
    )

