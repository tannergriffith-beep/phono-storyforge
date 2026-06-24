# app/agent.py
#
# =============================================================================
# CAPSTONE CONCEPT 1: Multi-agent systems built with ADK
# This file constructs a Sequential multi-agent pipeline containing a Loop agent:
#   SequentialAgent (root_agent)
#     ├── intake_agent (LlmAgent)
#     ├── story_planner (LlmAgent)
#     └── LoopAgent (writer_qa_loop)
#           ├── writer_agent (LlmAgent)
#           └── qa_agent (PhonicsQAAgent - custom BaseAgent)
#
# CAPSTONE CONCEPT 4: Security Features
# The PhonicsQAAgent acts as a loop-based security guardrail. It checks every
# word against allowed phonics levels and sight words. The loop is forced to
# repeat, directing the writer to revise, until the security check passes (is_decodable = True).
# =============================================================================

from __future__ import annotations
import asyncio
import os
import json
from typing import AsyncGenerator

from google.adk.agents import Agent, BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event, EventActions
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from app.schemas import (
    PhonicsProfile,
    StoryOutline,
    StoryDraft,
    QAFeedback,
    PageIllustration,
    StoryIllustrations,
    ExportResult,
    ParentReport,
)
from app.tools import check_decodability

# Configure Gemini Model options
MODEL_NAME = "gemini-flash-lite-latest"
gemini_model = Gemini(
    model=MODEL_NAME,
    retry_options=types.HttpRetryOptions(attempts=3),
)

# ---------------------------------------------------------------------------
# Callbacks: Rate Limiting and State Initialization
# ---------------------------------------------------------------------------
async def rate_limit_delay(callback_context: CallbackContext) -> None:
    """Delays execution to respect Gemini API free tier rate limits."""
    print("\n--- [Rate Limit Guard] Sleeping 5 seconds before calling LLM... ---")
    await asyncio.sleep(5)

async def init_loop_state(callback_context: CallbackContext) -> None:
    """Pre-populates draft and feedback keys in the state.

    This prevents KeyError failures when formatting system instructions
    before the first iteration of the LoopAgent.
    Also respects rate limit by sleeping.
    """
    print("\n--- [Rate Limit Guard] Sleeping 5 seconds before calling LLM... ---")
    await asyncio.sleep(5)
    if "story_draft" not in callback_context.state:
        callback_context.state["story_draft"] = {
            "title": "Untitled Book",
            "pages": [],
            "notes": "No draft generated yet."
        }
    if "qa_feedback" not in callback_context.state:
        callback_context.state["qa_feedback"] = {
            "is_decodable": False,
            "violations": [],
            "feedback_report": "This is the first iteration. Generate a brand new story based on the outline."
        }

# ---------------------------------------------------------------------------
# Agent 1: Intake Agent
# ---------------------------------------------------------------------------
intake_instruction = """You are the Phono StoryForge Intake Agent.
Your job is to take a child's raw reading profile information and format it into a structured PhonicsProfile JSON object.

Based on the user's message, identify and populate:
- target_level: The specific next phonics level they are working on. Must be one of: 'short_vowels', 'digraphs', 'blends', 'silent_e', 'r_controlled', 'vowel_teams'.
- mastered_levels: A list of all phonics levels they have already mastered. If they have mastered a level, they have also mastered all levels below it in the sequence:
  Sequence: short_vowels -> digraphs -> blends -> silent_e -> r_controlled -> vowel_teams
  So if the user says they mastered 'blends', their mastered_levels list must include: ['short_vowels', 'digraphs', 'blends'].
- sight_words: A list of words they know by sight. Clean them of punctuation.
- interest: Their core topic of interest (e.g., 'dinosaurs', 'space').
- age: Their age as an integer.
- reading_level: Their general reading level classification (e.g., 'early reader').

Provide a valid JSON response matching the PhonicsProfile schema.
"""

intake_agent = Agent(
    name="intake_agent",
    model=gemini_model,
    instruction=intake_instruction,
    output_schema=PhonicsProfile,
    output_key="phonics_profile"
)

# ---------------------------------------------------------------------------
# Agent 2: Story Planner Agent
# ---------------------------------------------------------------------------
planner_instruction = """You are the Phono StoryForge Story Planner Agent.
Your job is to draft a short story outline for a child, based on their phonics profile.

Phonics Profile: {phonics_profile}

Based on the child's age, interests, and phonics profile, design:
1. A catchy title that is easy to read.
2. 1-2 main characters with simple, decodable names (e.g., 'Sam', 'Chip', 'Ned', 'Fred').
3. A simple setting.
4. 4 to 6 page-by-page plot beats.
5. The specific target phonics sounds you will reinforce.

CRITICAL RULES:
- The plot beats must be very simple and tell a story that can be written using only the child's mastered phonics patterns and sight words.
- Do NOT plan plot beats that require complex vocabulary or sounds the child has not mastered.

Provide a valid JSON response matching the StoryOutline schema.
"""

story_planner = Agent(
    name="story_planner",
    model=gemini_model,
    instruction=planner_instruction,
    output_schema=StoryOutline,
    output_key="story_outline",
    before_agent_callback=rate_limit_delay
)

# ---------------------------------------------------------------------------
# Agent 3: Decodable Writer Agent (Inner Loop Agent)
# ---------------------------------------------------------------------------
writer_instruction = """You are the Phono StoryForge Decodable Writer Agent.
Your job is to write a page-by-page storybook based on the outline and the child's phonics profile.

Phonics Profile: {phonics_profile}
Story Outline: {story_outline}

CURRENT DRAFT & FEEDBACK:
Previous Draft: {story_draft}
Phonics QA Feedback: {qa_feedback}

CRITICAL RULES:
1. Every page must contain 1 to 3 short sentences.
2. Every word in the story must be decodable according to the child's mastered levels: {phonics_profile}.
3. You may also use the child's sight words.
4. Any word that violates the phonics patterns and is not a sight word must be replaced or rewritten.
5. Pay close attention to the Phonics QA Feedback. If specific words are flagged as violations, you MUST rewrite the pages to remove or replace those words.
6. Target levels and patterns:
   - short_vowels: only basic short vowel sounds in CVC/VC words (e.g., 'cat', 'red', 'pin', 'dog', 'run', 'on', 'at'). No blends or digraphs.
   - digraphs: adds sh, ch, th, wh, ck, ng, ph, qu.
   - blends: adds consonant blends (e.g., 'flat', 'stop', 'hand', 'went').
   - silent_e: adds silent 'e' long vowels (e.g., 'make', 'like', 'home').
   - r_controlled: adds ar, er, ir, or, ur (e.g., 'car', 'her', 'bird').
   - vowel_teams: adds vowel teams (e.g., 'rain', 'see', 'boat').
   Do NOT use any pattern that is NOT in the child's mastered list.

Provide a valid JSON response matching the StoryDraft schema.
"""

writer_agent = Agent(
    name="writer_agent",
    model=gemini_model,
    instruction=writer_instruction,
    output_schema=StoryDraft,
    output_key="story_draft",
    before_agent_callback=init_loop_state
)

# ---------------------------------------------------------------------------
# Agent 4: Phonics QA/Reviser Agent (Loop Guardrail Agent)
# ---------------------------------------------------------------------------
class PhonicsQAAgent(BaseAgent):
    """Custom Agent acting as a Loop Security Guardrail.

    It checks the story draft for phonics decodability violations.
    If the story is decodable, it escalates (exits the loop).
    Otherwise, it records feedback in the state and continues the loop.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Retrieve story draft and phonics profile from session state
        story_draft = ctx.session.state.get("story_draft")
        phonics_profile = ctx.session.state.get("phonics_profile")

        if not story_draft:
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part.from_text(text="No story draft found in state to evaluate.")]),
            )
            return

        if not phonics_profile:
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part.from_text(text="No phonics profile found in state.")]),
            )
            return

        # Pydantic models in state might be dictionary objects or BaseModel instances depending on runner.
        profile_dict = phonics_profile if isinstance(phonics_profile, dict) else phonics_profile.model_dump()

        # Extract text contents
        pages = []
        if isinstance(story_draft, dict):
            pages = story_draft.get("pages", [])
            title = story_draft.get("title", "")
        else:
            pages = story_draft.pages
            title = story_draft.title

        full_story_text = f"{title}\n" + "\n".join(pages)

        # Run decodability checker tool
        check_result = check_decodability(full_story_text, profile_dict)

        # Save QA feedback structure to state so the writer can consume it
        qa_feedback = QAFeedback(
            is_decodable=check_result["is_decodable"],
            violations=check_result["violations"],
            feedback_report=check_result["feedback"]
        )

        if check_result["is_decodable"]:
            # Story is fully decodable! Escalate to exit LoopAgent
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part.from_text(text=f"Phonics Guardrail PASSED: {check_result['feedback']}")]),
                actions=EventActions(
                    escalate=True,
                    state_delta={"qa_feedback": qa_feedback.model_dump()}
                )
            )
        else:
            # Phonics violations found. Do not escalate, loop repeats
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part.from_text(text=f"Phonics Guardrail FAILED: {check_result['feedback']}")]),
                actions=EventActions(
                    state_delta={"qa_feedback": qa_feedback.model_dump()}
                )
            )

qa_agent = PhonicsQAAgent(name="qa_agent")

async def verify_loop_decodability(callback_context: CallbackContext) -> types.Content | None:
    """Verifies that the story is fully decodable after exiting the loop.
    Raises ValueError to abort the pipeline if violations remain.
    """
    qa_feedback = callback_context.state.get("qa_feedback")
    if not qa_feedback or not qa_feedback.get("is_decodable"):
        violations = qa_feedback.get("violations", []) if qa_feedback else []
        raise ValueError(
            f"Phonics Guardrail Validation FAILED after maximum iterations. "
            f"Remaining violations: {violations}"
        )
    return None

# ---------------------------------------------------------------------------
# Loop Agent: Writer + QA Loop
# DEPRECATION WARNING: LoopAgent is deprecated in google-adk 2.x and will be
# removed in a future release. Migrate to the graph-based Workflow API instead.
# ---------------------------------------------------------------------------
writer_qa_loop = LoopAgent(
    name="writer_qa_loop",
    sub_agents=[writer_agent, qa_agent],
    max_iterations=4,
    after_agent_callback=verify_loop_decodability,
)

# ---------------------------------------------------------------------------
# Agent 5: Illustration Prompt Agent
# ---------------------------------------------------------------------------
illustration_instruction = """You are the Phono StoryForge Illustration Prompt Agent.
Your job is to generate a cohesive set of child-friendly illustration prompts for the pages of a personalized storybook.

Phonics Profile: {phonics_profile}
Story Draft: {story_draft}

For each page, generate an `image_prompt` that starts with the base style block, appends the age-band modifier corresponding to the child's age, and then describes the scene.

Base Style Block (start the image prompt with this EXACT text):
"Warm, loose, hand-illustrated style — not stock-perfect, not generic clip art. Flat color fills only, no gradients, 2px stroke weight. Real, expressive faces — not generic smiley faces. Home and everyday settings (kitchen table, living room, backyard) — not classrooms. Consistent character appearance across every page. Restricted to Japonica (#DB7E65), Deep Navy (#192255), Warm Gold (#EBBA7A), Strikemaster (#9C6D8B), Pearl Bush (#ECE5DB), and Tundora (#483E45)."

Age-Band Modifier:
Find the child's age in {phonics_profile} and append the matching modifier exactly:
- If age is between 5 and 7 (inclusive): "Rounder shapes, simpler scenes, larger character proportions, gentle and playful energy."
- If age is between 8 and 10 (inclusive): "Fuller scene detail, age-proportionate characters (not toddler-round), adventure/narrative energy."
- If age is between 11 and 13 (inclusive): "Graphic-novel/editorial illustration energy, more realistic proportions, dynamic compositions. Deliberately avoid anything that reads as an 'early reader' picture-book look."

Scene Description:
After the style block and age-band modifier, append a descriptive description of the specific characters, setting, actions, and objects from the page's text, incorporating the child's interest from {phonics_profile}. Keep the characters, clothing, and environment consistent across all pages.

Output schema must be StoryIllustrations.
"""

illustration_prompt_agent = Agent(
    name="illustration_prompt_agent",
    model=gemini_model,
    instruction=illustration_instruction,
    output_schema=StoryIllustrations,
    output_key="story_illustrations",
    before_agent_callback=rate_limit_delay
)

# ---------------------------------------------------------------------------
# Mock MCP Tools for Testing
# ---------------------------------------------------------------------------
def create_document(title: str) -> dict:
    """Creates a new Google Doc with the specified title.

    Args:
        title: The title of the document.

    Returns:
        A dictionary with documentId and url.
    """
    print(f"\n[Mock MCP Tool] create_document called with title: '{title}'")
    return {
        "documentId": "mock-doc-12345",
        "url": "https://docs.google.com/document/d/mock-doc-12345/edit"
    }

def append_text(document_id: str, text: str) -> dict:
    """Appends text content to a Google Doc.

    Args:
        document_id: The ID of the Google Doc.
        text: The text content to write.

    Returns:
        A dictionary indicating success.
    """
    print(f"\n[Mock MCP Tool] append_text called for doc {document_id} with content: '{text[:60]}...'")
    return {"status": "success"}

def create_file(name: str, mime_type: str, folder_id: str | None = None, content: str | None = None) -> dict:
    """Creates a file in Google Drive.

    Args:
        name: The name of the file.
        mime_type: The mime type of the file.
        folder_id: Optional folder ID where the file should be created.
        content: Optional content of the file.

    Returns:
        A dictionary with fileId and url.
    """
    print(f"\n[Mock MCP Tool] create_file called for '{name}' (mime_type: {mime_type})")
    return {
        "fileId": "mock-file-12345",
        "url": "https://drive.google.com/file/d/mock-file-12345/view"
    }

# Determine tool set to use (real MCP in production/local manual, mock in tests)
if os.environ.get("INTEGRATION_TEST") == "TRUE" or os.environ.get("PYTEST_CURRENT_TEST"):
    print("\n--- [Agent Setup] Using Mock MCP Tools for Google Docs and Google Drive ---")
    export_tools = [
        FunctionTool(create_document),
        FunctionTool(append_text),
        FunctionTool(create_file),
    ]
else:
    print("\n--- [Agent Setup] Instantiating real Stdio Google Workspace MCP Toolset ---")
    gws_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@googleworkspace/cli@0.7.0", "mcp", "-s", "drive,docs,gmail"],
            )
        )
    )
    export_tools = [gws_mcp]

# ---------------------------------------------------------------------------
# Agent 6: Formatter/Export Agent
# ---------------------------------------------------------------------------
formatter_instruction = """You are the Phono StoryForge Formatter/Export Agent.
Your job is to take the finalized `story_draft` (title and pages) and the `story_illustrations` (image prompts) from the session state and export them.

Story Draft: {story_draft}
Story Illustrations: {story_illustrations}

Use the Google Docs tools to create a new Google Doc:
- Set the document title to the storybook title.
- Format the title as a prominent header.
- For each page of the story, write the page's text.
- Underneath each page's text, insert a formatted block (placeholder/description) for the illustration using the corresponding page's image prompt.

Use the Google Drive tools to organize the file in a target folder (or confirm its placement).
Obtain the final Document ID and its shareable link/URL.

CRITICAL REQUIREMENT:
You MUST output your final response containing a markdown JSON block containing the 'doc_id' and 'shareable_url' keys, in this exact format:
```json
{{
  "doc_id": "document-id-here",
  "shareable_url": "shareable-url-here"
}}
```
"""

async def save_export_result(callback_context: CallbackContext) -> types.Content | None:
    """Parses the agent's JSON response and saves it to the export_result state key."""
    # Delay to respect free tier rate limit
    print("\n--- [Rate Limit Guard] Sleeping 5 seconds before processing export... ---")
    await asyncio.sleep(5)

    events = callback_context.session.events
    agent_response = ""
    for event in reversed(events):
        if event.author == "formatter_export_agent" and event.content and event.content.parts:
            agent_response = "".join(part.text for part in event.content.parts if part.text)
            if agent_response:
                break

    doc_id = "unknown"
    shareable_url = "unknown"
    if agent_response:
        try:
            # Extract JSON block
            if "```json" in agent_response:
                json_part = agent_response.split("```json")[1].split("```")[0].strip()
            elif "```" in agent_response:
                json_part = agent_response.split("```")[1].split("```")[0].strip()
            else:
                json_part = agent_response.strip()

            data = json.loads(json_part)
            doc_id = data.get("doc_id", "unknown")
            shareable_url = data.get("shareable_url", "unknown")
        except Exception as e:
            print(f"Error parsing agent output as JSON: {e}. Raw response: {agent_response}")
            # Fallback regex parsing
            import re
            doc_id_match = re.search(r'"doc_id"\s*:\s*"([^"]+)"', agent_response)
            url_match = re.search(r'"shareable_url"\s*:\s*"([^"]+)"', agent_response)
            if doc_id_match:
                doc_id = doc_id_match.group(1)
            if url_match:
                shareable_url = url_match.group(1)

    # Save to session state
    callback_context.state["export_result"] = {
        "doc_id": doc_id,
        "shareable_url": shareable_url
    }
    print(f"\n--- [Export Agent Callback] Saved export_result to state: {callback_context.state['export_result']} ---")
    
    # Export guardrail: Halt the pipeline if the document export failed.
    if doc_id == "unknown" or not doc_id:
        raise ValueError(
            "Google Workspace Document Export FAILED. "
            "Unable to generate or verify document ID for the exported book."
        )
        
    return None

formatter_export_agent = Agent(
    name="formatter_export_agent",
    model=gemini_model,
    instruction=formatter_instruction,
    tools=export_tools,
    output_key="formatter_export_output",
    after_agent_callback=save_export_result,
)

# ---------------------------------------------------------------------------
# Gmail Tools Setup
# ---------------------------------------------------------------------------
def create_draft(to: list[str], subject: str, body: str) -> dict:
    """Creates a new draft email in the user's Gmail account.

    Args:
        to: Required. The primary recipients of the email draft. Each string MUST be a valid plain email address (e.g., "user@example.com").
        subject: Optional. The subject line of the email.
        body: Optional. The main body content of the email draft.

    Returns:
        A dictionary with the draft ID, e.g. {"id": "..."}.
    """
    if os.environ.get("INTEGRATION_TEST") == "TRUE" or os.environ.get("PYTEST_CURRENT_TEST"):
        print(f"\n[Mock MCP Tool] create_draft called: to={to}, subject='{subject}', body='{body[:60]}...'")
        return {"id": "mock-draft-12345"}
    else:
        print(f"\n[Real Gmail Tool] create_draft called via Workspace CLI: to={to}, subject='{subject}'")
        import subprocess
        import json
        import base64
        from email.mime.text import MIMEText

        try:
            mime_message = MIMEText(body)
            mime_message["to"] = ", ".join(to)
            mime_message["subject"] = subject
            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")
            payload = {
                "message": {
                    "raw": raw_message
                }
            }
            cmd = [
                "npx", "-y", "@googleworkspace/cli@0.7.0",
                "gmail", "users", "drafts", "create",
                "--params", '{"userId": "me"}',
                "--json", json.dumps(payload)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                draft_id = data.get("id", "unknown")
                print(f"[Real Gmail Tool] Draft created successfully. ID: {draft_id}")
                return {"id": draft_id}
            else:
                print(f"[Real Gmail Tool] Error creating draft: {result.stderr}")
                return {"id": "unknown", "error": result.stderr}
        except Exception as e:
            print(f"[Real Gmail Tool] Exception during create_draft: {e}")
            return {"id": "unknown", "error": str(e)}

gmail_tools = [FunctionTool(create_draft)]

# ---------------------------------------------------------------------------
# Agent 7: Parent Report Agent
# ---------------------------------------------------------------------------
parent_report_instruction = """You are the Phono StoryForge Parent Report Agent.
Your job is to take the child's `phonics_profile`, the final `story_draft`, and the `export_result` from the session state, and generate a warm, encouraging, and educational parent report.

Phonics Profile: {phonics_profile}
Story Draft: {story_draft}
Export Result: {export_result}

The report must contain:
1. A warm, encouraging, and educational note addressed to the parent.
2. An explanation of which specific phonics patterns/rules the child practiced in the story (e.g. digraphs like 'sh' or blends like 'st').
3. An explanation of how the story was personalized to the child's interest.
4. A list of practice words from the story they can review together.
5. The shareable link/URL to the Google Doc storybook (retrieved from the `export_result` state).

CRITICAL REQUIREMENTS:
1. You MUST call the `create_draft` tool to create a draft email in Gmail containing this report. You should send the email to the parent's email address if it can be found in the profile or user messages, or default to a placeholder like 'parent@example.com'.
2. You MUST output your final response containing a markdown JSON block matching the ParentReport schema with 'parent_letter', 'reinforced_patterns', and 'sight_words_to_practice' keys, in this exact format:
```json
{{
  "parent_letter": "Warm note to the parent explaining progress, personalization, and showing the link: [shareable_url]",
  "reinforced_patterns": [
    "Specific spelling rule/pattern 1",
    "Specific spelling rule/pattern 2"
  ],
  "sight_words_to_practice": [
    "word1",
    "word2"
  ]
}}
```
"""

async def save_parent_report(callback_context: CallbackContext) -> types.Content | None:
    """Parses the agent's JSON response and saves it to the parent_report state key."""
    # Delay to respect free tier rate limit
    print("\n--- [Rate Limit Guard] Sleeping 5 seconds before processing parent report... ---")
    await asyncio.sleep(5)

    events = callback_context.session.events
    agent_response = ""
    for event in reversed(events):
        if event.author == "parent_report_agent" and event.content and event.content.parts:
            agent_response = "".join(part.text for part in event.content.parts if part.text)
            if agent_response:
                break

    parent_letter = "unknown"
    reinforced_patterns = []
    sight_words_to_practice = []

    if agent_response:
        try:
            # Extract JSON block
            if "```json" in agent_response:
                json_part = agent_response.split("```json")[1].split("```")[0].strip()
            elif "```" in agent_response:
                json_part = agent_response.split("```")[1].split("```")[0].strip()
            else:
                json_part = agent_response.strip()

            data = json.loads(json_part)
            parent_letter = data.get("parent_letter", "unknown")
            reinforced_patterns = data.get("reinforced_patterns", [])
            sight_words_to_practice = data.get("sight_words_to_practice", [])
        except Exception as e:
            print(f"Error parsing agent output as JSON: {e}. Raw response: {agent_response}")
            # Fallback regex parsing
            import re
            letter_match = re.search(r'"parent_letter"\s*:\s*"([^"]+)"', agent_response)
            if letter_match:
                parent_letter = letter_match.group(1)

    # Validate and save to session state using ParentReport schema
    try:
        validated_report = ParentReport(
            parent_letter=parent_letter,
            reinforced_patterns=reinforced_patterns,
            sight_words_to_practice=sight_words_to_practice
        )
        callback_context.state["parent_report"] = validated_report.model_dump()
    except Exception as e:
        print(f"Error validating parent report with schema: {e}")
        callback_context.state["parent_report"] = {
            "parent_letter": parent_letter,
            "reinforced_patterns": reinforced_patterns,
            "sight_words_to_practice": sight_words_to_practice
        }

    # Verification guardrail: confirm create_draft call exists and succeeded.
    draft_created = False
    draft_id = None
    has_call = False
    has_failed_response = False

    for event in events:
        for call in event.get_function_calls():
            if call.name == "create_draft":
                has_call = True

        for resp in event.get_function_responses():
            if resp.name == "create_draft":
                resp_data = resp.response
                if isinstance(resp_data, dict):
                    if "error" in resp_data:
                        has_failed_response = True
                        print(f"[Parent Report Guardrail] create_draft returned error: {resp_data['error']}")
                    else:
                        draft_id = resp_data.get("id")
                elif resp_data:
                    draft_id = getattr(resp_data, "id", None)
                    if not draft_id or draft_id == "unknown":
                        has_failed_response = True

                if draft_id and draft_id != "unknown":
                    draft_created = True

    if not has_call:
        raise ValueError(
            "Gmail Draft Creation FAILED. "
            "The create_draft tool call was never invoked by the parent_report_agent."
        )
    if has_failed_response or not draft_created:
        raise ValueError(
            "Gmail Draft Creation FAILED. "
            "The create_draft tool call failed or returned an invalid ID."
        )

    print(f"\n--- [Parent Report Agent Callback] Saved parent_report to state: {callback_context.state['parent_report']} ---")
    return None

parent_report_agent = Agent(
    name="parent_report_agent",
    model=gemini_model,
    instruction=parent_report_instruction,
    tools=gmail_tools,
    output_key="parent_report_output",
    before_agent_callback=rate_limit_delay,
    after_agent_callback=save_parent_report,
)

# ---------------------------------------------------------------------------
# Root Agent: Intake -> Planner -> Writer/QA Loop -> Illustration Prompts -> Exporter -> Parent Report
# ---------------------------------------------------------------------------
root_agent = SequentialAgent(
    name="story_forge_pipeline",
    sub_agents=[
        intake_agent,
        story_planner,
        writer_qa_loop,
        illustration_prompt_agent,
        formatter_export_agent,
        parent_report_agent,
    ],
)

# Initialize application
app = App(
    root_agent=root_agent,
    name="app",
)

