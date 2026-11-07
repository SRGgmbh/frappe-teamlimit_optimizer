---
name: pool-task-create
description: Works out a task for the Teamlimit task pool together with the user, so that a colleague can run it in Claude without asking back. Use when the user wants to "put a task into the pool", "prepare something for the task pool" or "hand something to someone with budget left".
---

# Create a task for the task pool

The goal is a prompt that a colleague with free Claude budget can start **without any follow-up question**. The colleague knows neither the background nor the files nor the expectations of the requester. Everything they need must be in the prompt.

## Organisation settings

- Frappe address: `https://your-frappe-site.example` (change to your own site before distributing)

## Steps

### 1. Interview

Ask the questions **one at a time**, wait for each answer and ask again while anything is unclear. Skip questions that are already answered. Suggest a sensible answer for each question that the user only has to confirm.

1. **Goal:** What exactly should exist at the end? What is it needed for?
2. **Input material:** Which files, data, links or systems does the task need, and where exactly are they (Claude project, folder, connector)?
3. **Claude project and mode:** In which organisation project should the task run? Is a chat enough, or does it need Cowork (files, folders) or Claude Code (repository)?
4. **Result format:** Which format (doc, table, file, code, text), language, length and tone?
5. **Storage:** Where should the result go so that the requester finds it?
6. **Done when:** How can you tell the task is completely done? Write 2–5 checkable criteria.
7. **Limits:** What must not happen under any circumstances (e.g. change prices, send e-mails, delete data)? What is explicitly not part of the task?
8. **Frame:** Priority, due date, required access, and whether only a specific Claude Team should take the task (e.g. because of confidential data).

At the end estimate the **effort** and justify it in one sentence:
- **S** – up to about a quarter of a 5-hour window (short text, small check)
- **M** – up to about half (several files, medium elaboration)
- **L** – a full window (extensive analysis, a lot of code, many files)

### 2. Write the prompt

Write the prompt to Claude in the second person, not to the colleague. Structure:

```
Context: <2–3 sentences of background, what the result is needed for>

Task: <what exactly has to be done>

Material: <where the inputs are, with exact names>

Result: <format, language, length, tone>

Storage: <where the result is saved or shared>

Done when:
- <criterion 1>
- <criterion 2>

Do not:
- <limit 1>
```

Then check the prompt yourself: are there terms, abbreviations or references ("the file from last week") that an outsider would not understand? Replace them.

### 3. Hand-over

Finally give the user:

1. A **title** (at most 8 words)
2. The **prompt** in a code block
3. **Metadata:** Claude project, project link if known, start in (Chat / Cowork / Claude Code), effort, priority, due date, prerequisites, Claude Team
4. A **link to create** the task in Frappe, with URL-encoded values:

   `<Frappe address>/app/claude-task/new?title=<title>&prompt=<prompt>&priority=<High|Medium|Low>&mode=<Chat|Cowork|Claude Code>&claude_project=<project name>&prerequisites=<prerequisites>`

   `claude_project` must match the name in the project list of the Teamlimit Optimizer exactly. If the link is longer than about 6,000 characters, leave out `prompt` and tell the user to copy the prompt from the code block into the field.

5. Additionally the hand-over block, in case the link does not work. It can be pasted in Frappe with **Import from AI text**:

````
=== TEAMLIMIT-TASK ===
Title: <title>
Priority: <High | Medium | Low>
Effort: <S | M | L>
Due date: <YYYY-MM-DD>
Start in: <Chat | Cowork | Claude Code>
Claude Project: <name>
Project Link: <link or empty>
Prerequisites: <…>
Claude Team: <name or empty>
--- PROMPT ---
<prompt>
=== END ===
````

The user checks the task in Frappe and saves it. Only then is it in the pool.
