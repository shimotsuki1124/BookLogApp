from flask import Flask, render_template, request, redirect, url_for
import requests
import uuid
import json
import os

app = Flask(__name__)
DATA_DIR = "data"
READING_FILE = os.path.join(DATA_DIR, "reading.json")
FINISHED_FILE = os.path.join(DATA_DIR, "finished.json")
MEMO_FILE = os.path.join(DATA_DIR, "memo.json")

# Utility functions
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_id():
    return uuid.uuid4().hex

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["GET"])
def search():
    keyword = request.args.get("q")
    if not keyword:
        return render_template("index.html", books=[])
    response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={keyword}")
    items = response.json().get("items", [])
    books = []
    for item in items:
        info = item["volumeInfo"]
        books.append({
            "title": info.get("title", ""),
            "authors": ", ".join(info.get("authors", [])),
            "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
            "description": info.get("description", "")[:200],
            "pageCount": info.get("pageCount", 0)
        })
    return render_template("index.html", books=books)

@app.route("/add", methods=["POST"])
def add():
    os.makedirs(DATA_DIR, exist_ok=True)
    reading = load_json(READING_FILE)
    book = {
        "id": generate_id(),
        "title": request.form["title"],
        "author": request.form["author"],
        "thumbnail": request.form["thumbnail"],
        "description": request.form["description"],
        "page_count": int(request.form.get("pageCount", 0)),
        "current_page": 0,
        "progress": 0
    }
    reading.append(book)
    save_json(READING_FILE, reading)
    return redirect("/reading")

@app.route("/reading")
def reading():
    reading_books = load_json(READING_FILE)
    for book in reading_books:
        book["progress"] = int((book["current_page"] / book["page_count"]) * 100) if book["page_count"] else 0
    return render_template("reading.html", books=reading_books)

@app.route("/update/<book_id>", methods=["POST"])
def update(book_id):
    reading = load_json(READING_FILE)
    for book in reading:
        if book["id"] == book_id:
            book["current_page"] = int(request.form["current_page"])
            break
    save_json(READING_FILE, reading)
    return redirect("/reading")

@app.route("/finish/<book_id>", methods=["POST"])
def finish(book_id):
    reading = load_json(READING_FILE)
    finished = load_json(FINISHED_FILE)
    for book in reading:
        if book["id"] == book_id:
            book["finished_date"] = request.form.get("finished_date", "今日")
            finished.append(book)
            reading.remove(book)
            break
    save_json(READING_FILE, reading)
    save_json(FINISHED_FILE, finished)
    return redirect("/finished")

@app.route("/finished")
def finished():
    books = load_json(FINISHED_FILE)
    return render_template("finished.html", books=books)

@app.route("/memo/<book_id>", methods=["GET", "POST"])
def memo(book_id):
    memos = load_json(MEMO_FILE)
    if request.method == "POST":
        content = request.form["content"]
        memos.append({"id": generate_id(), "book_id": book_id, "content": content, "timestamp": "今日"})
        save_json(MEMO_FILE, memos)
    reading = load_json(READING_FILE)
    finished = load_json(FINISHED_FILE)
    book = next((b for b in reading + finished if b["id"] == book_id), None)
    book_memos = [m for m in memos if m["book_id"] == book_id]
    return render_template("memo.html", book=book, memos=book_memos)

@app.route("/delete_memo/<memo_id>", methods=["POST"])
def delete_memo(memo_id):
    memos = load_json(MEMO_FILE)
    memos = [m for m in memos if m["id"] != memo_id]
    save_json(MEMO_FILE, memos)
    return redirect(request.referrer or "/")

@app.route("/delete_reading/<book_id>", methods=["POST"])
def delete_reading(book_id):
    reading = load_json(READING_FILE)
    reading = [b for b in reading if b["id"] != book_id]
    save_json(READING_FILE, reading)
    return redirect("/reading")

@app.route("/delete_finished/<book_id>", methods=["POST"])
def delete_finished(book_id):
    remove_log = request.form.get("remove_log") == "on"
    finished = load_json(FINISHED_FILE)
    finished = [b for b in finished if b["id"] != book_id]
    save_json(FINISHED_FILE, finished)

    if remove_log:
        memos = load_json(MEMO_FILE)
        memos = [m for m in memos if m["book_id"] != book_id]
        save_json(MEMO_FILE, memos)

    return redirect("/finished")

@app.route("/logs")
def logs():
    return render_template("logs.html", logs=load_json(FINISHED_FILE))

@app.route("/delete_log/<book_id>", methods=["POST"])
def delete_log(book_id):
    finished = load_json(FINISHED_FILE)
    finished = [b for b in finished if b["id"] != book_id]
    save_json(FINISHED_FILE, finished)

    memos = load_json(MEMO_FILE)
    memos = [m for m in memos if m["book_id"] != book_id]
    save_json(MEMO_FILE, memos)

    return redirect("/logs")

if __name__ == "__main__":
    app.run(debug=True)
