from flask import Flask, request, jsonify
from models import db, User
import os

app = Flask(__name__)

DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "usermgmt")

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/health")
def health():
    return "OK", 200

from sqlalchemy import text  # ← ADD THIS import

@app.route("/db_check")
def db_check():
    try:
        db.session.execute(text("SELECT 1"))  # ← FIXED HERE
        return "DB Connected", 200
    except Exception as e:
        return str(e), 500

@app.route("/users", methods=["GET"])
def list_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email} for u in users])

@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    user = User(name=data["name"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User added", "user_id": user.id}), 201

@app.route("/add", methods=["GET", "POST"])
def add_user_form():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        try:
            user = User(name=name, email=email)
            db.session.add(user)
            db.session.commit()
            return f"<p>User {name} added successfully!</p><a href='/add'>Add Another</a>"
        except Exception as e:
            return f"<p>Error: {e}</p><a href='/add'>Try Again</a>"
    return '''
        <h2>Add New User</h2>
        <form method="post">
            <label>Name:</label><br><input type="text" name="name"><br><br>
            <label>Email:</label><br><input type="email" name="email"><br><br>
            <input type="submit" value="Add User">
        </form>
    '''


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)
