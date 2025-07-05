from flask import Flask, render_template_string, request, redirect, url_for
import json
import os
import markdown
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# ===========================
# ✅ Initialize Firebase Admin
# ===========================
if os.path.exists("serviceAccountKey.json"):
    cred = credentials.Certificate("serviceAccountKey.json")
else:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://note-book-464907-default-rtdb.firebaseio.com/'
})

ref = db.reference('/')  # Root

# ===========================
# ✅ HTML Template
# ===========================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>📓 Termux Notebook</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- ✅ Prism core CSS for syntax colors only -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.css" rel="stylesheet" />

    <style>
        body { background: #343541; color: #d1d5db; font-family: Arial, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        header { padding: 20px; background: #202123; text-align: center; font-size: 24px; font-weight: bold; color: #fff; border-bottom: 1px solid #444; }
        .search-bar { padding: 10px; background: #40414f; display: flex; }
        .search-bar input { flex: 1; padding: 8px; font-size: 16px; border-radius: 5px; border: none; outline: none; background: #343541; color: #fff; }
        .search-bar button { margin-left: 10px; background: #10a37f; border: none; color: white; padding: 8px 16px; font-size: 16px; border-radius: 5px; cursor: pointer; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .message { background: #444654; padding: 15px; border-radius: 10px; margin: 8px 0; word-wrap: break-word; }
        .code-container { position: relative; margin: 10px 0; }
        pre { padding: 30px 15px 15px 70px; background: #202123 !important; border-radius: 6px; overflow-x: auto; font-family: monospace; }
        code { background: none; } /* Let Prism show colors */
        .language-label { position: absolute; top: 8px; left: 8px; background: #4b5563; color: #fff; font-size: 12px; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
        .copy-code { position: absolute; top: 8px; right: 8px; background: #10a37f; border: none; color: white; padding: 4px 8px; font-size: 12px; border-radius: 4px; cursor: pointer; }
        .meta { font-size: 12px; color: #aaa; margin-top: 5px; }
        .delete-btn { background: #ef4444; border: none; color: white; padding: 4px 8px; font-size: 12px; border-radius: 3px; cursor: pointer; margin-left: 10px; }
        .clear-btn { background: #ef4444; border: none; color: white; padding: 6px 12px; font-size: 14px; border-radius: 5px; cursor: pointer; margin: 10px; align-self: flex-end; }
        .pagination { text-align: center; margin: 15px; }
        .pagination a { color: #10a37f; text-decoration: none; margin: 0 10px; }
        .input-area { display: flex; padding: 10px; background: #40414f; }
        textarea { flex: 1; resize: none; padding: 10px; font-size: 16px; border-radius: 5px; border: none; outline: none; background: #343541; color: #fff; }
        .send-btn { margin-left: 10px; background: #10a37f; border: none; color: white; padding: 10px 16px; font-size: 16px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
<header>📓 BIJUSH NOTE BOOK</header>

<form method="get" class="search-bar">
    <input type="text" name="q" placeholder="🔍 Search notes..." value="{{ q }}">
    <button type="submit">Search</button>
</form>

<div class="chat-container" id="chat">
    {% for key, note in notes.items() %}
    <div class="message">
        {{ note["html"] | safe }}
        <div class="meta">
            Saved: {{ note["time"] }}
            <form method="post" style="display:inline;">
                <input type="hidden" name="delete" value="{{ key }}">
                <button type="submit" class="delete-btn">Delete</button>
            </form>
        </div>
    </div>
    {% endfor %}

    <div class="pagination">
        {% if next_last_key %}
            <a href="/?last_key={{ next_last_key }}">Next Page ⏭️</a>
        {% endif %}
        {% if prev_key %}
            <a href="/">⬅️ First Page</a>
        {% endif %}
    </div>

    {% if notes %}
    <form method="post">
        <input type="hidden" name="clear_all" value="1">
        <button type="submit" class="clear-btn" onclick="return confirm('Clear ALL notes?')">Clear All</button>
    </form>
    {% endif %}
</div>

<form method="post" class="input-area">
    <textarea name="note" rows="3" placeholder="Write command, explanation, markdown..."></textarea>
    <button type="submit" class="send-btn">Save</button>
</form>

<!-- ✅ Prism core JS -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>

<script>
document.querySelectorAll('pre').forEach(function(pre) {
    const container = document.createElement('div');
    container.className = 'code-container';
    pre.parentNode.insertBefore(container, pre);
    container.appendChild(pre);

    let lang = 'code';
    const codeTag = pre.querySelector('code');
    if (codeTag && codeTag.className) {
        const match = codeTag.className.match(/language-(\\w+)/);
        if (match) {
            lang = match[1];
        }
    }

    const label = document.createElement('span');
    label.className = 'language-label';
    label.innerText = lang.toUpperCase();
    container.appendChild(label);

    const button = document.createElement('button');
    button.innerText = 'Copy';
    button.className = 'copy-code';
    container.appendChild(button);

    button.addEventListener('click', function() {
        const code = codeTag ? codeTag.innerText : pre.innerText;
        navigator.clipboard.writeText(code).then(() => {
            button.innerText = 'Copied!';
            setTimeout(() => button.innerText = 'Copy', 1000);
        });
    });
});

var chat = document.getElementById("chat");
chat.scrollTop = chat.scrollHeight;
</script>
</body>
</html>
"""

# ===========================
# ✅ Page limit
# ===========================
PAGE_SIZE = 10

# ===========================
# ✅ Main route
# ===========================
@app.route("/", methods=["GET", "POST"])
def index():
    notes_ref = ref.child('notes')

    if request.method == "POST":
        if "clear_all" in request.form:
            notes_ref.delete()
            return redirect(url_for("index"))

        if "delete" in request.form:
            key = request.form["delete"]
            notes_ref.child(key).delete()
            return redirect(url_for("index"))

        note = request.form["note"]
        if note.strip():
            html_note = markdown.markdown(note, extensions=["fenced_code", "codehilite"])
            new_note = {
                "raw": note.strip(),
                "html": html_note,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            notes_ref.push(new_note)
            return redirect(url_for("index"))

    q = request.args.get('q', '').strip().lower()
    last_key = request.args.get('last_key')
    query = notes_ref.order_by_key().limit_to_last(200)
    snapshot = query.get() or {}
    notes = dict(snapshot)

    if q:
        notes = {k: v for k, v in notes.items() if q in v.get('raw', '').lower()}

    sorted_keys = sorted(notes.keys(), reverse=True)
    page_keys = sorted_keys[:PAGE_SIZE]
    page_notes = {k: notes[k] for k in page_keys}

    next_last_key = None
    if len(sorted_keys) > PAGE_SIZE:
        next_last_key = sorted_keys[PAGE_SIZE]

    return render_template_string(HTML, notes=page_notes, next_last_key=next_last_key, prev_key=last_key, q=q)

# ===========================
# ✅ Run
# ===========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
