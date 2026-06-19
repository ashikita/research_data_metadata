import requests
import sqlite3
import json
import time

# -----------------------------
# 設定
# -----------------------------
resource_type_id = "dataset"
published_year = "2025"
page_size = 100
sleep_interval = 1.0
max_records = 20000

filter_relation_types = ["IsSupplementTo", "IsReferencedBy"]

# メールアドレス（連絡先）
contact_email = "your_email@example.com"

# HTTPヘッダー
headers = {
    "User-Agent": f"DataCiteCollector/1.0 ({contact_email})"
}

exclude_publishers = [
    "HEPData",
    "Cambridge Crystallographic Data Centre",
    "National Institute for Fusion Science (NIFS)",
    "UC San Diego Library Digital Collections"
]

json_output_file = "raw_metadata.json"
db_file = "metadata.db"

# -----------------------------
# DB接続
# -----------------------------
conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

# -----------------------------
# API URL
# -----------------------------
base_url = (
    "https://api.datacite.org/dois?"
    f"resource-type-id={resource_type_id}&"
    f"published={published_year}&"
    f"page[size]={page_size}"
)

# -----------------------------
# 時間計測開始
# -----------------------------
start_time = time.time()

# -----------------------------
# データ取得
# -----------------------------
all_data = []
total_count = 0
url = base_url

while url and total_count < max_records:
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"取得失敗: {response.status_code}")
        break

    data = response.json()
    all_data.extend(data.get("data", []))

    for item in data.get("data", []):
        if total_count >= max_records:
            break

        attr = item.get("attributes", {})

        doi = item.get("id", "")
        publisher = attr.get("publisher", "")
        if publisher in exclude_publishers:
            continue

        publication_year = attr.get("publicationYear", "")
        created = attr.get("created", "")
        registered = attr.get("registered", "")
        updated = attr.get("updated", "")

        resource_type = attr.get("types", {}).get("resourceType", "")

        # datasets
        cursor.execute("""
            INSERT OR IGNORE INTO datasets (
                doi, resource_type, created, registered,
                published, updated, publisher
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doi,
            resource_type,
            created,
            registered,
            str(publication_year),
            updated,
            publisher
        ))

        # related_identifiers
        for rel in attr.get("relatedIdentifiers", []):
            # ✅ 修正：リストとの比較 → in を使う
            if rel.get("relationType") in filter_relation_types:
                cursor.execute("""
                    INSERT OR IGNORE INTO related_identifiers (
                        doi,
                        related_identifier,
                        related_identifier_type,
                        relation_type
                    ) VALUES (?, ?, ?, ?)
                """, (
                    doi,
                    rel.get("relatedIdentifier", ""),
                    rel.get("relatedIdentifierType", ""),
                    rel.get("relationType", "")
                ))

        total_count += 1

    url = data.get("links", {}).get("next")

    if url and total_count < max_records:
        time.sleep(sleep_interval)

# -----------------------------
# JSON保存
# -----------------------------
with open(json_output_file, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

# -----------------------------
# 終了処理
# -----------------------------
conn.commit()
conn.close()

# -----------------------------
# 時間計測終了
# -----------------------------
elapsed_time = time.time() - start_time

print(f"完了: {total_count} 件処理")
print(f"経過時間: {elapsed_time:.2f} 秒")
print(f"JSON保存: {json_output_file}")
print(f"DB保存: {db_file}")