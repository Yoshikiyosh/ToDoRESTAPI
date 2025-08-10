# Level2: ToDo REST API

FastAPI + Clean Architecture による ToDo REST API の実装

## セットアップ

```bash
pip install -r requirements.txt
```

## 実行

```bash
uvicorn main:app --reload
```

## API ドキュメント

http://localhost:8000/docs にアクセスして OpenAPI ドキュメントを確認できます。

## ディレクトリ構造

```
ToDoRESTAPI/
├── domain/                    # ドメインレイヤ
│   ├── entities/             # エンティティ
│   └── repositories/         # リポジトリ抽象
├── usecases/                 # ユースケースレイヤ
├── infra/                    # インフラレイヤ
│   └── db/                   # データベース関連
├── interfaces/               # インターフェースレイヤ
│   └── api/                  # API関連
├── configs/                  # 設定
├── tests/                    # テスト
└── main.py                   # エントリーポイント
```

## API エンドポイント

- `GET /api/v1/todos` - ToDo 一覧取得
- `POST /api/v1/todos` - ToDo 作成
- `GET /api/v1/todos/{id}` - ToDo 取得
- `PATCH /api/v1/todos/{id}` - ToDo 更新
- `DELETE /api/v1/todos/{id}` - ToDo 削除

## 使用例

```bash
# ToDo 作成
curl -X POST http://localhost:8000/api/v1/todos \
  -H 'Content-Type: application/json' \
  -d '{"title":"Buy milk","priority":1,"tags":["home"]}'

# 一覧取得
curl 'http://localhost:8000/api/v1/todos?is_done=false&sort=-priority'

# 更新
curl -X PATCH http://localhost:8000/api/v1/todos/1 \
  -H 'Content-Type: application/json' \
  -d '{"is_done":true}'

# 削除
curl -X DELETE http://localhost:8000/api/v1/todos/1
```
