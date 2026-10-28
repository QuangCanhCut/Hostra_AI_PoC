
# HOSTRA AI — Coding Agent Instructions

## Project
HOSTRA AI is a Hybrid AI Live Commerce Proof of Concept.

Main goal:
Build a verifiable AI sales assistant integrated
with TTS, video lip-sync and a live compositor.

## Repository Structure
- src/hostra_ai/part1_agent_tts:
  Verified sales agent, RAG, tools, policies and TTS.
- src/hostra_ai/part2_video_lipsync:
  Video processing and lip synchronization.
- src/hostra_ai/part3_demo_compositor:
  Integration and live demonstration.
- web:
  Web interface.
- tests:
  Automated tests.

## Read First
- README.md
- docs/PROJECT_BRIEF.md
- docs/ARCHITECTURE.md
- docs/CURRENT_STATUS.md

## Engineering Rules
1. Inspect relevant code before editing.
2. Do not invent existing APIs or functionality.
3. Explain the implementation plan for complex tasks.
4. Keep changes limited to the requested scope.
5. Preserve public interfaces unless approved.
6. Add or update tests for behavior changes.
7. Run relevant checks and report results.
8. Never expose secrets or read .env unnecessarily.
9. Do not push, deploy, or delete files without approval.
10. Report assumptions and unresolved problems.

## Commerce Safety
- Never fabricate prices, inventory or promotions.
- Prefer verified database/API values.
- Do not make unsupported sales claims.
- Preserve audit evidence and human escalation.
- Use identity assets only with valid permission.

## Completion Report
Provide:
- Summary of changes
- Files modified
- Tests executed and results
- Risks and remaining work
