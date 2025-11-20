# flask_api.py
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

# Replace with your URL or set DATABASE_URL in env
DATABASE_URL2 = 'postgresql://neondb_owner:npg_uwsePmK35xkc@ep-ancient-frog-a1ivavxy.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_URL2)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = Flask(__name__)
_initialized = False


# -------------------------
# Generic SQL execution wrapper
# -------------------------
def exec_sql(sql: str, params: dict | None = None, fetch: bool = True):
    """Execute SQL safely and return results or rowcount."""
    try:
        stmt = text(sql)
        with engine.begin() as conn:
            result = conn.execute(stmt, params or {})
            if fetch:
                rows = result.fetchall()
                keys = result.keys()
                return {"ok": True, "rows": [dict(zip(keys, r)) for r in rows]}
            else:
                return {"ok": True, "rowcount": result.rowcount}
    except SQLAlchemyError as e:
        app.logger.exception("SQL error: %s", e)
        return {"ok": False, "error": str(e)}


# -------------------------
# Startup check (Flask 3.x safe)
# -------------------------
@app.before_request
def startup_once():
    global _initialized
    if _initialized:
        return
    _initialized = True
    ok = exec_sql("SELECT 1 AS v;", fetch=True)
    if ok["ok"]:
        app.logger.info("DB connected OK")
    else:
        app.logger.error("DB connect failed: %s", ok.get("error"))


# -------------------------
# Endpoint: list users
# -------------------------
@app.route("/users", methods=["GET"])
def get_users():
    """
    GET /users
    Returns list of users from public."user" (id,email,name)
    """
    out = exec_sql('SELECT id, email, name FROM public."user" ORDER BY id;', fetch=True)
    if not out["ok"]:
        return jsonify({"error": out.get("error")}), 500
    return jsonify({"users": out["rows"]}), 200


# -------------------------
# Endpoint: add user (JSON body: {"email": "...", "name": "..."})
# -------------------------
@app.route("/users", methods=["POST"])
def add_user():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    name = payload.get("name")
    if not email or not name:
        return jsonify({"error": "Both 'email' and 'name' are required"}), 400

    sql = '''
        INSERT INTO public."user" (email, name)
        VALUES (:email, :name)
        RETURNING id, email, name;
    '''
    out = exec_sql(sql, params={"email": email, "name": name}, fetch=True)
    if not out["ok"]:
        return jsonify({"error": out.get("error")}), 500
    created = out["rows"][0] if out["rows"] else None
    return jsonify({"created": created}), 201


# -------------------------
# Endpoint: delete user by id
# -------------------------
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    # check exists
    chk = exec_sql('SELECT id FROM public."user" WHERE id = :id LIMIT 1;', params={"id": user_id}, fetch=True)
    if not chk["ok"]:
        return jsonify({"error": chk.get("error")}), 500
    if not chk["rows"]:
        return jsonify({"error": "User not found"}), 404

    out = exec_sql('DELETE FROM public."user" WHERE id = :id;', params={"id": user_id}, fetch=False)
    if not out["ok"]:
        return jsonify({"error": out.get("error")}), 500
    return jsonify({"deleted": out.get("rowcount", 0)}), 200


# -------------------------
# Optional: console helper to insert a single user (same logic you pasted)
# Call this directly in Python or leave for debugging
# -------------------------
def insert_user_console(email="saikiranreddy790@gmail.com", name="saikiran 111"):
    print("🔍 Inserting user into public.\"user\" ...")
    sql = '''
        INSERT INTO public."user" (email, name)
        VALUES (:email, :name)
    '''
    out = exec_sql(sql, params={"email": email, "name": name}, fetch=False)
    if not out["ok"]:
        print("❌ Error:", out.get("error"))
    else:
        print("✅ Insert successful, rowcount:", out.get("rowcount"))


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    # optional quick insert for testing (uncomment to use)
    insert_user_console()

    # print current rows once before server starts
    try:
        rows = exec_sql('SELECT id, email, name FROM public."user" ORDER BY id;', fetch=True)
        if rows["ok"]:
            print("📌 Current users:")
            for r in rows["rows"]:
                print(f"   id: {r.get('id')} | email: {r.get('email')} | name: {r.get('name')}")
        else:
            print("Could not list users:", rows.get("error"))
    except Exception as e:
        print("Startup read failed:", e)

    app.run(host="0.0.0.0", port=7070, debug=True)
