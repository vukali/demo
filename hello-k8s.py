from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello k8s 3.0! test sync with argocd-> done & test auto images"


@app.route("/about")
def about():
    return """
        <h1>Welcome to the About Page</h1>
        <p>This is an example Flask app running on Kubernetes with Argocd and automatic image tagging!</p>
    """


@app.route("/details")
def details():
    return """
        <h1>Details</h1>
        <p>Here we can add information about your Kubernetes environment, CI/CD pipeline, and more!</p>
        <p>This is an advanced web application running on Kubernetes, utilizing Docker images.</p>
    """


@app.route("/api/info", methods=['GET'])
def api_info():
    data = {
        "version": "1.0.0",
        "status": "running",
        "message": "This is a sample API endpoint in Flask"
    }
    return jsonify(data)


@app.route("/submit", methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        return f"Form submitted successfully! Username: {username}, Email: {email}"
    return '''
        <form method="POST">
            Username: <input type="text" name="username"><br>
            Email: <input type="email" name="email"><br>
            <input type="submit" value="Submit">
        </form>
    '''


@app.route("/error")
def error():
    return "Oops, something went wrong! But don't worry, we're on it."

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)





# from flask import Flask

# app = Flask(__name__)

# @app.route("/")
# def hello():
#     return "Hello k8s 3.0! test sync with argocd-> done & test auto images"

# if __name__ == "__main__":
#     app.run(host='0.0.0.0')