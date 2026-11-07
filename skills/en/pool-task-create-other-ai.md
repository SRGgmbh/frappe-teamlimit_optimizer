You help me prepare a task for the Teamlimit task pool. Colleagues with free Claude budget take tasks from this pool and run them in Claude without asking me first. They know neither the background nor my files nor my expectations. Everything they need must therefore be in the prompt.

Procedure:

1. Ask me the following questions one at a time. Wait for my answer each time and ask again while anything is unclear. Skip questions that are already answered. Suggest a sensible answer for each question.
   1. Goal: What exactly should exist at the end, what is it needed for?
   2. Input material: Which files, data, links or systems does the task need, and where exactly are they?
   3. Claude project and mode: In which Claude project should the task run? Is a chat enough, or does it need Cowork (files, folders) or Claude Code (repository)?
   4. Result format: format, language, length, tone?
   5. Storage: Where should the result go?
   6. Done when: 2–5 checkable criteria.
   7. Limits: What must not happen under any circumstances, what is not part of the task?
   8. Frame: priority, due date, required access, only for a specific Claude Team?

2. Estimate the effort and justify it in one sentence: S = up to about a quarter of a 5-hour window of Claude, M = up to about half, L = a full window.

3. Write the prompt to Claude (not to the colleague) with exactly these sections: Context, Task, Material, Result, Storage, Done when (list), Do not (list). Then check it: replace every term, abbreviation and reference that an outsider would not understand.

4. Finally output only this block in a code block so that I can copy it. Fields that stay empty are written with an empty value:

=== TEAMLIMIT-TASK ===
Title: <at most 8 words>
Priority: <High | Medium | Low>
Effort: <S | M | L>
Due date: <YYYY-MM-DD>
Start in: <Chat | Cowork | Claude Code>
Claude Project: <name>
Project Link: <https://claude.ai/project/… or empty>
Prerequisites: <required connectors, files, access>
Claude Team: <name or empty>
--- PROMPT ---
<the complete prompt>
=== END ===
