import sqlite3
import requests
import time
import json
import zipfile

# -----------------------------
# 設定
# -----------------------------
db_file = "metadata.db"
sleep_interval = 0.5

# メールアドレス（連絡先）
contact_email = os.environ.get("CONTACT_EMAIL", "example@example.com")
# HTTPヘッダー
headers = {
    "User-Agent": f"DataCiteCollector/1.0 ({contact_email})"
}

# JSON出力（ZIP）
zip_output_file = "identifiers_metadata.zip"

# -----------------------------
# DB接続
# -----------------------------
conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

# -----------------------------
# 時間計測開始
# -----------------------------
start_time = time.time()

# -----------------------------
# 未登録identifier取得
# -----------------------------
cursor.execute("""
SELECT DISTINCT
    r.related_identifier,
    r.related_identifier_type
FROM related_identifiers r
LEFT JOIN identifiers i
ON r.related_identifier = i.identifier
WHERE i.identifier IS NULL
""")

targets = cursor.fetchall()
print(f"未登録identifier数: {len(targets)}")

# -----------------------------
# API関数
# -----------------------------
def fetch_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return None

    data = r.json().get("message", {})
    return data.get("type", None)


def fetch_datacite(doi):
    url = f"https://api.datacite.org/dois/{doi}"
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return None

    data = r.json().get("data", {}).get("attributes", {})
    return data.get("types", {}).get("resourceType", None)


# -----------------------------
# メイン処理
# -----------------------------
count = 0

# 保存用（JSON出力用）
results = []

for identifier, id_type in targets:

    resource_type = None
    source = None

    # -------------------------
    # DOIの場合
    # -------------------------
    if id_type == "DOI" and identifier.startswith("10."):

        # Crossref優先
        resource_type = fetch_crossref(identifier)

        if resource_type:
            source = "Crossref"
        else:
            # fallback DataCite
            resource_type = fetch_datacite(identifier)
            if resource_type:
                source = "DataCite"

    # -------------------------
    # URLの場合
    # -------------------------
    elif id_type == "URL":
        resource_type = None
        source = "Unknown"

    # -------------------------
    # DB登録
    # -----------------------------
    cursor.execute("""
        INSERT OR IGNORE INTO identifiers (
            identifier,
            identifier_type,
            resource_type,
            source
        ) VALUES (?, ?, ?, ?)
    """, (
        identifier,
        id_type,
        resource_type,
        source
    ))

    # JSON保存用
    results.append({
        "identifier": identifier,
        "identifier_type": id_type,
        "resource_type": resource_type,
        "source": source
    })

    count += 1

    if count % 50 == 0:
        print(f"{count} 件処理")

    time.sleep(sleep_interval)

# -----------------------------
# ZIP保存（JSON）
# -----------------------------
with zipfile.ZipFile(zip_output_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    zf.writestr("identifiers_metadata.json", json_str)

# -----------------------------
# 保存
# -----------------------------
conn.commit()
conn.close()

# -----------------------------
# 時間計測終了
# -----------------------------
elapsed = time.time() - start_time
minutes = int(elapsed // 60)
seconds = elapsed % 60

print(f"完了: {count} 件処理")
print(f"経過時間: {minutes}分 {seconds:.2f}秒")
print(f"ZIP保存: {zip_output_file}")
