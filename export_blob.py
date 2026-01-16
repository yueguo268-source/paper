import sqlite3
import os

DB_PATH = "survey.db"
EXPORT = "exported_files"
os.makedirs(EXPORT, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, file_name, file_blob, file_type FROM survey_records WHERE file_blob IS NOT NULL")
rows = cur.fetchall()
conn.close()

for rid, fname, blob, ftype in rows:
    if not fname:
        fname = f"unknown_{rid}"

    safe_name = f"{rid}_{fname}"
    out = os.path.join(EXPORT, safe_name)

    with open(out, "wb") as f:
        f.write(blob)

    print(f"[OK] 导出：{out}   类型：{ftype}")

print(f"\n全部导出完成，共 {len(rows)} 个。输出目录：{EXPORT}")
