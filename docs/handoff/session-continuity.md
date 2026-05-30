# Session Continuity

## Opening the Folder

Use one of these methods:

### VS Code UI
1. Open VS Code.
2. Select `File`.
3. Select `Open Folder...`.
4. Choose `F:\Projects\Hackathons\YardMind`.

### Command Line

```powershell
code F:\Projects\Hackathons\YardMind
```

## Important Limitation

Chat sessions do not persist as live memory across a brand-new session unless the information has been written into the repository or workspace memory. The safest way to continue work is:

1. Open the same project folder.
2. Start a new chat from that folder.
3. Paste the next-session prompt from `docs/handoff/next-session-prompt.md`.
4. Ask the new session to read the handoff docs before editing.

## What Carries Forward Reliably

- all files in this repository
- all documentation added under `docs/`
- all code, tests, and examples in the project folder

## What Does Not Reliably Carry Forward

- the live conversational context of this exact chat
- unwritten assumptions that were never saved into the repo
- temporary terminal context if you start from a fresh window