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

## 1. 仮想環境の導入

```bash
python3 -m venv venv
source venv/bin/activate

