from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "hello"


if __name__ == "__main__":
    cert_path = '/cert.pem'
    key_path = '/key.pem'
    app.run(debug=True, host="0.0.0.0", port=8888,ssl_context=(cert_path, key_path))
