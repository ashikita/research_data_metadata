import sqlite3
import requests
import time

# -----------------------------
# 設定
# -----------------------------
db_file = "metadata.db"
sleep_interval = 0.5

# -----------------------------
# DB接続
# -----------------------------
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

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
    r = requests.get(url)

    if r.status_code != 200:
        return None

    data = r.json().get("message", {})
    return data.get("type", None)


def fetch_datacite(doi):
    url = f"https://api.datacite.org/dois/{doi}"
    r = requests.get(url)

    if r.status_code != 200:
        return None

    data = r.json().get("data", {}).get("attributes", {})
    return data.get("types", {}).get("resourceType", None)


# -----------------------------
# メイン処理
# -----------------------------
count = 0

for identifier, id_type in targets:

    resource_type = None
    source = None

    # -------------------------
    # DOIの場合
    # -------------------------
    if id_type == "DOI" and identifier.startswith("10."):
        
        # ① Crossrefを優先
        resource_type = fetch_crossref(identifier)

        if resource_type:
            source = "Crossref"
        else:
            # ② fallbackでDataCite
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

    count += 1

    if count % 50 == 0:
        print(f"{count} 件処理")

    time.sleep(sleep_interval)

# -----------------------------
# 保存
# -----------------------------
conn.commit()
conn.close()

print(f"完了: {count} 件処理")