import os
from datetime import datetime

from flask import (
    Flask, render_template, redirect, url_for,
    request, session, flash
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite DB under /data so it’s easy to persist in Docker
db_url = os.environ.get("DATABASE_URL", "sqlite:////data/app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")
db_url = os.environ.get("DATABASE_URL", "sqlite:////data/app.db")


db = SQLAlchemy(app)

# Database
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    added_by = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    done = db.Column(db.Boolean, default=False)
    done_by = db.Column(db.String(50), nullable=True)
    done_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Item {self.id}: {self.text[:20]!r}>"


# Helpers
def get_username():
    return session.get("username")


def login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not get_username():
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


# Database initialisation
with app.app_context():
    os.makedirs("/data", exist_ok=True)
    db.create_all()



# Routes
@app.route("/", methods=["GET"])
def index():
    if get_username():
        return redirect(url_for("shopping_list"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a name.")
            return redirect(url_for("login"))

        # Super simple "user system", stores name in session
        session["username"] = name
        flash(f"Logged in as {name}")
        return redirect(url_for("shopping_list"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/list", methods=["GET"])
@login_required
def shopping_list():
    # Show incomplete first, then completed
    items = (
        Item.query.order_by(Item.done.asc(), Item.created_at.asc())
        .all()
    )
    return render_template("list.html", items=items, username=get_username())


@app.route("/items/add", methods=["POST"])
@login_required
def add_item():
    text = request.form.get("text", "").strip()
    if not text:
        flash("Item cannot be empty.")
        return redirect(url_for("shopping_list"))

    item = Item(
        text=text,
        added_by=get_username()
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for("shopping_list"))


@app.route("/items/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_item(item_id):
    item = Item.query.get_or_404(item_id)
    username = get_username()

    if not item.done:
        item.done = True
        item.done_by = username
        item.done_at = datetime.utcnow()
    else:
        item.done = False
        item.done_by = None
        item.done_at = None

    db.session.commit()
    return redirect(url_for("shopping_list"))


@app.route("/items/clear_done", methods=["POST"])
@login_required
def clear_done():
    Item.query.filter_by(done=True).delete()
    db.session.commit()
    flash("Cleared completed items.")
    return redirect(url_for("shopping_list"))


if __name__ == "__main__":
    # Debug
    app.run(host="0.0.0.0", port=5000, debug=True)
