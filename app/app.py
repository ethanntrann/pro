import json
import os
from datetime import datetime
from functools import wraps
from uuid import uuid4

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
ALLOWED_MEDIA_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
LINKEDIN_URL = "https://www.linkedin.com/in/ethanlytran"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

research_experiences = [
    {
        "title": "Healthcare Internship",
        "description": "Shadowed oncologist Dr. Bao Dao and learned about oncology practices such as patient consultations, reviewing imaging and lab results, discussing treatment plans, understanding chemotherapy and radiation care, and observing how physicians communicate with patients and families."
    },
    {
        "title": "Hospital Volunteering",
        "description": "Volunteered at Pomona Valley Hospital for four years, gaining experience through direct patient interactions, patient support, communication with hospital staff, and helping create a more welcoming and compassionate care environment."
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
        "title": "Future Projects",
        "description": "More research, coding, and healthcare-related projects will be added here.",
        "skills": "Coming Soon"
    }
]

leadership = [
    {
        "title": "President of American Red Cross Club",
        "description": "Lead club meetings, coordinate volunteer opportunities, and help students support humanitarian work through service, emergency preparedness, blood-donation awareness, and community outreach."
    },
    {
        "title": "President of WeBall",
        "description": "Lead a youth basketball service club that teaches elementary school students the fundamentals of the game, including dribbling, passing, shooting, defense, teamwork, confidence, and sportsmanship. Organize accessible lessons and mentorship opportunities that help younger students build athletic skills while learning discipline, cooperation, and encouragement."
    },
    {
        "title": "President of Asian Pacific Islander Student Union (APISU)",
        "description": "Guide a student organization dedicated to building community, cultural awareness, and advocacy for Asian Pacific Islander Americans. Plan meetings and activities that celebrate identity, create belonging, and encourage thoughtful conversations about representation and service."
    },
    {
        "title": "Vice President of Key Club",
        "description": "Help lead a service-focused organization by supporting meeting planning, member engagement, volunteer coordination, and communication between officers and club members. Work to create meaningful service opportunities that encourage students to contribute consistently to their school and local community."
    },
    {
        "title": "Competitive Events Officer for FBLA",
        "description": "Support members as they prepare for business, finance, technology, and presentation competitions. Help organize practice resources, explain event expectations, encourage chapter participation, and strengthen the team's communication, professionalism, and competitive readiness."
    }
]

about_paragraphs = [
    "My name is Ethan Tran. I am a senior at Diamond Bar High School, and I am passionate about medicine, cancer biology, research, computer science, and using technology to solve meaningful problems.",
    "I have taken many courses to further these interests, including college-level biology and AP Chemistry, while also learning through hands-on experiences such as building computers and exploring how technology can support healthcare and problem solving.",
    "Community service has also shaped who I am. With hundreds of hours dedicated to serving others, I have learned the importance of consistency, empathy, leadership, and using my time to make a positive impact.",
    "In my free time, I also enjoy playing basketball."
]

relevant_courses = [
    "AP Calculus AB & BC",
    "AP Chemistry",
    "AP Computer Science A",
    "Biology",
    "Computer Systems",
    "Industrial Engineering",
    "BIOL 4 (Biology for Majors)",
    "AHIS 6 (History of Modern Art)",
    "BUSC 1A (Principles of Macroeconomics)"
]

awards = [
    {
        "section": "Service and Advocacy",
        "items": [
            "Humanitarian and International Law Advocate",
            "President's Volunteer Service Award - Gold"
        ]
    },
    {
        "section": "FBLA Awards",
        "items": [
            "1st Place Regional - Introduction to Financial Math",
            "6th Place Regional - Introduction to Information Technology",
            "4th Place State - Sports and Entertainment Management",
            "9th Place State - Digital Video Production"
        ]
    },
    {
        "section": "HOSA Awards",
        "items": [
            "8th Place State - Creative Problem Solving"
        ]
    }
]

SYSTEM_PROMPT = """
You are Ethan Tran's personal website AI assistant.
Answer questions about Ethan professionally and briefly.

Ethan is interested in medicine, cancer biology, stem cell biology,
research, computer science, hackathons, volunteering, FBLA, leadership,
and building technology that helps people. He has taken college-level
biology and AP Chemistry, enjoys building computers, plays basketball,
has hundreds of community service hours, and has leadership roles in
American Red Cross Club, FBLA, WeBall, APISU, and Key Club.
He has earned awards in FBLA, HOSA, humanitarian and international law
advocacy, and the President's Volunteer Service Award - Gold.

Give personalized answers based on the visitor's question. You may use
Markdown-style **bold** and *italic* formatting for emphasis. Keep answers
short, polished, and helpful.
"""

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"assistant_questions": [], "site_items": [], "visits": []}

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    data.setdefault("assistant_questions", [])
    data.setdefault("site_items", [])
    data.setdefault("visits", [])
    changed = False

    for item in data["site_items"]:
        if "id" not in item:
            item["id"] = uuid4().hex
            changed = True
        item.setdefault("heading", "")
        item.setdefault("file_url", "")
        item.setdefault("file_name", "")

    if changed:
        save_data(data)

    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_MEDIA_EXTENSIONS

def save_uploaded_media(file):
    if not file or not file.filename or not allowed_file(file.filename):
        return "", "", ""

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    timestamped_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file.save(os.path.join(UPLOAD_FOLDER, timestamped_filename))
    media_url = f"/static/uploads/{timestamped_filename}"

    if extension in IMAGE_EXTENSIONS:
        return media_url, "", filename
    return "", media_url, filename

def get_site_items(section):
    data = load_data()
    return [item for item in data["site_items"] if item["section"] == section]

def page_sections(section):
    sections = {}
    for item in get_site_items(section):
        heading = item.get("heading") or "Added Updates"
        sections.setdefault(heading, []).append(item)
    return sections

def page_name_from_path(path):
    if path == "/":
        return "home"
    return path.strip("/") or "home"

def visitor_ip_prefix():
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip_address = forwarded.split(",")[0].strip() or request.remote_addr or "unknown"
    if "." in ip_address:
        parts = ip_address.split(".")
        return ".".join(parts[:2]) + ".*.*"
    if ":" in ip_address:
        return ip_address.split(":")[0] + ":*"
    return ip_address

def track_visit(page):
    if request.path.startswith("/static") or request.path.startswith("/admin") or request.path == "/chat":
        return

    data = load_data()
    data["visits"].insert(0, {
        "id": uuid4().hex,
        "page": page,
        "path": request.path,
        "visited_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "referrer": request.referrer or "Direct",
        "user_agent": request.headers.get("User-Agent", "Unknown"),
        "ip_prefix": visitor_ip_prefix()
    })
    data["visits"] = data["visits"][:500]
    save_data(data)

def analytics_summary(visits):
    page_counts = {}
    recent_visits = visits[:50]

    for visit in visits:
        page_counts[visit["page"]] = page_counts.get(visit["page"], 0) + 1

    top_pages = sorted(page_counts.items(), key=lambda item: item[1], reverse=True)

    return {
        "total_visits": len(visits),
        "top_pages": top_pages,
        "recent_visits": recent_visits
    }

def editor_items(section):
    return get_site_items(section) if session.get("is_admin") else []

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
def home():
    track_visit("home")
    return render_template(
        "index.html",
        about_paragraphs=about_paragraphs,
        linkedin_url=LINKEDIN_URL,
        site_sections=page_sections("home"),
        current_page="home",
        editor_items=editor_items("home")
    )

@app.route("/about")
def about():
    track_visit("about")
    return render_template("about.html", site_sections=page_sections("about"), current_page="about", editor_items=editor_items("about"))

@app.route("/research")
def research():
    track_visit("experiences")
    return render_template(
        "research.html",
        research_experiences=research_experiences,
        publications=publications,
        projects=projects,
        research_interests=research_interests,
        relevant_courses=relevant_courses,
        site_sections=page_sections("experiences"),
        current_page="experiences",
        editor_items=editor_items("experiences")
    )

@app.route("/projects")
def projects_page():
    track_visit("projects")
    return render_template("projects.html", projects=projects, site_sections=page_sections("projects"), current_page="projects", editor_items=editor_items("projects"))

@app.route("/leadership")
def leadership_page():
    track_visit("leadership")
    return render_template("leadership.html", leadership=leadership, site_sections=page_sections("leadership"), current_page="leadership", editor_items=editor_items("leadership"))

@app.route("/awards")
def awards_page():
    track_visit("awards")
    return render_template("awards.html", awards=awards, site_sections=page_sections("awards"), current_page="awards", editor_items=editor_items("awards"))

@app.route("/resume")
def resume():
    return redirect(url_for("static", filename="files/ethan-tran-resume.pdf"))

@app.route("/contact")
def contact():
    track_visit("contact")
    return render_template("contact.html", linkedin_url=LINKEDIN_URL, site_sections=page_sections("contact"), current_page="contact", editor_items=editor_items("contact"))

@app.route("/ai")
def ai():
    track_visit("help")
    return render_template("ai.html", site_sections=page_sections("help"), current_page="help", editor_items=editor_items("help"))

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
    selected_page = request.args.get("page", "home")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        section = request.form.get("section", selected_page)
        heading = request.form.get("heading", "").strip()
        media = request.files.get("media") or request.files.get("image")
        image_url, file_url, file_name = save_uploaded_media(media)

        if title and description:
            data["site_items"].insert(0, build_site_item(title, description, section, heading, image_url, file_url, file_name))
            save_data(data)
            return redirect(url_for("admin_dashboard", page=section))

    return render_template(
        "admin_dashboard.html",
        questions=data["assistant_questions"],
        site_items=data["site_items"],
        selected_page=selected_page,
        analytics=analytics_summary(data["visits"])
    )

def build_site_item(title, description, section, heading, image_url, file_url="", file_name=""):
    return {
        "id": uuid4().hex,
        "title": title,
        "description": description,
        "section": section,
        "heading": heading,
        "image_url": image_url,
        "file_url": file_url,
        "file_name": file_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }

def safe_return_path():
    return_path = request.form.get("return_path", "/admin/dashboard")
    if not return_path.startswith("/") or return_path.startswith("//"):
        return "/admin/dashboard"
    return return_path

@app.route("/admin/inline-content", methods=["POST"])
@admin_required
def add_inline_site_item():
    data = load_data()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    section = request.form.get("section", "home")
    heading = request.form.get("heading", "").strip()
    media = request.files.get("media") or request.files.get("image")
    image_url, file_url, file_name = save_uploaded_media(media)

    if title and description:
        data["site_items"].insert(0, build_site_item(title, description, section, heading, image_url, file_url, file_name))
        save_data(data)

    return redirect(safe_return_path())

@app.route("/admin/content/<item_id>/update", methods=["POST"])
@admin_required
def update_site_item(item_id):
    data = load_data()

    for item in data["site_items"]:
        if item.get("id") == item_id:
            item["section"] = request.form.get("section", item["section"])
            item["heading"] = request.form.get("heading", "").strip()
            item["title"] = request.form.get("title", "").strip()
            item["description"] = request.form.get("description", "").strip()
            media = request.files.get("media") or request.files.get("image")
            image_url, file_url, file_name = save_uploaded_media(media)

            if image_url:
                item["image_url"] = image_url
                item["file_url"] = ""
                item["file_name"] = ""
            if file_url:
                item["file_url"] = file_url
                item["file_name"] = file_name
                item["image_url"] = ""
            break

    save_data(data)
    if request.form.get("return_path"):
        return redirect(safe_return_path())
    return redirect(url_for("admin_dashboard", page=request.form.get("section", "home")))

@app.route("/admin/content/<item_id>/delete", methods=["POST"])
@admin_required
def delete_site_item(item_id):
    data = load_data()
    data["site_items"] = [item for item in data["site_items"] if item.get("id") != item_id]
    save_data(data)
    if request.form.get("return_path"):
        return redirect(safe_return_path())
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
