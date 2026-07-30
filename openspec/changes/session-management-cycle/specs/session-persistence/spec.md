# Spec: session-persistence

**Change**: `session-management-cycle` | **Status**: Draft

## 1. Schema

```
session_id: "ses_{ISO8601-no-punct}_{4-hex}"  # generated on_mount
messages: [{"role": "user"|"agent"|"system", "content": str, "timestamp": str}]
started_at, ended_at: ISO 8601
theme, provider, model: str
total_tokens: int, total_cost_usd: float  (0 if unavailable)
```

## 2. Persistence

### 2.1 Capture Boundaries
Messages MUST be captured at two points:
1. **User submit** (`_handle_input_submit`): append `{"role": "user", "content": text}` after `chat.add_message("user", text)`.
2. **Agent response complete** (end `_stream_agent_response`): append `{"role": "agent", "content": full_response}`.
System messages, warnings, thinking widgets MUST NOT be persisted.

### 2.2 Files
- Save: `~/.ohm/sessions/{session_id}.json` (full data) + update `~/.ohm/sessions/last_session.json` pointer: `{"last_session_id": "ses_..."}`.
- Load: read pointer → resolve `{session_id}.json` → return data. Missing/corrupt → `{}`.
- Clear: remove pointer only. Historical session files MUST NOT be deleted.
- Multiple session files coexist — never overwrite a non-matching ID.

### 2.3 Rich Content
All content MUST be plain text in JSON. On save, strip Rich objects. On load, content is re-rendered as new messages (Markdown for agent, plain for user). Rationale: Rich objects do not survive `json.dumps`.

## 3. Scenarios

**GIVEN** active chat with user + agent messages  
**WHEN** user quits via ctrl+q → confirm  
**THEN** `{session_id}.json` contains both messages AND `last_session.json` points to it  

**GIVEN** agent response with Markdown  
**WHEN** serialized  
**THEN** file has plain text only (no Rich objects)  

**GIVEN** sessions A and B  
**WHEN** both saved  
**THEN** both files exist AND last_session.json points to B
