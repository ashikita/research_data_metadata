import sqlite3
import requests
import time
import os
import json

# -----------------------------
# 設定
# -----------------------------
db_file = "metadata.db"

# API待機時間
sleep_interval = 0.1

# SQLiteコミット間隔
commit_interval = 100

# JSONL書き込み間隔
jsonl_interval = 1000

jsonl_file = "identifiers_metadata.jsonl"

contact_email = os.environ.get(
    "CONTACT_EMAIL",
    "example@example.com"
)

headers = {
    "User-Agent": (
        f"DataCiteCollector/1.0 ({contact_email})"
    )
}

# -----------------------------
# DB接続
# -----------------------------
conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON;")
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
    ON lower(r.related_identifier)
       = lower(i.identifier)
WHERE i.identifier IS NULL
""")

targets = cursor.fetchall()

print(f"未登録identifier数: {len(targets):,}")

# -----------------------------
# API関数
# -----------------------------
def fetch_datacite(doi):

    url = f"https://api.datacite.org/dois/{doi}"

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        if r.status_code != 200:
            return None

        data = (
            r.json()
            .get("data", {})
            .get("attributes", {})
        )

        types = data.get("types", {})

        return {
            "resource_type":
                types.get("resourceType"),
            "resource_type_general":
                types.get("resourceTypeGeneral")
        }

    except requests.RequestException:
        return None


def fetch_crossref(doi):

    url = f"https://api.crossref.org/works/{doi}"

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        r.raise_for_status()

        data = r.json().get(
            "message",
            {}
        )

        return {
            "resource_type":
                data.get("type"),
            "resource_type_general":
                None
        }

    except requests.RequestException:
        return None


# -----------------------------
# メイン処理
# -----------------------------
count = 0
jsonl_buffer = []

try:

    for identifier, id_type in targets:

        resource_type = None
        resource_type_general = None
        source = None

        # DOI正規化
        if identifier:
            identifier = (
                identifier
                .strip()
                .lower()
            )

        # -------------------------
        # DOI
        # -------------------------
        if (
            id_type == "DOI"
            and identifier
            and identifier.startswith("10.")
            and "/" in identifier
        ):

            result = fetch_datacite(identifier)

            if result:

                resource_type = (
                    result["resource_type"]
                )

                resource_type_general = (
                    result["resource_type_general"]
                )

                source = "DataCite"

            else:

                result = fetch_crossref(identifier)

                if result:

                    resource_type = (
                        result["resource_type"]
                    )

                    resource_type_general = (
                        result["resource_type_general"]
                    )

                    source = "Crossref"

                else:

                    source = "Error"

        # -------------------------
        # URL
        # -------------------------
        elif id_type == "URL":

            resource_type = "Unknown"
            resource_type_general = "Unknown"
            source = "Unknown"

        # -------------------------
        # その他
        # -------------------------
        else:

            resource_type = "Unknown"
            resource_type_general = "Unknown"
            source = "Unknown"

        resource_type = (
            resource_type or "Unknown"
        )

        resource_type_general = (
            resource_type_general
            or "Unknown"
        )

        source = (
            source or "Unknown"
        )

        # -------------------------
        # SQLite保存
        # -------------------------
        cursor.execute("""
        INSERT OR IGNORE INTO identifiers (
            identifier,
            identifier_type,
            resource_type,
            resource_type_general,
            source
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            identifier,
            id_type,
            resource_type,
            resource_type_general,
            source
        ))

        # -------------------------
        # JSONLバッファ
        # -------------------------
        jsonl_buffer.append({
            "identifier": identifier,
            "identifier_type": id_type,
            "resource_type": resource_type,
            "resource_type_general":
                resource_type_general,
            "source": source
        })

        count += 1

        # -------------------------
        # SQLite Commit
        # -------------------------
        if count % commit_interval == 0:
            conn.commit()

        # -------------------------
        # JSONL Flush
        # -------------------------
        if count % jsonl_interval == 0:

            with open(
                jsonl_file,
                "a",
                encoding="utf-8"
            ) as f:

                for record in jsonl_buffer:

                    f.write(
                        json.dumps(
                            record,
                            ensure_ascii=False
                        )
                        + "\n"
                    )

            jsonl_buffer.clear()

            print(
                f"{count:,}/{len(targets):,} "
                f"({count / len(targets) * 100:.1f}%)"
            )

        time.sleep(sleep_interval)

except KeyboardInterrupt:

    print("\nCtrl+C を受信しました")
    print("途中結果を保存しています...")

finally:

    # SQLite保存
    conn.commit()

    # JSONL残り書き出し
    if jsonl_buffer:

        with open(
            jsonl_file,
            "a",
            encoding="utf-8"
        ) as f:

            for record in jsonl_buffer:

                f.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    )
                    + "\n"
                )

    conn.close()

print()
print(f"処理件数: {count:,}")
print(f"JSONL出力: {jsonl_file}")
