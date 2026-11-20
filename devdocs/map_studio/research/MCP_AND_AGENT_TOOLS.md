# Research: MCP and agent tool design (2026-11-12)

Digest of two research passes made while designing the agent interface. Claims are sourced; "unverified" marks what
could not be confirmed. Re-check the MCP parts before implementing: the protocol and the clients move fast.

## MCP protocol state

- Latest specification: **revision 2026-07-28** (https://modelcontextprotocol.io/specification/2026-07-28,
  changelog https://modelcontextprotocol.io/specification/2026-07-28/changelog). It breaks compatibility with
  2025-11-25.
- **Stateless:** no `initialize` handshake, no `Mcp-Session-Id`. Version and client info travel in `_meta` of every
  request; servers implement `server/discover`. State that spans calls is an explicit handle passed as a tool
  argument. `tools/list` must not vary per connection.
- **No server-initiated requests:** elicitation, sampling and roots go through "multi round-trip" results
  (`resultType: "input_required"`, `inputRequests`, `requestState`; the client retries).
- **`subscriptions/listen`** replaces `resources/subscribe`. Removed: `ping`, `logging/setLevel`, SSE resumption.
- **Deprecated** (12-month window): Roots, Sampling, Logging, HTTP+SSE transport, dynamic client registration.
- **Extensions:** Tasks (`io.modelcontextprotocol/tasks`) for long work (`resultType: "task"`, `tasks/get`,
  `tasks/cancel`); MCP Apps (`io.modelcontextprotocol/ui`, `ui://` resources with `text/html;profile=mcp-app`).
- **Caching:** list results carry `ttlMs` and `cacheScope`. Deterministic tool order helps prompt caching.
- **Tools:** `inputSchema`/`outputSchema` (JSON Schema 2020-12), `structuredContent` (also send a text summary),
  content types text, image, audio, `resource_link`, embedded resource; `isError: true` for errors the model should
  correct. Annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
- **Transports:** stdio, and Streamable HTTP (one POST endpoint; headers `MCP-Protocol-Version`, `Mcp-Method`,
  `Mcp-Name`; validate `Origin`; bind 127.0.0.1).
- **SDKs:** tier 1 TypeScript, Python, C#, Go, Rust, Ruby. **No official C++ SDK.** TypeScript SDK 2.x speaks both
  revisions and has the Tasks and Apps extensions. **Checked against npm on 2026-11-12 while building the
  host (S2): the newest `@modelcontextprotocol/sdk` is 1.32.2 and speaks 2025-11-25; no 2.x is published. Treat the
  2026-07-28 claims of this note as unverified until a published SDK implements them.** MCP Inspector: `npx @modelcontextprotocol/inspector` (web, CLI).

## Client support and limits (as documented, Nov 2026)

| | Claude Code | Codex CLI | claude.ai / Desktop | VS Code / Cursor |
|---|---|---|---|---|
| Tasks | yes (2026-07-28 connection, main conversation only, polls every 2 s) | no (use jobs) | yes | no |
| MCP Apps | no | no | yes | yes (VS Code inline) |
| Elicitation | yes, interactive sessions | unverified | unverified | yes |
| Resources | yes (`@` mentions) | unverified | yes, no subscriptions | Cursor yes; VS Code only for Apps |
| Prompts | yes (`/mcp__server__prompt`) | unverified | yes | Cursor yes |
| Timeouts | idle 5 min HTTP / 30 min stdio; calls auto-background after 2 min | **60 s per tool call** by default | **240 s per call** | — |
| Result size | warns at 10k tokens, cap 25k (`MAX_MCP_OUTPUT_TOKENS`); text over 50 000 chars goes to a file | per-tool `output_token_limit` | ~150 000 chars | — |
| Tool loading | deferred behind tool search; `_meta["anthropic/alwaysLoad"]`; descriptions cut at 4 096 / 16 384 chars | first 512 chars of server instructions guaranteed | — | — |

Claude Code `_meta` extras: `anthropic/requiresUserInteraction`, `anthropic/alwaysLoad`,
`anthropic/maxResultSizeChars`. Push into a running Claude Code session only via "channels" (research preview,
legacy handshake only). Sources: https://code.claude.com/docs/en/mcp, https://learn.chatgpt.com/docs/extend/mcp?surface=cli,
https://claude.com/docs/connectors/building, https://modelcontextprotocol.io/extensions/client-matrix.

Images: Claude downsizes to 1 568 px long edge (2 576 on newer models); cost ⌈w/28⌉×⌈h/28⌉ tokens; stricter limits
above 20 images per request (https://platform.claude.com/docs/en/build-with-claude/vision).

## Tool design guidance

- Anthropic, "Writing effective tools for agents" (https://www.anthropic.com/engineering/writing-tools-for-agents):
  few workflow-level tools, not one per endpoint; namespaced names; readable ids instead of UUIDs or indices;
  `response_format` concise/detailed; paging and filters; errors that say how to fix the call; make mistakes hard
  (poka-yoke); evaluate with realistic multi-step tasks and refine descriptions from transcripts.
- Code execution with MCP and programmatic tool calling (https://www.anthropic.com/engineering/code-execution-with-mcp,
  https://www.anthropic.com/engineering/advanced-tool-use): agents writing code against an API save large amounts of
  context for bulk work; tool search and 1–5 usage examples per complex tool improve selection and accuracy (vendor
  figures).
- Cloudflare Code Mode (https://blog.cloudflare.com/code-mode/): MCP schemas as a typed API plus one execute tool.
- OpenAI function-calling guide: fewer than ~20 tools at a time, enums and structure that make invalid states
  impossible; overlap between tools hurts more than count.
- Claude Code best practice (https://code.claude.com/docs/en/best-practices): give the agent a check to run; ask for
  evidence; review with a fresh read-only subagent.

## Lessons from 3D and game-editor MCP servers

- Blender MCP: `execute_blender_code`, `get_scene_info`, multi-view `look`; reported problems: imprecise positions,
  scale errors ("trees as big as mountains"), unrelated settings changed. No undo or transactions.
- Unity (CoplayDev): tools consolidated by `action`, toggleable tool groups, `batch_execute` with `fail_fast`,
  multi-angle screenshots.
- Unreal (Epic, experimental): tool search with four meta-tools, typed tools with read/write/execute access.
- Roblox: run code, scripted play sessions returning logs. Figma: cheap outline first (`get_metadata`), rich detail
  per node.
- Gaps none of them fill: transactional edits with undo, validation after each edit, labelled views.

## Spatial layout research

- Constraints and a solver beat raw coordinates: Holodeck (https://arxiv.org/abs/2312.09067), SceneCraft
  (https://arxiv.org/abs/2403.01248), LayoutVLM (https://arxiv.org/abs/2412.02193), Infinigen Indoors
  (https://arxiv.org/abs/2406.11824).
- Game levels: the model does content, algorithms do space and checks: Word2World (https://arxiv.org/abs/2405.06686),
  database-driven 3D level generation (https://arxiv.org/abs/2508.18533).
- Mission graph separate from layout (Dormans; lock-and-key graph work).
- Set-of-Mark labels on images improve grounding (https://arxiv.org/abs/2310.11441).
- Image judges are viewpoint- and wording-sensitive (SceneCritic, https://arxiv.org/abs/2604.13035); deterministic
  checks first, images second; separate critic and verifier (LL3M, https://arxiv.org/abs/2508.08228).

## What the plan took from this

PLAN.md sections 5–8: command line as source of truth with a thin MCP layer; about fourteen tools, four always loaded;
handles `doc@revision`; transactions with diff and check delta; relations instead of coordinates; graph before
geometry; three check tiers; fixed labelled camera sets; jobs plus MCP Tasks; code mode (`map_exec`); an evaluation
set of real tasks.
