from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello k8s 3.0! Test demo flow Argo CD. Final version."

if __name__ == "__main__":
    app.run(host='0.0.0.0')