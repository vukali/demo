from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Welcome to Demo app! Test demo Harbor workflow. CI/CD, test down time"

if __name__ == "__main__":
    app.run(host='0.0.0.0')