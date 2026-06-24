# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Force integration test mode to use mocked MCP tools
os.environ["INTEGRATION_TEST"] = "TRUE"

from app.agent import root_agent


def test_agent_stream() -> None:
    """Integration test for the agent stream functionality.
    
    Tests that the agent returns valid streaming responses.
    """
    session_service = InMemorySessionService()

    session = session_service.create_session_sync(user_id="test_user", app_name="app")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="app")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Why is the sky blue?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    has_text_content = False
    for event in events:
        if (
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
        ):
            has_text_content = True
            break
    assert has_text_content, "Expected at least one message with text content"


@pytest.mark.asyncio
async def test_pipeline_e2e() -> None:
    """Integration test for the full 7-agent pipeline.
    
    Runs root_agent end-to-end with mocked MCP tools and asserts that:
    - phonics_profile is populated correctly.
    - qa_feedback.is_decodable is True.
    - export_result has doc_id and shareable_url.
    - parent_report has all three fields populated.
    """
    session_service = InMemorySessionService()
    user_id = "test_user_e2e"
    session_id = "test_session_e2e"

    await session_service.create_session(app_name="app", user_id=user_id, session_id=session_id)
    runner = Runner(agent=root_agent, session_service=session_service, app_name="app")

    child_profile_input = (
        "I need a story for my 6-year-old child. "
        "Their reading target level is blends. "
        "They have mastered short_vowels and digraphs. "
        "Their known sight words are: the, was, to, she, a, of, is. "
        "Their topic of interest is space."
    )

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=child_profile_input)]
    )

    # Run the pipeline to completion
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        pass

    # Inspect final session state
    session = await session_service.get_session(app_name="app", user_id=user_id, session_id=session_id)
    state = session.state

    # 1. Assert Phonics Profile is populated correctly
    profile = state.get("phonics_profile")
    assert profile is not None
    assert profile.get("age") == 6
    assert profile.get("target_level") == "blends"
    assert "short_vowels" in profile.get("mastered_levels")
    assert "digraphs" in profile.get("mastered_levels")
    assert "space" in profile.get("interest").lower()

    # 2. Assert Phonics QA feedback is decodable
    qa_feedback = state.get("qa_feedback")
    assert qa_feedback is not None
    assert qa_feedback.get("is_decodable") is True

    # 3. Assert Export Result has doc_id and shareable_url
    export_result = state.get("export_result")
    assert export_result is not None
    assert "doc_id" in export_result
    assert "shareable_url" in export_result
    assert export_result.get("doc_id") != "unknown"
    assert export_result.get("shareable_url") != "unknown"

    # 4. Assert Parent Report has all three fields populated
    parent_report = state.get("parent_report")
    assert parent_report is not None
    assert "parent_letter" in parent_report
    assert "reinforced_patterns" in parent_report
    assert "sight_words_to_practice" in parent_report
    assert parent_report.get("parent_letter") != "unknown"


@pytest.mark.asyncio
async def test_pipeline_failure_path() -> None:
    """Integration test verifying the failure path.
    
    Provides an impossible phonics profile (target_level = vowel_teams, no mastered levels).
    Asserts that the pipeline exits by raising a ValueError, preventing exporting.
    """
    session_service = InMemorySessionService()
    user_id = "test_user_fail"
    session_id = "test_session_fail"

    await session_service.create_session(app_name="app", user_id=user_id, session_id=session_id)
    runner = Runner(agent=root_agent, session_service=session_service, app_name="app")

    # Nearly impossible profile: target is vowel_teams but nothing is mastered (not even short vowels),
    # and the child's interest is extremely complex, and they know zero sight words.
    impossible_input = (
        "Write a story for my 13-year-old child. "
        "Their reading target level is vowel_teams. "
        "They have mastered absolutely nothing, not even short vowels. "
        "They are interested in photosynthesizing chloroplasts in prehistoric vegetation. "
        "No sight words."
    )

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=impossible_input)]
    )

    # Verify that ValueError is raised during async execution
    with pytest.raises(ValueError) as excinfo:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            pass
            
    assert "Phonics Guardrail Validation FAILED" in str(excinfo.value)
