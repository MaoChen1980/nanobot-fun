"""Tests for nanobot.providers.transcription — OpenAI and Groq Whisper providers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nanobot.providers.transcription import (
    GroqTranscriptionProvider,
    OpenAITranscriptionProvider,
)


# ---------------------------------------------------------------------------
# OpenAITranscriptionProvider
# ---------------------------------------------------------------------------

class TestOpenAITranscriptionProvider:
    def test_default_api_key_from_env(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env-key"}, clear=True):
            p = OpenAITranscriptionProvider()
            assert p.api_key == "sk-env-key"

    def test_default_api_key_none_when_not_set(self):
        with patch.dict("os.environ", {}, clear=True):
            p = OpenAITranscriptionProvider()
            assert p.api_key is None

    def test_explicit_api_key_overrides_env(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env"}, clear=True):
            p = OpenAITranscriptionProvider(api_key="sk-explicit")
            assert p.api_key == "sk-explicit"

    def test_default_api_base(self):
        p = OpenAITranscriptionProvider()
        assert p.api_url == "https://api.openai.com/v1/audio/transcriptions"

    def test_api_base_from_env(self):
        with patch.dict("os.environ", {"OPENAI_TRANSCRIPTION_BASE_URL": "https://custom.example.com/transcribe"}):
            p = OpenAITranscriptionProvider()
            assert p.api_url == "https://custom.example.com/transcribe"

    def test_explicit_api_base_overrides_env(self):
        p = OpenAITranscriptionProvider(api_base="https://explicit.example.com/audio")
        assert p.api_url == "https://explicit.example.com/audio"

    def test_language_set(self):
        p = OpenAITranscriptionProvider(language="zh")
        assert p.language == "zh"

    @pytest.mark.asyncio
    async def test_transcribe_no_api_key_returns_empty(self):
        p = OpenAITranscriptionProvider(api_key=None)
        result = await p.transcribe("/tmp/test.mp3")
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found_returns_empty(self, tmp_path):
        p = OpenAITranscriptionProvider(api_key="sk-test")
        result = await p.transcribe(tmp_path / "nonexistent.mp3")
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_success(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")
        p = OpenAITranscriptionProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "hello world"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_transcribe_with_language(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = OpenAITranscriptionProvider(api_key="sk-test", language="zh")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "你好"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == "你好"

    @pytest.mark.asyncio
    async def test_transcribe_http_error_returns_empty(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = OpenAITranscriptionProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_network_error_returns_empty(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = OpenAITranscriptionProvider(api_key="sk-test")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection failed"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_missing_text_key_returns_empty(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = OpenAITranscriptionProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""


# ---------------------------------------------------------------------------
# GroqTranscriptionProvider
# ---------------------------------------------------------------------------

class TestGroqTranscriptionProvider:
    def test_default_api_key_from_env(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk-env-key"}, clear=True):
            p = GroqTranscriptionProvider()
            assert p.api_key == "gsk-env-key"

    def test_default_api_key_none_when_not_set(self):
        with patch.dict("os.environ", {}, clear=True):
            p = GroqTranscriptionProvider()
            assert p.api_key is None

    def test_default_api_base(self):
        p = GroqTranscriptionProvider()
        assert p.api_url == "https://api.groq.com/openai/v1/audio/transcriptions"

    def test_api_base_from_env(self):
        with patch.dict("os.environ", {"GROQ_BASE_URL": "https://groq.custom.example.com"}):
            p = GroqTranscriptionProvider()
            assert p.api_url == "https://groq.custom.example.com"

    @pytest.mark.asyncio
    async def test_transcribe_no_api_key_returns_empty(self):
        p = GroqTranscriptionProvider(api_key=None)
        result = await p.transcribe("/tmp/test.mp3")
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found_returns_empty(self, tmp_path):
        p = GroqTranscriptionProvider(api_key="gsk-test")
        result = await p.transcribe(tmp_path / "nonexistent.mp3")
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_success(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")
        p = GroqTranscriptionProvider(api_key="gsk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "transcribed by groq"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == "transcribed by groq"

    @pytest.mark.asyncio
    async def test_transcribe_with_language(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = GroqTranscriptionProvider(api_key="gsk-test", language="en")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "hello"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_transcribe_http_error_returns_empty(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = GroqTranscriptionProvider(api_key="gsk-test")

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_network_error_returns_empty(self, tmp_path):
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake")
        p = GroqTranscriptionProvider(api_key="gsk-test")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("timeout"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""
