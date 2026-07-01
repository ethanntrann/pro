import os
from flask import Flask, render_template, request, jsonify
from openrouter import OpenRouter

app = Flask(__name__)

API_KEY = os.getenv("BAYLEAF_API_KEY", "campus")

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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/research")
def research():
    return render_template(
        "research.html",
        research_experiences=research_experiences,
        publications=publications,
        research_interests=research_interests
    )

@app.route("/projects")
def projects_page():
    return render_template("projects.html", projects=projects)

@app.route("/leadership")
def leadership_page():
    return render_template("leadership.html", leadership=leadership)

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
    user_message = request.json.get("message", "")

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
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)