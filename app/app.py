import json
import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from openrouter import OpenRouter
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24)

API_KEY = os.getenv("BAYLEAF_API_KEY", "campus")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "site_data.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

research_experiences = [
    {
        "title": "Healthcare Internship",
        "description": "Observed patient care and became more interested in medicine and cancer biology."
    },
    {
        "title": "Hospital Volunteering",
        "description": "Volunteered in a hospital setting and learned more about patient-centered care."
    }
]

publications = [
    {
        "title": "Coming Soon",
        "description": "Future research papers, posters, or presentations will be added here."
    }
]

research_interests = [
    "Cancer Biology",
    "Stem Cell Biology",
    "Medicine",
    "Patient Care",
    "AI in Healthcare"
]

projects = [
    {
        "title": "AI Hackathon Assistant",
        "description": "A Bayleaf AI chatbot that helps hackathon students brainstorm project ideas.",
        "skills": "Python, Flask, Bayleaf AI"
    },
    {
        "title": "Blossom Project",
        "description": "A project focused on helping people form groups and create ideas during hackathons.",
        "skills": "AI, Human Interaction, Research"
    },
    {
        "title": "Portfolio Website",
        "description": "A professional personal website with multiple pages and an AI assistant.",
        "skills": "Flask, HTML, CSS"
    },
    {
        "title": "Future Projects",
        "description": "More research, coding, and healthcare-related projects will be added here.",
        "skills": "Coming Soon"
    }
]

leadership = [
    {
        "title": "President of American Red Cross Club",
        "description": "Lead club meetings, organize service opportunities, and help students support humanitarian work through volunteering, preparedness, and community outreach."
    },
    {
        "title": "FBLA",
        "description": "Developed leadership, business, communication, and teamwork skills."
    },
    {
        "title": "Research Club",
        "description": "Interested in helping students explore research and STEM opportunities."
    },
    {
        "title": "Volunteering",
        "description": "Gained experience serving others and learning about healthcare environments."
    },
    {
        "title": "Community Service",
        "description": "Committed to supporting my community through service and leadership."
    }
]

SYSTEM_PROMPT = """
You are Ethan Tran's personal website AI assistant.
Answer questions about Ethan professionally and briefly.

Ethan is interested in medicine, cancer biology, stem cell biology,
research, computer science, hackathons, volunteering, FBLA, leadership,
and building technology that helps people.

Keep answers short, polished, and helpful.
"""

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"assistant_questions": [], "site_items": []}

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_site_items(section):
    data = load_data()
    return [item for item in data["site_items"] if item["section"] == section]

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
def home():
    return render_template("index.html", site_items=get_site_items("home"))

@app.route("/about")
def about():
    return render_template("about.html", site_items=get_site_items("about"))

@app.route("/research")
def research():
    return render_template(
        "research.html",
        research_experiences=research_experiences,
        publications=publications,
        research_interests=research_interests,
        site_items=get_site_items("experiences")
    )

@app.route("/projects")
def projects_page():
    return render_template("projects.html", projects=projects, site_items=get_site_items("projects"))

@app.route("/leadership")
def leadership_page():
    return render_template("leadership.html", leadership=leadership, site_items=get_site_items("leadership"))

@app.route("/resume")
def resume():
    return render_template("resume.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/ai")
def ai():
    return render_template("ai.html")

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = payload.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please ask a question first."})

    with OpenRouter(
        server_url="https://api.bayleaf.dev/v1",
        api_key=API_KEY
    ) as client:
        response = client.chat.send(
            model="minimax/minimax-m2",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )

    reply = response.choices[0].message.content
    data = load_data()
    data["assistant_questions"].insert(0, {
        "question": user_message,
        "reply": reply,
        "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    })
    save_data(data)

    return jsonify({"reply": reply})

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = None

    if not ADMIN_PASSWORD:
        return render_template("admin_login.html", error="Set ADMIN_PASSWORD before using the admin page.")

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect password."

    return render_template("admin_login.html", error=error)

@app.route("/admin/dashboard", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    data = load_data()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        section = request.form.get("section", "home")
        image = request.files.get("image")
        image_url = ""

        if image and image.filename and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            timestamped_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            image.save(os.path.join(UPLOAD_FOLDER, timestamped_filename))
            image_url = f"/static/uploads/{timestamped_filename}"

        if title and description:
            data["site_items"].insert(0, {
                "title": title,
                "description": description,
                "section": section,
                "image_url": image_url,
                "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p")
            })
            save_data(data)
            return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_dashboard.html",
        questions=data["assistant_questions"],
        site_items=data["site_items"]
    )

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
