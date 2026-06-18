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

```sql
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

```sql
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
```sql
CREATE UNIQUE INDEX uniq_rel
ON related_identifiers(doi, related_identifier, relation_type);
```

### 3-3. リソースタイプテーブル

```sql
CREATE TABLE identifiers (
    identifier TEXT PRIMARY KEY,
    identifier_type TEXT,
    resource_type TEXT,
    source TEXT
);
```

### 3-4. 注意点

メインテーブル（datasets）と子テーブル（related_identifiers）は、データ間の対応関係（参照整合性）を保ち、不正なデータ（存在しないDOI）を防ぐために外部キーで関連付けている。 
SQLiteの外部キー制約はデフォルトで無効のため、SQLite起動後に毎回以下を実行して外部キー制約を有効化する必要がある。 
```sql
-- SQLite起動後すぐ実行
PRAGMA foreign_keys = ON;
```
Python
```python
conn.execute("PRAGMA foreign_keys = ON;")
```

## 4. 仮想環境の導入

```bash
python3 -m venv venv
source venv/bin/activate
```

## 5. 必要なライブラリのインストール

```bash
pip install requests
```

## 6. メタデータの取得

### 6-1. relationType が 'IsSupplementTo' の条件で取得

code_01.py を以下通りに修正して実行
```
filter_relation_type = "IsSupplementTo"
```
```bash
python code_01.py
```
### 6-2. relationType が 'IsReferencedBy' の条件で取得

code_01.py を以下通りに修正して実行 
```
filter_relation_type = "IsReferencedBy"
```
```bash
python code_01.py
```

### 6-3. 関連識別子のリソースタイプを取得

```bash
python code_02.py
```
