import os
import random
import string

import psycopg
from flask import Flask, render_template, request, redirect, abort

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "urlshortener")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")


def get_connection():
    return psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(6) UNIQUE NOT NULL,
            original_url TEXT NOT NULL
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def get_client_ip():
    # Behind Nginx, the real visitor IP arrives in X-Forwarded-For.
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", short_url=None)


@app.route("/shorten", methods=["POST"])
def shorten():
    original_url = request.form.get("url", "").strip()
    if not original_url:
        return render_template("index.html", short_url=None, error="Please enter a URL")

    conn = get_connection()
    cur = conn.cursor()

    code = generate_code()
    # extremely small chance of collision; retry a few times if needed
    for _ in range(5):
        cur.execute("SELECT 1 FROM links WHERE short_code = %s", (code,))
        if cur.fetchone() is None:
            break
        code = generate_code()

    cur.execute(
        "INSERT INTO links (short_code, original_url) VALUES (%s, %s)",
        (code, original_url),
    )
    conn.commit()
    cur.close()
    conn.close()

    app.logger.info(f"Shortened {original_url} -> {code} for client {get_client_ip()}")

    short_url = request.host_url + code
    return render_template("index.html", short_url=short_url)


@app.route("/<short_code>", methods=["GET"])
def redirect_to_original(short_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT original_url FROM links WHERE short_code = %s", (short_code,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        abort(404)

    app.logger.info(f"Redirect {short_code} requested by client {get_client_ip()}")
    return redirect(row[0], code=302)


@app.route("/healthz", methods=["GET"])
def healthz():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return "OK", 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return "DB unreachable", 500


import time


def init_db_with_retry(retries=10, delay=2):
    for attempt in range(retries):
        try:
            init_db()
            return
        except Exception as e:
            app.logger.warning(f"DB not ready ({e}), retry {attempt + 1}/{retries}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to database after retries")


# Runs whether started via `python app.py` or via gunicorn
init_db_with_retry()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
