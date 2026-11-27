import os
import re
import uuid
from functools import wraps

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db, init_db
from docx_generator import (
    MODULES_META,
    build_official_filename,
    generate_report_docx,
)
from gemini_service import generate_report_ai_content

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
ADMIN_PIN = os.environ.get("LAPRAKIN_ADMIN_PIN", "2026")

app = Flask(__name__)
app.secret_key = os.environ.get("LAPRAKIN_SECRET_KEY", "laprakin-labtif-uad-2026-secret")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB

init_db()
os.makedirs(GENERATED_DIR, exist_ok=True)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Sesi berakhir. Silakan login kembali."}), 401
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, full_name, username, created_at FROM users WHERE id = ?",
            (uid,),
        ).fetchone()
    return dict(row) if row else None


@app.route("/")
@login_required
def index():
    user = current_user()
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template("index.html", user=user, modules=MODULES_META)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    error = None
    success = request.args.get("reset")
    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip().lower()
        password = request.form.get("password") or ""
        if not identifier or not password:
            error = "Email/Username dan Password wajib diisi."
        else:
            with get_db() as conn:
                user = conn.execute(
                    "SELECT * FROM users WHERE lower(username) = ?",
                    (identifier,),
                ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                return redirect(url_for("index"))
            error = "Username atau kata sandi salah."

    return render_template("login.html", error=error, success=success)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("index"))

    error = None
    form_data = {"full_name": "", "username": ""}
    if request.method == "POST":
        # Anti-bot honeypot check
        honeypot = (request.form.get("website") or "").strip()
        if honeypot:
            return render_template(
                "signup.html",
                error="Permintaan tidak valid terdeteksi.",
                form_data=form_data,
            ), 400

        full_name = (request.form.get("full_name") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        form_data = {"full_name": full_name, "username": username}

        if not full_name:
            error = "Nama Lengkap wajib diisi."
        elif not re.fullmatch(r"[a-z0-9]{3,30}", username):
            error = "Username harus 3-30 karakter huruf kecil & angka tanpa spasi."
        elif len(password) < 5:
            error = "Kata sandi minimal 5 karakter."
        elif password != confirm_password:
            error = "Konfirmasi kata sandi tidak cocok."
        else:
            with get_db() as conn:
                existing = conn.execute(
                    "SELECT id FROM users WHERE username = ?", (username,)
                ).fetchone()
                if existing:
                    error = "Username sudah terdaftar. Silakan pilih username lain."
                else:
                    cur = conn.execute(
                        "INSERT INTO users (full_name, username, password_hash) VALUES (?, ?, ?)",
                        (full_name, username, generate_password_hash(password)),
                    )
                    session["user_id"] = cur.lastrowid
                    session["username"] = username
                    session["full_name"] = full_name
                    return redirect(url_for("index"))

    return render_template("signup.html", error=error, form_data=form_data)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    if request.method == "POST":
        honeypot = (request.form.get("website") or "").strip()
        if honeypot:
            return render_template("forgot_password.html", error="Permintaan ditolak."), 400

        username = (request.form.get("username") or "").strip().lower()
        full_name = (request.form.get("full_name") or "").strip()
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not username or not full_name:
            error = "Username dan Nama Lengkap wajib diisi untuk verifikasi akun."
        elif len(new_password) < 5:
            error = "Kata sandi baru minimal 5 karakter."
        elif new_password != confirm_password:
            error = "Konfirmasi kata sandi baru tidak cocok."
        else:
            with get_db() as conn:
                user = conn.execute(
                    "SELECT id, full_name FROM users WHERE lower(username) = ?",
                    (username,),
                ).fetchone()
                if not user or user["full_name"].strip().lower() != full_name.lower():
                    error = "Kombinasi Username dan Nama Lengkap tidak ditemukan."
                else:
                    conn.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (generate_password_hash(new_password), user["id"]),
                    )
                    return redirect(url_for("login", reset="1"))

    return render_template("forgot_password.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/privacy")
def privacy():
    return render_template("legal.html", page="privacy")


@app.route("/terms")
def terms():
    return render_template("legal.html", page="terms")


@app.route("/about-account")
def about_account():
    return render_template("legal.html", page="about-account")


@app.route("/api/ai/generate", methods=["POST"])
@login_required
def api_ai_generate():
    data = request.get_json(silent=True) or {}
    module_key = data.get("moduleKey", "kdjk")
    meta = MODULES_META.get(module_key, MODULES_META["kdjk"])
    payload = {
        **data,
        "moduleName": meta["name"],
        "moduleTools": meta["tools"],
    }
    try:
        result = generate_report_ai_content(payload)
        return jsonify(result)
    except ValueError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:
        return jsonify({"error": f"Gagal generate AI: {err}"}), 502


@app.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    data = request.get_json(silent=True) or {}
    module_key = data.get("moduleKey", "kdjk")
    if module_key not in MODULES_META:
        return jsonify({"error": "Modul tidak valid."}), 400

    nim = (data.get("nim") or "").strip()
    student_name = (data.get("studentName") or "").strip()
    meeting_number = int(data.get("meetingNumber") or 1)
    class_name = (data.get("className") or "").strip()
    topic_title = (data.get("topicTitle") or "").strip()
    pj_assistant = (data.get("pjAssistant") or "").strip()

    if not nim or not student_name or not class_name or not topic_title:
        return jsonify({"error": "Data profil praktikum belum lengkap."}), 400

    if MODULES_META[module_key]["needs_pj"] and not pj_assistant:
        return jsonify({"error": "Nama PJ Asisten Praktikum wajib diisi untuk modul ini."}), 400

    official_filename = build_official_filename(
        module_key=module_key,
        nim=nim,
        student_name=student_name,
        meeting_number=meeting_number,
        pj_assistant=pj_assistant,
        day_name=(data.get("dayName") or "").strip(),
        exec_time=(data.get("execTime") or "").strip(),
    )

    unique_storage_name = f"{uuid.uuid4().hex}_{official_filename}"
    output_path = os.path.join(GENERATED_DIR, unique_storage_name)

    generate_report_docx(data, output_path)

    review_text = (data.get("reviewText") or "").strip()
    word_count = len(review_text.split()) if review_text else 0

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO reports (
                user_id, module_key, module_name, nim, student_name,
                meeting_number, class_name, topic_title, pj_assistant,
                filename, file_path, word_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                module_key,
                MODULES_META[module_key]["name"],
                nim,
                student_name,
                meeting_number,
                class_name,
                topic_title,
                pj_assistant,
                official_filename,
                unique_storage_name,
                word_count,
            ),
        )
        report_id = cur.lastrowid

    return jsonify(
        {
            "reportId": report_id,
            "filename": official_filename,
            "downloadUrl": url_for("api_download_report", report_id=report_id),
        }
    )


@app.route("/api/reports", methods=["GET"])
@login_required
def api_reports():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, module_key, module_name, nim, student_name,
                   meeting_number, class_name, topic_title, filename,
                   word_count, created_at
            FROM reports
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (session["user_id"],),
        ).fetchall()

    items = []
    for r in rows:
        item = dict(r)
        item["downloadUrl"] = url_for("api_download_report", report_id=r["id"])
        items.append(item)
    return jsonify({"reports": items})


@app.route("/api/profile/update", methods=["POST"])
@login_required
def api_profile_update():
    data = request.get_json(silent=True) or {}
    new_full_name = (data.get("fullName") or "").strip()
    new_username = (data.get("username") or "").strip().lower()
    current_password = data.get("currentPassword") or ""
    new_password = data.get("newPassword") or ""

    if not new_username or len(new_username) < 3:
        return jsonify({"error": "Username minimal 3 karakter."}), 400
    if not re.match(r"^[a-z0-9_.-]+$", new_username):
        return jsonify({"error": "Username hanya boleh berisi huruf, angka, titik, garis bawah, atau strip."}), 400

    uid = session["user_id"]
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        if not user:
            return jsonify({"error": "Pengguna tidak ditemukan."}), 404

        conflict = conn.execute(
            "SELECT id FROM users WHERE lower(username) = ? AND id != ?",
            (new_username, uid),
        ).fetchone()
        if conflict:
            return jsonify({"error": "Username sudah digunakan akun lain."}), 409

        final_full_name = new_full_name or user["full_name"]
        final_hash = user["password_hash"]

        if new_password:
            if not current_password:
                return jsonify({"error": "Masukkan kata sandi saat ini untuk mengganti kata sandi."}), 400
            if not check_password_hash(user["password_hash"], current_password):
                return jsonify({"error": "Kata sandi saat ini salah."}), 400
            if len(new_password) < 6:
                return jsonify({"error": "Kata sandi baru minimal 6 karakter."}), 400
            final_hash = generate_password_hash(new_password)

        conn.execute(
            "UPDATE users SET full_name = ?, username = ?, password_hash = ? WHERE id = ?",
            (final_full_name, new_username, final_hash, uid),
        )

    session["username"] = new_username
    session["full_name"] = final_full_name
    return jsonify(
        {
            "ok": True,
            "username": new_username,
            "fullName": final_full_name,
            "message": "Profil berhasil diperbarui.",
        }
    )


@app.route("/api/reports/<int:report_id>/download", methods=["GET"])
@login_required
def api_download_report(report_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM reports WHERE id = ? AND user_id = ?",
            (report_id, session["user_id"]),
        ).fetchone()
    if not row:
        return jsonify({"error": "Laporan tidak ditemukan."}), 404

    full_path = os.path.join(GENERATED_DIR, row["file_path"])
    if not os.path.exists(full_path):
        return jsonify({"error": "File laporan sudah tidak tersedia di server."}), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=row["filename"],
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.route("/admin", methods=["GET"])
def admin_page():
    unlocked = bool(session.get("admin_unlocked"))
    return render_template("admin.html", unlocked=unlocked)


@app.route("/api/admin/auth", methods=["POST"])
def api_admin_auth():
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin") or "").strip()
    if pin == ADMIN_PIN:
        session["admin_unlocked"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "PIN 4 digit salah."}), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    session.pop("admin_unlocked", None)
    return jsonify({"ok": True})


@app.route("/api/admin/stats", methods=["GET"])
def api_admin_stats():
    if not session.get("admin_unlocked"):
        return jsonify({"error": "Akses admin terkunci."}), 401

    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        by_module = conn.execute(
            "SELECT module_key, module_name, COUNT(*) AS count FROM reports GROUP BY module_key, module_name ORDER BY count DESC"
        ).fetchall()
        recent_users = conn.execute(
            "SELECT id, full_name, username, created_at FROM users ORDER BY id DESC LIMIT 15"
        ).fetchall()
        recent_reports = conn.execute(
            """
            SELECT r.id, r.module_name, r.nim, r.student_name, r.meeting_number,
                   r.filename, r.word_count, r.created_at, u.username
            FROM reports r
            JOIN users u ON u.id = r.user_id
            ORDER BY r.id DESC
            LIMIT 20
            """
        ).fetchall()

    return jsonify(
        {
            "totalUsers": total_users,
            "totalReports": total_reports,
            "byModule": [dict(r) for r in by_module],
            "recentUsers": [dict(r) for r in recent_users],
            "recentReports": [dict(r) for r in recent_reports],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
