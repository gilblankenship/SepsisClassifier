"""Authentication blueprint for SepsisDx."""

from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

# Hardcoded user credentials (hashed)
USERS = {
    "mdc": {
        "password_hash": generate_password_hash("mdcstudio123"),
        "full_name": "MDC Studio",
        "role": "admin",
    },
}


def login_required(f):
    """Decorator that redirects unauthenticated users to the login page."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        user = USERS.get(username)
        if user and check_password_hash(user["password_hash"], password):
            session.permanent = True
            session["user"] = username
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            next_url = request.args.get("next") or request.form.get("next") or url_for("index")
            return redirect(next_url)

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
