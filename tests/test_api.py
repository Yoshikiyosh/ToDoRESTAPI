import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app


class TestTodoAPI:
    """Todo API のテスト"""
    
    def test_root_endpoint(self, client: TestClient):
        """ルートエンドポイントのテスト"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "api" in data
    
    def test_health_check(self, client: TestClient):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_create_todo_success(self, client: TestClient):
        """Todo 作成の成功テスト"""
        todo_data = {
            "title": "Test Todo",
            "description": "Test Description",
            "priority": 1,
            "tags": ["work", "test"]
        }
        
        response = client.post("/api/v1/todos", json=todo_data)
        assert response.status_code == 201
        
        # Location ヘッダの確認
        assert "Location" in response.headers
        
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"
        assert data["is_done"] is False
        assert data["priority"] == 1
        assert data["tags"] == ["work", "test"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_todo_minimal(self, client: TestClient):
        """最小限のデータでの Todo 作成テスト"""
        todo_data = {"title": "Minimal Todo"}
        
        response = client.post("/api/v1/todos", json=todo_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "Minimal Todo"
        assert data["description"] is None
        assert data["is_done"] is False
        assert data["priority"] == 0
        assert data["tags"] == []
    
    def test_create_todo_validation_error(self, client: TestClient):
        """Todo 作成のバリデーションエラーテスト"""
        # 空のタイトル
        response = client.post("/api/v1/todos", json={"title": ""})
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        
        # 無効な優先度
        response = client.post("/api/v1/todos", json={
            "title": "Test",
            "priority": 10
        })
        assert response.status_code == 422
    
    def test_get_todo_success(self, client: TestClient):
        """Todo 取得の成功テスト"""
        # まず Todo を作成
        create_response = client.post("/api/v1/todos", json={
            "title": "Test Todo",
            "description": "Test Description"
        })
        todo_id = create_response.json()["id"]
        
        # 取得
        response = client.get(f"/api/v1/todos/{todo_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"
    
    def test_get_todo_not_found(self, client: TestClient):
        """存在しない Todo 取得のテスト"""
        response = client.get("/api/v1/todos/999999")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
    
    def test_update_todo_success(self, client: TestClient):
        """Todo 更新の成功テスト"""
        # まず Todo を作成
        create_response = client.post("/api/v1/todos", json={
            "title": "Original Title",
            "priority": 1
        })
        todo_id = create_response.json()["id"]
        
        # 更新
        update_data = {
            "title": "Updated Title",
            "is_done": True,
            "priority": 3
        }
        response = client.patch(f"/api/v1/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["is_done"] is True
        assert data["priority"] == 3
    
    def test_update_todo_not_found(self, client: TestClient):
        """存在しない Todo 更新のテスト"""
        response = client.patch("/api/v1/todos/999999", json={
            "title": "Updated"
        })
        assert response.status_code == 404
    
    def test_delete_todo_success(self, client: TestClient):
        """Todo 削除の成功テスト"""
        # まず Todo を作成
        create_response = client.post("/api/v1/todos", json={
            "title": "To be deleted"
        })
        todo_id = create_response.json()["id"]
        
        # 削除
        response = client.delete(f"/api/v1/todos/{todo_id}")
        assert response.status_code == 204
        
        # 削除後に取得を試みる
        get_response = client.get(f"/api/v1/todos/{todo_id}")
        assert get_response.status_code == 404
    
    def test_delete_todo_not_found(self, client: TestClient):
        """存在しない Todo 削除のテスト"""
        response = client.delete("/api/v1/todos/999999")
        assert response.status_code == 404
    
    def test_list_todos_empty(self, client: TestClient):
        """空の Todo リスト取得テスト"""
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_items"] == 0
        assert data["total_pages"] == 0
    
    def test_list_todos_with_data(self, client: TestClient):
        """Todo リスト取得テスト（データあり）"""
        # 複数の Todo を作成
        todos = [
            {"title": "Todo 1", "priority": 1},
            {"title": "Todo 2", "priority": 2},
            {"title": "Todo 3", "priority": 0}
        ]
        
        for todo_data in todos:
            client.post("/api/v1/todos", json=todo_data)
        
        # リスト取得
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total_items"] == 3
        assert data["total_pages"] == 1
    
    def test_list_todos_pagination(self, client: TestClient):
        """Todo リストのページネーションテスト"""
        # 複数の Todo を作成
        for i in range(5):
            client.post("/api/v1/todos", json={"title": f"Todo {i}"})
        
        # 1ページ目（サイズ2）
        response = client.get("/api/v1/todos?page=1&page_size=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_items"] == 5
        assert data["total_pages"] == 3
        
        # 2ページ目
        response = client.get("/api/v1/todos?page=2&page_size=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
    
    def test_list_todos_filter_by_done(self, client: TestClient):
        """完了状態でのフィルタリングテスト"""
        # 完了と未完了の Todo を作成
        client.post("/api/v1/todos", json={"title": "Todo 1"})
        
        create_response = client.post("/api/v1/todos", json={"title": "Todo 2"})
        todo_id = create_response.json()["id"]
        client.patch(f"/api/v1/todos/{todo_id}", json={"is_done": True})
        
        # 未完了のみ取得
        response = client.get("/api/v1/todos?is_done=false")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_done"] is False
        
        # 完了のみ取得
        response = client.get("/api/v1/todos?is_done=true")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_done"] is True
    
    def test_list_todos_search(self, client: TestClient):
        """フリーテキスト検索のテスト"""
        # 異なるタイトルの Todo を作成
        client.post("/api/v1/todos", json={
            "title": "Buy milk",
            "description": "From the store"
        })
        client.post("/api/v1/todos", json={
            "title": "Call doctor",
            "description": "About appointment"
        })
        
        # タイトルで検索
        response = client.get("/api/v1/todos?q=milk")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert "milk" in data["items"][0]["title"].lower()
        
        # 説明で検索
        response = client.get("/api/v1/todos?q=appointment")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert "appointment" in data["items"][0]["description"].lower()
    
    def test_list_todos_sort(self, client: TestClient):
        """ソート機能のテスト"""
        # 異なる優先度の Todo を作成
        client.post("/api/v1/todos", json={"title": "Low", "priority": 1})
        client.post("/api/v1/todos", json={"title": "High", "priority": 5})
        client.post("/api/v1/todos", json={"title": "Medium", "priority": 3})
        
        # 優先度降順でソート
        response = client.get("/api/v1/todos?sort=-priority")
        assert response.status_code == 200
        
        data = response.json()
        priorities = [item["priority"] for item in data["items"]]
        assert priorities == [5, 3, 1]  # 降順
        
        # 優先度昇順でソート
        response = client.get("/api/v1/todos?sort=priority")
        assert response.status_code == 200
        
        data = response.json()
        priorities = [item["priority"] for item in data["items"]]
        assert priorities == [1, 3, 5]  # 昇順
