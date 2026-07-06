from shared.llm.providers import DeepSeekClient


def test_deepseek_client_uses_chat_completions_and_maps_json_format():
    class FakeResponse:
        def __init__(self):
            self.choices = [type("Choice", (), {"message": type("Message", (), {"content": '{"ok":true}'})()})()]

        def model_dump(self):
            return {"id": "fake-response"}

    class FakeCompletions:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return FakeResponse()

    fake_completions = FakeCompletions()
    fake_client = type(
        "FakeClient",
        (),
        {"chat": type("FakeChat", (), {"completions": fake_completions})()},
    )()

    client = object.__new__(DeepSeekClient)
    client.provider = "deepseek"
    client.model = "deepseek-chat"
    client.client = fake_client

    result = client.generate(
        "classify this product",
        temperature=0,
        text={"format": {"type": "json_object"}},
    )

    assert result["text"] == '{"ok":true}'
    assert fake_completions.calls[0]["model"] == "deepseek-chat"
    assert fake_completions.calls[0]["messages"] == [{"role": "user", "content": "classify this product"}]
    assert fake_completions.calls[0]["response_format"] == {"type": "json_object"}
