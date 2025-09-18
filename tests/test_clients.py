import pytest

from ttsfm.client import TTSClient
from ttsfm.async_client import AsyncTTSClient
from ttsfm.models import TTSResponse, AudioFormat


def _mk_response(data: bytes) -> TTSResponse:
    return TTSResponse(
        audio_data=data,
        content_type="audio/mpeg",
        format=AudioFormat.MP3,
        size=len(data),
    )


def test_sync_long_text_auto_combine(monkeypatch):
    client = TTSClient()

    monkeypatch.setattr(
        client,
        "generate_speech_batch",
        lambda **kwargs: [_mk_response(b"one"), _mk_response(b"two")],
    )

    combined_flag = {}

    def fake_combine(responses):
        combined_flag["called"] = True
        return _mk_response(b"onetwo")

    monkeypatch.setattr("ttsfm.client.combine_responses", fake_combine)

    result = client.generate_speech_long_text(
        text="dummy",
        auto_combine=True,
    )

    assert combined_flag["called"] is True
    assert isinstance(result, TTSResponse)
    assert result.audio_data == b"onetwo"


def test_sync_long_text_returns_list_without_auto_combine(monkeypatch):
    client = TTSClient()

    responses = [_mk_response(b"one")]
    monkeypatch.setattr(client, "generate_speech_batch", lambda **_: responses)

    result = client.generate_speech_long_text(text="dummy", auto_combine=False)

    assert result is responses


@pytest.mark.asyncio
async def test_async_long_text_auto_combine(monkeypatch):
    client = AsyncTTSClient()

    async def fake_batch(**kwargs):
        return [_mk_response(b"one"), _mk_response(b"two")]

    monkeypatch.setattr(client, "generate_speech_batch", fake_batch)

    def fake_combine(responses):
        return _mk_response(b"onetwo")

    monkeypatch.setattr("ttsfm.async_client.combine_responses", fake_combine)

    result = await client.generate_speech_long_text(
        text="dummy",
        auto_combine=True,
    )

    assert isinstance(result, TTSResponse)
    assert result.audio_data == b"onetwo"
