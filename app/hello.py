from flask import Flask, escape, request, render_template

app = Flask(__name__)


@app.route("/")
@app.route("/index")
def hello():
    user = {"username": "Duan"}
    return render_template("index.html", title="Home", user=user)
