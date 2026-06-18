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

## 1. 必要なライブラリのインストール

```bash
pip install requests
