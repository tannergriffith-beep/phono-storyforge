import pytest
from app.agent import save_parent_report
from google.adk.events import Event
from google.genai import types

class FakeSession:
    def __init__(self, events):
        self.events = events

class FakeCallbackContext:
    def __init__(self, events):
        self.session = FakeSession(events)
        self.state = {}

@pytest.mark.asyncio
async def test_save_parent_report_success() -> None:
    # Construct events with valid call and response
    part_text = types.Part.from_text(
        text='```json\n{\n  "parent_letter": "Warm letter [shareable_url]",\n  "reinforced_patterns": ["Pattern 1"],\n  "sight_words_to_practice": ["word1"]\n}\n```'
    )
    event_text = Event(
        author="parent_report_agent",
        content=types.Content(role="model", parts=[part_text])
    )
    
    part_call = types.Part.from_function_call(
        name="create_draft",
        args={"to": ["parent@example.com"], "subject": "Test", "body": "Body"}
    )
    event_call = Event(
        author="parent_report_agent",
        content=types.Content(role="model", parts=[part_call])
    )
    
    part_resp = types.Part.from_function_response(
        name="create_draft",
        response={"id": "mock-draft-12345"}
    )
    event_resp = Event(
        author="parent_report_agent",
        content=types.Content(role="user", parts=[part_resp])
    )
    
    context = FakeCallbackContext([event_call, event_resp, event_text])
    
    # Run callback
    await save_parent_report(context)
    
    assert context.state["parent_report"]["parent_letter"] == "Warm letter [shareable_url]"

@pytest.mark.asyncio
async def test_save_parent_report_missing_call() -> None:
    part_text = types.Part.from_text(
        text='```json\n{\n  "parent_letter": "Warm letter",\n  "reinforced_patterns": [],\n  "sight_words_to_practice": []\n}\n```'
    )
    event_text = Event(
        author="parent_report_agent",
        content=types.Content(role="model", parts=[part_text])
    )
    
    # Missing create_draft call and response
    context = FakeCallbackContext([event_text])
    
    with pytest.raises(ValueError) as excinfo:
        await save_parent_report(context)
        
    assert "The create_draft tool call was never invoked" in str(excinfo.value)

@pytest.mark.asyncio
async def test_save_parent_report_failed_response() -> None:
    part_text = types.Part.from_text(
        text='```json\n{\n  "parent_letter": "Warm letter",\n  "reinforced_patterns": [],\n  "sight_words_to_practice": []\n}\n```'
    )
    event_text = Event(
        author="parent_report_agent",
        content=types.Content(role="model", parts=[part_text])
    )
    
    part_call = types.Part.from_function_call(
        name="create_draft",
        args={"to": ["parent@example.com"], "subject": "Test", "body": "Body"}
    )
    event_call = Event(
        author="parent_report_agent",
        content=types.Content(role="model", parts=[part_call])
    )
    
    # Response contains error
    part_resp = types.Part.from_function_response(
        name="create_draft",
        response={"id": "unknown", "error": "API error"}
    )
    event_resp = Event(
        author="parent_report_agent",
        content=types.Content(role="user", parts=[part_resp])
    )
    
    context = FakeCallbackContext([event_text, event_call, event_resp])
    
    with pytest.raises(ValueError) as excinfo:
        await save_parent_report(context)
        
    assert "The create_draft tool call failed or returned an invalid ID" in str(excinfo.value)
