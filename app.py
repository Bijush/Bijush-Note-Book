from flask import Flask, render_template, request, redirect, url_for
import os, json, markdown
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# ===========================
# ✅ Firebase Setup
# ===========================
if os.path.exists("serviceAccountKey.json"):
    cred = credentials.Certificate("serviceAccountKey.json")
else:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://note-book-464907-default-rtdb.firebaseio.com/'
})

ref = db.reference('/')
PAGE_SIZE = 10

# ===========================
# ✅ Main Route
# ===========================
@app.route("/", methods=["GET", "POST"])
def index():
    notes_ref = ref.child('notes')

    # 🔁 Handle POST (Add, Edit, Delete, Clear All)
    if request.method == "POST":
        if "clear_all" in request.form:
            notes_ref.delete()
            return redirect(url_for("index"))

        if "delete" in request.form:
            key = request.form["delete"]
            notes_ref.child(key).delete()
            return redirect(url_for("index"))

        note_text = request.form.get("note", "").strip()
        tag_text = request.form.get("tags", "").strip()
        tags = [t.strip() for t in tag_text.split(",")] if tag_text else []

        html_note = markdown.markdown(note_text, extensions=["fenced_code", "codehilite"])
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if "edit_id" in request.form:
            # ✏️ Editing existing note
            key = request.form["edit_id"]
            if note_text:
                notes_ref.child(key).update({
                    "raw": note_text,
                    "html": html_note,
                    "time": now,
                    "tags": tags or []
                })
            return redirect(url_for("index"))

        # ➕ Add new note
        if note_text:
            notes_ref.push({
                "raw": note_text,
                "html": html_note,
                "time": now,
                "tags": tags or []
            })
            return redirect(url_for("index"))

    # 🔍 Handle GET
    q = request.args.get('q', '').strip().lower()
    tag_filter = request.args.get('tag', '').strip().lower()
    last_key = request.args.get('last_key')

    # ⬇️ Fetch recent notes
    snapshot = notes_ref.order_by_key().limit_to_last(200).get() or {}
    notes = dict(snapshot)

    # 🔎 Search filter
    if q:
        notes = {k: v for k, v in notes.items() if q in v.get('raw', '').lower()}

    # 🏷️ Tag filter
    if tag_filter:
        notes = {
            k: v for k, v in notes.items()
            if tag_filter in [t.lower() for t in v.get("tags", [])]
        }

    # 📄 Pagination
    sorted_keys = sorted(notes.keys(), reverse=True)
    page_keys = sorted_keys[:PAGE_SIZE]
    page_notes = {k: notes[k] for k in page_keys}

    next_last_key = None
    if len(sorted_keys) > PAGE_SIZE:
        next_last_key = sorted_keys[PAGE_SIZE]

    # 🏷️ Collect all unique tags
    all_tags = set()
    for note in notes.values():
        for tag in note.get("tags", []):
            all_tags.add(tag.strip())

    return render_template("index.html",
        notes=page_notes,
        next_last_key=next_last_key,
        prev_key=last_key,
        q=q,
        all_tags=sorted(all_tags),
        selected_tag=tag_filter
    )

# ===========================
# ✅ Run App
# ===========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
