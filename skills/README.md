# Skills for Claude

Skills that help with the task pool of the Teamlimit Optimizer. Upload the ZIP files from [`dist`](dist) as organisation skills in Claude (owner: organisation settings → skills). Before uploading, change the Frappe address in the create skill to your own site and rebuild the ZIP.

| Purpose | English | German |
| --- | --- | --- |
| Write a task for the pool together with Claude | [`pool-task-create`](en/pool-task-create/SKILL.md) | [`aufgabe-einstellen`](de/aufgabe-einstellen/SKILL.md) |
| Complete a task: check criteria, share result, write summary | [`pool-task-complete`](en/pool-task-complete/SKILL.md) | [`aufgabe-abschliessen`](de/aufgabe-abschliessen/SKILL.md) |
| Instruction for other AI assistants (ChatGPT, Copilot, Gemini …) | [`pool-task-create-other-ai.md`](en/pool-task-create-other-ai.md) | [`aufgabe-einstellen-andere-ki.md`](de/aufgabe-einstellen-andere-ki.md) |

Both languages produce the same hand-over block. The app reads English and German keys and markers, so tasks created with either version can be imported with **Import from AI text**.
