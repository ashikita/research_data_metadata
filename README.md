# DataCite API → SQLite 保存手順

このリポジトリでは、DataCite APIを利用して研究データのメタデータを取得し、SQLiteデータベースに保存する手順をまとめています。

---

## 概要

本手順では以下の流れでデータを構築します：

1. DataCite APIから研究データのメタデータを取得
2. relatedIdentifiersを分離してSQLiteに格納
3. 外部API（Crossref / DataCite）を用いて関連識別子のリソースタイプを取得
4. データと論文の関係を構造化する

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

### 注意点

メインテーブル（datasets）と子テーブル（related_identifiers）は、データ間の対応関係（参照整合性）を保ち、不正なデータ（存在しないDOI）を防ぐために外部キーで関連付けている。 
SQLiteの外部キー制約はデフォルトで無効のため、SQLite起動後に毎回以下を実行して外部キー制約を有効化する必要がある。 
```sql
-- SQLite起動後すぐ実行
PRAGMA foreign_keys = ON;
```
Pythonで実行する場合: 
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

### 6-1. 設定

get_metadata.pyを開いて設定変更

```bash
contact_email = "your_email@example.com"
```
* User-Agentにメールアドレスを含めることで利用者を識別可能にし、API提供者に配慮したアクセスを行います。

必要に応じてフィルタリング設定を変更してください。

* リソースタイプ: dataset
* 出版年: 2025
* 関連情報のrelation type属性: IsSupplementTo
* 除外する出版者
    * HEPData
    * Cambridge Crystallographic Data Centre
    * National Institute for Fusion Science (NIFS)
    * UC San Diego Library Digital Collections

### 6-2. 実行

Pythonコードにより取得したメタデータをmetadata.dbとraw_metadata_2025.jsonに保存します。

```bash
python get_metadata.py
```

### 6-3. 設定を変えて再実行

get_metadata.py を以下通りに修正して再度実行してください。

```python
filter_relation_type = "IsReferencedBy"
```
```bash
python get_metadata.py
```

### 6-3. 関連識別子のリソースタイプを取得

関連識別子（DOIやURL）に対して、Crossref / DataCite API から resource_type を取得し、identifiersテーブルに格納する

```bash
python get_resource_type.py
```

### 補足: relationTypeの意味

- IsSupplementTo: データが論文の補足資料である
- IsReferencedBy: データが論文に引用されている
- IsPartOf / HasPart: データ同士の構成関係
