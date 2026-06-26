import requests
import sqlite3
import json
import time
import zipfile
import os
from datetime import datetime

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
contact_email = os.environ.get("CONTACT_EMAIL", "example@example.com")
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

json_base_name = "raw_metadata"
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
            # 修正：リストとの比較 → in を使う
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
# JSON保存（ZIP圧縮）
# -----------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_output_file = f"{json_base_name}_{published_year}_{timestamp}.json"
zip_output_file = f"{json_base_name}_{published_year}_{timestamp}.zip"

with zipfile.ZipFile(zip_output_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    # JSONを文字列として生成
    json_str = json.dumps(all_data, ensure_ascii=False, indent=2)

    # ZIP内ファイルとして保存
    zf.writestr(os.path.basename(json_output_file), json_str)

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
print(f"JSON/ZIP保存: {zip_output_file}")
print(f"DB保存: {db_file}")
