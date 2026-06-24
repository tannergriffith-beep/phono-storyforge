import pytest
from app.agent import save_export_result
from google.adk.events import Event
from google.genai import types


class FakeSession:
    def __init__(self, events):
        self.events = events


class FakeCallbackContext:
    def __init__(self, events):
        self.session = FakeSession(events)
        self.state = {}


def _text_event(json_body: str) -> Event:
    part_text = types.Part.from_text(text=json_body)
    return Event(
        author="formatter_export_agent",
        content=types.Content(role="model", parts=[part_text]),
    )


@pytest.mark.asyncio
async def test_save_export_result_success() -> None:
    event = _text_event(
        '```json\n{\n  "doc_id": "real-doc-123",\n  "shareable_url": "https://docs.google.com/document/d/real-doc-123/edit"\n}\n```'
    )
    context = FakeCallbackContext([event])

    await save_export_result(context)

    assert context.state["export_result"]["doc_id"] == "real-doc-123"
    assert context.state["export_result"]["shareable_url"] == (
        "https://docs.google.com/document/d/real-doc-123/edit"
    )


@pytest.mark.asyncio
async def test_save_export_result_missing_doc_id() -> None:
    event = _text_event(
        '```json\n{\n  "shareable_url": "https://docs.google.com/document/d/real-doc-123/edit"\n}\n```'
    )
    context = FakeCallbackContext([event])

    with pytest.raises(ValueError) as excinfo:
        await save_export_result(context)

    assert "Google Workspace Document Export FAILED" in str(excinfo.value)


@pytest.mark.asyncio
async def test_save_export_result_missing_shareable_url() -> None:
    """Regression test for the silent-failure bug.

    Before the fix, `save_export_result` only validated `doc_id`. A response
    with a real `doc_id` but a missing/unparseable `shareable_url` would save
    `shareable_url: "unknown"` to state without raising — letting the pipeline
    continue to `parent_report_agent`, which embeds that "unknown" value as a
    broken link in the parent-facing letter. This must halt the pipeline
    instead, the same as a missing `doc_id` does.
    """
    event = _text_event('```json\n{\n  "doc_id": "real-doc-123"\n}\n```')
    context = FakeCallbackContext([event])

    with pytest.raises(ValueError) as excinfo:
        await save_export_result(context)

    assert "Google Workspace Document Export FAILED" in str(excinfo.value)


@pytest.mark.asyncio
async def test_save_export_result_no_agent_response() -> None:
    context = FakeCallbackContext([])

    with pytest.raises(ValueError) as excinfo:
        await save_export_result(context)

    assert "Google Workspace Document Export FAILED" in str(excinfo.value)
