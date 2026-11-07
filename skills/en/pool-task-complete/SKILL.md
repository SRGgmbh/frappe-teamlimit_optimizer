---
name: pool-task-complete
description: Completes a task from the Teamlimit task pool properly – checks the done criteria, makes sure the result is shared and writes the result summary for Frappe. Use when a chat started with "[Teamlimit task …]" or "[Teamlimit-Aufgabe …]" and the user wants to complete the task or says it is done.
---

# Complete a task from the task pool

The chat started with a header line `[Teamlimit task <number>: <title>]` (German interface: `[Teamlimit-Aufgabe …]`) and a link "Task in the pool". The requester is notified in Frappe as soon as the task is marked as done and then reads the summary.

## Steps

1. **Check the done criteria.** Find the section "Done when" (or "Fertig, wenn") in the first prompt. Go through every criterion and say honestly whether it is met. If something is open, ask the user whether they want to finish it or report it as an open point.
2. **Make the result shareable.** The requester cannot see this chat. Agree with the user how the result reaches them:
   - share the chat (share button at the top, copy the link)
   - share the artifact or doc
   - save the file in the agreed folder or project
   Ask the user for the link or the storage location.
3. **Write the summary**, at most 8 lines, without an introduction:
   - What was done (1–3 sentences, with figures where possible)
   - Where the result is
   - Open points or assumptions, if any
   - What the requester should check next
4. **Hand over to the user:**
   - The summary in a code block for copying
   - The result link
   - The link "Task in the pool" from the header line, with the note: click **Done** there and paste the result link and the summary

Do not mark the task as done yourself and do not claim to have done so. The user does that in Frappe.
