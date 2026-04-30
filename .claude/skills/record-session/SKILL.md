---
name: record-session
description: >
  Begins or manages detailed session recording to a Markdown file. Captures every
  Q&A exchange, analysis process, errors encountered, fixes applied, and key
  decisions with full technical context. Use when the user asks to "record the
  session", "log our conversation", "start recording", "take notes", "keep a
  detailed log", "document everything", "save this session", "/record", or similar
  recording/journaling requests.
argument-hint: "[start|stop|status|markdown-file-path]"
allowed-tools: [Read, Write, Edit, Bash(git *)]
---

# Session Recording

You are now in **recording mode**. Maintain a detailed, structured log of this
conversation in the specified Markdown file. If no file is given, default to
`claude-record.md` in the current working directory.

## File path

Use `$ARGUMENTS` as the target file path. If `$ARGUMENTS` is empty, `start`,
`stop`, `status`, or not a file path, default to `claude-record.md`.

Commands (these are not file paths):
- `stop` — finish recording, write a closing entry, and stop
- `status` — report the current recording file, entry count, and file size

## Recording format

Write each exchange as a top-level section. Include for EVERY user question or
task:

### Required fields per entry

1. **User instruction** — the user's exact question or request (verbatim when
   possible, paraphrased only if the original is extremely long)
2. **Analysis process** — step-by-step reasoning before any action:
   - What was investigated and why
   - Files read, commands run, and what each revealed
   - Dead ends explored and why they were abandoned
   - How the root cause was narrowed down
3. **Actions taken** — what was actually done:
   - Files created, modified, or deleted (with line numbers)
   - Commands executed and their key output
   - Decisions made and their rationale
4. **Results** — outcome of the actions:
   - Whether the fix worked
   - New issues discovered
   - Verification steps and their results
5. **Technical context** — environment details that matter:
   - Git branch and last commit
   - Relevant tool versions
   - File paths referenced

### Formatting rules

- Use Markdown headings: `##` for each Q&A exchange, `###` for sub-sections
- Use fenced code blocks with language tags for all code
- Show **before/after** code for all fixes with line number ranges
- Wrap error messages in blockquotes (`>`)
- Use tables for summarizing multiple related changes
- Link to specific lines using `file:line` syntax

### Level of detail

- **Errors**: Always include the full error message, the root cause
  explanation (WHY it happens, not just WHAT), and why the fix works
- **Code changes**: Show the diff-level change with surrounding context
- **Commands**: Include the exact command and its exit status; excerpt
  long output to the relevant parts
- **Decisions**: Always explain the trade-offs considered

## When to write

- After each completed Q&A exchange, append the entry to the file
- At session start, write a header with date, working directory, and git status
- On `stop`, write a closing timestamp

## Anti-patterns

- Do NOT write in-progress half-entries (wait until the exchange is complete)
- Do NOT copy entire compiler logs verbatim — excerpt only the relevant parts
- Do NOT skip recording minor exchanges (even small fixes are worth a short entry)
