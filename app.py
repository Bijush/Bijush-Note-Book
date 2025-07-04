from flask import Flask, render_template_string, request, redirect, url_for
import os
import json
import markdown
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Initialize Firebase
if os.path.exists("serviceAccountKey.json"):
    cred = credentials.Certificate("serviceAccountKey.json")
else:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
firebase_admin.initialize_app(cred)
db = firestore.client()
notes_ref = db.collection("notes")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>📓 Termux Notebook</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/pygments/2.17.2/styles/monokai.min.css" rel="stylesheet">
    <style>
        body { background-color: #343541; color: #d1d5db; font-family: Arial, sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        header { padding: 20px; background: #202123; text-align: center; font-size: 24px; font-weight: bold; color: #fff; border-bottom: 1px solid #444; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }
        .message { background-color: #444654; padding: 15px; border-radius: 10px; margin: 8px 0; max-width: 95%; position: relative; word-wrap: break-word; }
        .message pre { position: relative; background-color: #202123 !important; padding: 15px; border-radius: 6px; overflow-x: auto; font-family: monospace; margin: 10px 0; }
        .message pre code { display: block; }
        .copy-code { position: absolute; top: 8px; right: 8px; background: #10a37f; border: none; color: white; padding: 4px 8px; font-size: 12px; border-radius: 4px; cursor: pointer; }
        .message h1, .message h2, .message h3 { color: #fff; margin: 10px 0 5px; }
        .input-area { display: flex; padding: 10px; background: #40414f; }
        textarea { flex: 1; resize: none; padding: 10px; font-size: 16px; border-radius: 5px; border: none; outline: none; background: #343541; color: #fff; }
        .send-btn { margin-left: 10px; background: #10a37f; border: none; color: white; padding: 10px 16px; font-size: 16px; border-radius: 5px; cursor: pointer; }
        .meta { font-size: 12px; color: #aaa; margin-top: 5px; }
        .delete-btn { background: #ef4444; border: none; color: white; padding: 4px 8px; font-size: 12px; border-radius: 3px; cursor: pointer; margin-left: 10px; }
        .clear-btn { background: #ef4444; border: none; color: white; padding: 6px 12px; font-size: 14px; border-radius: 5px; cursor: pointer; margin: 10px; align-self: flex-end; }
    </style>
</head>
<body>
<header>📓 BIJUSH NOTE BOOK</header>
<div class="chat-container" id="chat">
{% for note in notes %}
    <div class="message">
        {{ note["html"] | safe }}
        <div class="meta">
            Saved: {{ note["time"] }}
            <form method="post" style="display:inline;">
                <input type="hidden" name="delete" value="{{ note['id'] }}">
                <button type="submit" class="delete-btn">Delete</button>
            </form>
        </div>
    </div>
{% endfor %}
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
<script>
document.querySelectorAll('pre').forEach(function(pre) {
    const button = document.createElement('button');
    button.innerText = 'Copy code';
    button.className = 'copy-code';
    pre.appendChild(button);
    button.addEventListener('click', function() {
        const code = pre.querySelector('code').innerText;
        navigator.clipboard.writeText(code).then(() => {
            button.innerText = 'Copied!';
            setTimeout(() => button.innerText = 'Copy code', 1000);
        });
    });
});
var chat = document.getElementById("chat");
chat.scrollTop = chat.scrollHeight;
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "clear_all" in request.form:
            docs = notes_ref.stream()
            for doc in docs:
                doc.reference.delete()
            return redirect(url_for("index"))
        if "delete" in request.form:
            note_id = request.form["delete"]
            notes_ref.document(note_id).delete()
            return redirect(url_for("index"))
        note = request.form["note"]
        if note.strip():
            html_note = markdown.markdown(note, extensions=["fenced_code", "codehilite"])
            notes_ref.add({
                "raw": note.strip(),
                "html": html_note,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        return redirect(url_for("index"))

    docs = notes_ref.order_by("time").stream()
    notes = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return render_template_string(HTML, notes=notes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
