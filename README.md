# DataCite API → SQLite 保存手順

このリポジトリでは、DataCite APIを利用して研究データのメタデータを取得し、SQLiteデータベースに保存する手順をまとめています。

---

## 環境

- OS: Ubuntu (WSL)
- Python: 3.x
- 使用ライブラリ:
  - requests
  - sqlite3（標準ライブラリ）

---

## 1. SQLiteのインストール

```bash
sudo apt update
sudo apt install sqlite3
```
## 2. データベースの作成

```bash
sqlite3 metadata.db
```
## 3. テーブルの作成

### 3-1. メインテーブル

```
CREATE TABLE datasets (
    doi TEXT PRIMARY KEY,
    resource_type TEXT,
    publisher TEXT, 
    published TEXT,
    created TEXT,
    registered TEXT,
    updated TEXT
);
```

### 3-2. 関連識別子テーブル(子テーブル)

```
CREATE TABLE related_identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doi TEXT,
    related_identifier TEXT,
    related_identifier_type TEXT,
    relation_type TEXT,
    FOREIGN KEY (doi) REFERENCES datasets(doi)
);
```

重複防止
```
CREATE UNIQUE INDEX uniq_rel
ON related_identifiers(doi, related_identifier, relation_type);
```

### 補足

SQLiteの外部キー制約はデフォルトで無効のため、SQLite起動後に毎回以下を実行して外部キー制約を有効化する必要がある
```
-- SQLite起動後すぐ実行
PRAGMA foreign_keys = ON;
```
Python
```
conn.execute("PRAGMA foreign_keys = ON;")
```

### 3-3. リソースタイプテーブル

```
CREATE TABLE identifiers (
    identifier TEXT PRIMARY KEY,
    identifier_type TEXT,
    resource_type TEXT,
    source TEXT
);
```

## 3. 仮想環境の導入

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. 必要なライブラリのインストール

```bash
pip install requests
```




