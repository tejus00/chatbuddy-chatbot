# app.py
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from db import db
from model import Message,Employee
from sqlalchemy.exc import SQLAlchemyError
from indent import rule_based_reply

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip() or None
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"
PORT = int(os.getenv("PORT", 5000))
DATABASE_FILE = os.getenv("DATABASE_FILE", "./data/chat.sqlite")

# ---- NEW: robust, absolute DB path (Windows friendly) ----
BASE_DIR = os.path.abspath(os.path.dirname(__file__))          # D:\woi\my_agent
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, DATABASE_FILE))  # D:\woi\my_agent\data\chat.sqlite

app = Flask(__name__, static_folder="public", static_url_path="/")

# Use forward slashes for SQLite URI
db_uri_path = DB_PATH.replace("\\", "/")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_uri_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

print("USING DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])

# Create DB file / tables on startup
with app.app_context():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    db.create_all()
# Optional: lazy import google genai if GEMINI_API_KEY present
genai_client = None
if GEMINI_API_KEY:
    try:
        # google-genai SDK picks up GEMINI_API_KEY from env or we can set it:
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        # import the SDK
        from google import genai
        genai_client = genai.Client()  # per SDK quickstart example
    except Exception as e:
        genai_client = None
        app.logger.warning("Failed to initialize google-genai client: %s", e)



    
    

def query_gemini(prompt: str) -> str:
    """Query Gemini via google-genai SDK. Returns reply string or raises."""
    if not genai_client:
        raise RuntimeError("Gemini client is not configured.")
    # Per google-genai Python quickstart and text-generation examples:
    # client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    # response.text prints the generated text.
    model_name = "gemini-2.5-flash"  # pick model; change if you have access to others
    response = genai_client.models.generate_content(model=model_name, contents=prompt)
    # SDK exposes response.text (per docs/examples). Defensive handling below:
    if hasattr(response, "text") and response.text:
        return response.text
    # fallback: try outputs structure
    outputs = getattr(response, "outputs", None)
    if outputs and len(outputs) > 0:
        first = outputs[0]
        # content may be an array with text
        content = first.get("content") if isinstance(first, dict) else None
        if content and isinstance(content, list) and len(content) > 0:
            maybe_text = content[0].get("text")
            if maybe_text:
                return maybe_text
    # if still nothing:
    raise RuntimeError("No text returned from Gemini response; unexpected structure.")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "gemini": bool(genai_client)})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    if not data or "message" not in data:
        return jsonify({"error": "message required"}), 400
    user_msg = data["message"]

    # Save user message
    try:
        m = Message(sender="user", text=user_msg, source=None)
        db.session.add(m)
        db.session.commit()
    except SQLAlchemyError as e:
        app.logger.error("DB save user failed: %s", e)
        db.session.rollback()

    # 1) try local rule-based
    rule_reply = rule_based_reply(user_msg)
    if rule_reply is not None:
        try:
            mb = Message(sender="bot", text=rule_reply, source="rules")
            db.session.add(mb)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
        return jsonify({"reply": rule_reply, "source": "rules"})

    # 2) try Gemini if enabled
    if USE_GEMINI and genai_client:
        try:
            gemini_reply = query_gemini(user_msg)
            try:
                mb = Message(sender="bot", text=gemini_reply, source="gemini")
                db.session.add(mb)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
            return jsonify({"reply": gemini_reply, "source": "gemini"})
        except Exception as e:
            app.logger.error("Gemini call failed: %s", e)

    # 3) fallback reply
    fallback = "I’m not sure about that. Try something simpler (or configure GEMINI_API_KEY)."
    try:
        mb = Message(sender="bot", text=fallback, source="fallback")
        db.session.add(mb)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
    return jsonify({"reply": fallback, "source": "fallback"})
@app.route("/employees", methods=["POST"])
def create_employee():
    data = request.get_json(force=True)

    name = data.get("name")
    email = data.get("email")
    department = data.get("department")
    designation = data.get("designation")
    salary = data.get("salary")

    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400

    try:
        emp = Employee(
            name=name,
            email=email,
            department=department,
            designation=designation,
            salary=salary
        )
        db.session.add(emp)
        db.session.commit()
        return jsonify(emp.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error("Failed to insert employee: %s", e)
        return jsonify({"error": "DB error"}), 500


@app.route("/employees", methods=["GET"])
def list_employees():
    employees = Employee.query.order_by(Employee.id.asc()).all()
    return jsonify([e.to_dict() for e in employees])
@app.route("/employee_table")
def employee_table():
    employees = Employee.query.all()
    return jsonify([e.to_dict() for e in employees])


@app.route("/history", methods=["GET"])
def history():
    try:
        limit = min(int(request.args.get("limit", 200)), 2000)
    except Exception:
        limit = 200
    rows = Message.query.order_by(Message.created_at.asc()).limit(limit).all()
    return jsonify([r.to_dict() for r in rows])

# Serve frontend
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
