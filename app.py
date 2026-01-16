import os
import sqlite3
import socket
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
from io import BytesIO
import qrcode
import mimetypes
import zipfile
import tempfile
from functools import wraps
import threading
import time
from contextlib import contextmanager

ADMIN_ACCOUNTS_STR = os.environ.get("ADMIN_ACCOUNTS", "")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")
SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_secret_for_prod")
ADMIN_ACCOUNTS = {}
if ADMIN_ACCOUNTS_STR:
    for account in ADMIN_ACCOUNTS_STR.split(","):
        account = account.strip()
        if ":" in account:
            user, pwd = account.split(":", 1)
            ADMIN_ACCOUNTS[user.strip()] = pwd.strip()
else:
    ADMIN_ACCOUNTS[ADMIN_USER] = ADMIN_PASS
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "5000"))
DEBUG_MODE = os.environ.get("DEBUG", "False").lower() == "true"
SERVER_URL = os.environ.get("SERVER_URL", "")

DB = "survey.db"

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY

DB_TIMEOUT = 60.0
DB_CHECK_SAME_THREAD = False

MAX_RETRIES = 5
RETRY_BASE_DELAY = 0.05
MAX_RETRY_DELAY = 2.0


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(
            DB,
            timeout=DB_TIMEOUT,
            check_same_thread=DB_CHECK_SAME_THREAD
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        cache_size = int(os.environ.get("SQLITE_CACHE_SIZE", "-256000"))
        conn.execute(f"PRAGMA cache_size={cache_size}")
        conn.execute("PRAGMA page_size=4096")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")
        yield conn
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            if conn:
                try:
                    conn.close()
                except:
                    pass
            raise
        else:
            raise
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS survey_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q1 TEXT,
            q2 TEXT,
            q3 TEXT,
            name TEXT,
            student_id TEXT,
            file_name TEXT,
            file_blob BLOB,
            file_type TEXT,
            submit_time TEXT
        )
        """)
        
        try:
            c.execute("ALTER TABLE survey_records ADD COLUMN name TEXT")
        except:
            pass
        try:
            c.execute("ALTER TABLE survey_records ADD COLUMN student_id TEXT")
        except:
            pass
        c.execute("""
        CREATE TABLE IF NOT EXISTS survey_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_id INTEGER,
            file_name TEXT,
            file_blob BLOB,
            file_type TEXT,
            FOREIGN KEY(survey_id) REFERENCES survey_records(id)
        )
        """)

        conn.commit()


def get_server_url():
    if SERVER_URL:
        return SERVER_URL
    
    try:
        from flask import request
        if request and hasattr(request, 'host') and request.host:
            host = request.host
            if not host.startswith('http'):
                return f"http://{host}"
            return host
    except:
        pass
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        port = SERVER_PORT if SERVER_PORT != 80 else ""
        port_str = f":{port}" if port and port != 80 else ""
        return f"http://{ip}{port_str}"
    except:
        return f"http://127.0.0.1:{SERVER_PORT}"


@app.route("/qrcode")
def show_qrcode():
    url = get_server_url()
    if not url.endswith("/"):
        url += "/"
    
    if DEBUG_MODE:
        print(f"[DEBUG] 二维码URL: {url}")

    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/")
def survey():
    return render_template("survey.html")


@app.route("/survey")
def survey_redirect():
    return redirect(url_for("survey"))


@app.route("/submit", methods=["POST"])
def submit():
    files_data = []
    try:
        files = request.files.getlist("files")
        for f in files:
            if not f:
                continue
            fname = f.filename
            blob = f.read()
            low = fname.lower()

            if low.endswith((".jpg", ".jpeg", ".png")):
                ftype = "image"
            elif low.endswith((".doc", ".docx")):
                ftype = "word"
            else:
                ftype = "other"
            
            files_data.append((fname, blob, ftype))
    except Exception as e:
        return jsonify({"status": "error", "msg": f"文件读取失败: {str(e)}"}), 500

    # 获取表单数据
    q1 = request.form.get("q1", "")
    q2 = request.form.get("q2", "")
    q3 = request.form.get("q3", "")
    name = request.form.get("name", "").strip()
    student_id = request.form.get("student_id", "").strip()

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO survey_records (q1, q2, q3, name, student_id, file_name, file_blob, file_type, submit_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
                """, (q1, q2, q3, name, student_id, None, None, None))
                survey_id = cursor.lastrowid

                if files_data:
                    cursor.executemany(
                        "INSERT INTO survey_files (survey_id, file_name, file_blob, file_type) VALUES (?, ?, ?, ?)",
                        [(survey_id, fname, blob, ftype) for fname, blob, ftype in files_data]
                    )

                conn.commit()

            return jsonify({"status": "ok"}), 200

        except sqlite3.OperationalError as e:
            last_error = e
            if "database is locked" in str(e).lower():
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                    time.sleep(delay)
                    continue
                else:
                    return jsonify({"status": "error", "msg": "系统繁忙，请稍后重试"}), 503
            else:
                return jsonify({"status": "error", "msg": f"数据库错误: {str(e)}"}), 500

        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    return jsonify({"status": "error", "msg": "提交失败，请稍后重试"}), 500


@app.route("/file/<int:file_id>")
@login_required
def get_file(file_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_name, file_blob, file_type FROM survey_files WHERE id=?", (file_id,))
        row = cursor.fetchone()

    if not row:
        return "文件不存在", 404

    fname, blob, ftype = row
    if ftype == "image":
        mime = mimetypes.guess_type(fname)[0] or "image/jpeg"
        return send_file(BytesIO(blob), mimetype=mime)
    else:
        return send_file(BytesIO(blob), as_attachment=True, download_name=fname)


@app.route("/records")
@login_required
def records():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.id, r.q1, r.q2, r.q3, r.name, r.student_id, r.submit_time,
                   f.id, f.file_name, f.file_type
            FROM survey_records r
            LEFT JOIN survey_files f ON r.id = f.survey_id
            ORDER BY r.id DESC, f.id ASC
        """)
        rows = cursor.fetchall()

    records_map = {}
    order = []

    for row in rows:
        rid = row[0]
        if rid not in records_map:
            records_map[rid] = {
                "id": rid,
                "q1": row[1],
                "q2": row[2],
                "q3": row[3],
                "name": row[4],
                "student_id": row[5],
                "submit_time": row[6],
                "files": []
            }
            order.append(rid)

        file_id = row[7]
        if file_id:
            records_map[rid]["files"].append({
                "id": file_id,
                "name": row[8],
                "type": row[9]
            })

    records_list = [records_map[r] for r in order]
    return render_template("records.html", records=records_list)


@app.route("/delete_records", methods=["POST"])
@login_required
def delete_records():
    try:
        data = request.get_json()
        ids = data.get("ids", [])
        
        if not ids:
            return jsonify({"status": "error", "msg": "未选择要删除的记录"}), 400
        
        try:
            ids = [int(id) for id in ids]
        except (ValueError, TypeError):
            return jsonify({"status": "error", "msg": "无效的记录ID"}), 400
        
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    placeholders = ",".join(["?"] * len(ids))
                    cursor.execute(f"""
                        DELETE FROM survey_files 
                        WHERE survey_id IN ({placeholders})
                    """, ids)
                    
                    cursor.execute(f"""
                        DELETE FROM survey_records 
                        WHERE id IN ({placeholders})
                    """, ids)
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                return jsonify({
                    "status": "ok",
                    "msg": f"成功删除 {deleted_count} 条记录"
                }), 200
                
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e).lower():
                    if attempt < MAX_RETRIES - 1:
                        delay = min(RETRY_BASE_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                        time.sleep(delay)
                        continue
                    else:
                        return jsonify({"status": "error", "msg": "系统繁忙，请稍后重试"}), 503
                else:
                    return jsonify({"status": "error", "msg": f"数据库错误: {str(e)}"}), 500
        
        return jsonify({
            "status": "ok",
            "msg": f"成功删除 {deleted_count} 条记录"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route("/download_all")
@login_required
def download_all():
    ftype = request.args.get("type", "all")
    date_filter = request.args.get("date")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        sql = """
        SELECT f.id, f.file_name, f.file_blob, f.file_type,
               r.submit_time, r.id
        FROM survey_files f
        JOIN survey_records r ON r.id = f.survey_id
        WHERE 1=1
        """
        params = []

        if ftype == "image":
            sql += " AND f.file_type='image'"
        elif ftype == "word":
            sql += " AND f.file_type='word'"

        if date_filter:
            sql += " AND date(r.submit_time)=?"
            params.append(date_filter)

        sql += " ORDER BY r.submit_time ASC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

    if not rows:
        return "没有符合条件的文件"

    tmp = tempfile.NamedTemporaryFile(delete=False)
    zp = tmp.name
    tmp.close()

    readme = []

    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for fid, fname, blob, ftype_name, submit_time, sid in rows:
            date = submit_time.split(" ")[0]
            safe = f"{fid}_{fname}"
            z.writestr(f"{date}/{safe}", blob)

            readme.append(
                f"记录ID:{sid}\n文件ID:{fid}\n文件:{safe}（{ftype_name}）\n时间:{submit_time}\n\n"
            )

        z.writestr("README.txt", "".join(readme))

    name_map = {
        "all": "all_files.zip",
        "image": "images_only.zip",
        "word": "word_only.zip"
    }
    return send_file(zp, as_attachment=True, download_name=name_map.get(ftype, "all_files.zip"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("records"))

    msg = ""
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pwd = request.form.get("password", "")

        if user in ADMIN_ACCOUNTS and ADMIN_ACCOUNTS[user] == pwd:
            session["is_admin"] = True
            session["admin_user"] = user
            return redirect(url_for("records"))
        else:
            msg = "账号或密码错误"

    return render_template("login.html", msg=msg)


@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    session.pop("admin_user", None)
    return redirect(url_for("login"))


@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")


if __name__ == "__main__":
    init_db()
    
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        pass
    
    localhost_url = f"http://127.0.0.1:{SERVER_PORT}"
    lan_url = f"http://{local_ip}:{SERVER_PORT}"
    
    qrcode_url_localhost = localhost_url.rstrip("/") + "/qrcode"
    qrcode_url_lan = lan_url.rstrip("/") + "/qrcode"

    print(f"服务器启动中...")
    print(f"=" * 60)
    print(f"【电脑访问地址】")
    print(f"  问卷地址：{localhost_url}")
    print(f"  二维码地址：{qrcode_url_localhost}")
    print(f"")
    print(f"【手机访问地址】（请确保手机和电脑在同一WiFi）")
    print(f"  问卷地址：{lan_url}")
    print(f"  二维码地址：{qrcode_url_lan}")
    print(f"=" * 60)
    print(f"调试模式：{'开启' if DEBUG_MODE else '关闭'}")
    print(f"注意：生产环境建议使用 gunicorn 或 uwsgi 运行")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE, threaded=True)
