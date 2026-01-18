import io
import sys
import os

# Make sure the backend package is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_image_qa_captioning_success(monkeypatch):
    # Arrange: patch the captioner
    def fake_caption(b):
        return ("A dog wearing a blue collar sitting on grass", None)

    from backend.brain import image_services as isvc
    monkeypatch.setattr(isvc, "caption_image", fake_caption)

    # Act: send a fake image file and question
    files = {"file": ("dog.jpg", io.BytesIO(b"fakeimagebytes"), "image/jpeg")}
    data = {"question": "What color is the collar?", "chat_id": None}

    res = client.post("/image_qa", files=files, data=data)

    # Assert
    assert res.status_code == 200
    payload = res.json()
    assert "response" in payload
    assert payload["response"] != ""
    assert payload["chat_id"] is not None
    assert "collar" in payload["response"].lower() or "blue" in payload["response"].lower()


def test_image_qa_captioning_unavailable(monkeypatch):
    # Simulate captioner returning None
    def fake_caption(b):
        return (None, "no model")

    from backend.brain import image_services as isvc
    monkeypatch.setattr(isvc, "caption_image", fake_caption)

    files = {"file": ("dog.jpg", io.BytesIO(b"fakeimagebytes"), "image/jpeg")}
    data = {"question": "Count objects", "chat_id": None}

    res = client.post("/image_qa", files=files, data=data)

    assert res.status_code == 200
    payload = res.json()
    assert "attempted to process the image" in payload["response"].lower()
