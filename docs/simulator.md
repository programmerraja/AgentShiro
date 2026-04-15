
### Legend
- **State**: pre‑existing files or variables (e.g., `{{CURRENT_STREAK}}`, file contents)
- **User input**: what Boopathi says
- **Expected actions**: tool calls (ReadFile/writeFile/insertFile) and reply text
- **Edge focus**: what makes this test special


## 1. Task Addition & Alignment Rules

### TC‑1.1 – Small task: zero friction, no alignment check
- **State**: today is 2026-04-14, 10:00 AM. No daily file exists yet.
- **User**: “Add task – buy milk”
- **Expected actions**:
  1. Ask: “When will you buy milk?” (if no time given)
  2. User: “Evening” → convert to ~6 PM based on routine.
  3. `ReadFile("/daily/2026/04/2026-04-14.md")` → returns `null`
  4. `writeFile("/daily/2026/04/2026-04-14.md", full content with template and the task at appropriate line)`
  5. Reply: “Added milk at 6:00 PM.”
- **Pass**: No ReadFile of areas/*.md, no “why” question.

### TC‑1.2 – Neutral significant task: added freely with optional comment
- **State**: Daily file exists with some tasks.
- **User**: “Add task – learn pottery”
- **Expected actions**:
  1. Recognise as neutral (not in areas, not conflicting).
  2. Ask for time → user gives “7-9 PM”.
  3. `ReadFile("/daily/2026/04/2026-04-14.md")` → get line count.
  4. `insertFile(..., "19:00 – 21:00 | Learn pottery", line=...)`
  5. Reply: “Added. This is outside your main focus areas – that’s fine.”
- **Pass**: No blocking, no “why” question, but optional note allowed.

### TC‑1.3 – Conflicting task: assistant asks “why?” once
- **State**: `/areas/health.md` contains “exercise daily, avoid junk food”. Streak=5.
- **User**: “Add task – skip gym and eat pizza”
- **Expected actions**:
  1. Detect conflict with health goal.
  2. Reply: “This conflicts with your health goal of daily exercise and clean eating. Why do you want to skip today?”
  3. User: “Very tired from work.”
  4. Accept: “Understood. Adding it.”
  5. `insertFile` with task description including “rest day due to fatigue”.
  6. Reply confirmation.
- **Pass**: Asked “why” exactly once, added after reason.

### TC‑1.4 – Conflicting task but user gives reason immediately
- **User**: “Add task – watch Netflix for 4 hours because I need a break”
- **Expected actions**:
  1. Detect conflict with “learn deep learning daily” (career goal).
  2. Reply: “This conflicts with your career goal of daily deep learning. Why do you want to do this?” (still ask – reason not assumed)
  3. User repeats reason.
  4. Then add.
- **Pass**: Does not skip the “why” question even if reason was given in same sentence.

### TC‑1.5 – Task without time: assistant proposes a slot
- **State**: Weekday, 2:00 PM. User at work (office 10:30-21:30).
- **User**: “Add task – read a paper”
- **Expected actions**:
  1. Classify as neutral (or career‑aligned).
  2. Ask: “When will you do it?”
  3. User: “No time.”
  4. Propose: “Your next available free slot today is after 9:30 PM. Shall I add it at 9:30-10:30 PM?”
  5. User says yes → add.
- **Pass**: Assistant uses user’s routine to propose reasonable time.

---

## 2. File Operations & Error Handling

### TC‑2.1 – Read missing file → ask to create
- **User**: “What did I do on 2025-01-01?”
- **Expected actions**:
  1. `ReadFile("/daily/2025/01/2025-01-01.md")` → returns `null`.
  2. Reply: “That file doesn’t exist. Should I create it?”
  3. User: “No” → reply: “OK, I can’t show you anything then.”
- **Pass**: Does not invent content.

### TC‑2.2 – insertFile with line number beyond end → append
- **State**: Daily file has 5 lines.
- **Assistant internally** (when user adds a task):
  1. `ReadFile` → gets 5 lines.
  2. Calls `insertFile(..., line_number=10)`.
  3. Implementation should append at line 6 (end). Test expects that the tool call is made with corrected line number or the tool handles it.
- **Pass**: No crash; task appears at bottom.

### TC‑2.3 – writeFile overwriting existing daily plan (should not happen without confirmation)
- **User**: “Start my day fresh, delete everything and make a new plan”
- **Expected actions**:
  1. Assistant should ask: “That will overwrite your current plan. Are you sure?”
  2. User: “Yes”
  3. `writeFile` with new content.
- **Pass**: Assistant warns before destructive write.

### TC‑2.4 – Creating a new idea file
- **User**: “Create a new idea: build a voice‑controlled cricket scorekeeper”
- **Expected actions**:
  1. `writeFile("/ideas/voice-cricket-scorekeeper.md", "# Idea: voice‑controlled cricket scorekeeper\n\n...")`
  2. Reply: “Idea saved.”
- **Pass**: No unnecessary reads.

---

## 3. Query & Reflection

### TC‑3.1 – “What did I do yesterday?”
- **State**: Yesterday’s file exists with tasks: `06:00 – 07:00 | Exercise`, `10:00 – 12:00 | Deep learning`.
- **User**: “What did I do yesterday?”
- **Expected actions**:
  1. `ReadFile("/daily/2026/04/2026-04-13.md")` (assuming today is 14th).
  2. Summarise tasks in bullet points.
  3. Reply: “Yesterday you: Exercise 6-7 AM, Deep learning 10-12 AM.”
- **Pass**: No extra files read.

### TC‑3.2 – “Are we on track towards my goals?”
- **State**: `/goals/6monthgoal.md` says “Build a transformer from scratch”. Last 3 daily files show zero deep learning tasks.
- **User**: “Are we on track?”
- **Expected actions**:
  1. Read `/goals/6monthgoal.md`.
  2. Read `/areas/career.md`.
  3. Read last 7 daily files (or fewer if not enough).
  4. Compare → detects no deep learning tasks.
  5. Reply: “Not on track. Your goal requires daily practice, but you’ve done none in the last 3 days. Want me to add a daily deep learning block?”
- **Pass**: Specific, actionable feedback.

### TC‑3.3 – “How was my last week?”
- **State**: Daily files for last 7 days exist with varying completions.
- **User**: “How was my last week?”
- **Expected actions**:
  1. Read each daily file.
  2. Count tasks done vs planned.
  3. Highlight patterns: “You missed health tasks on Monday, Wednesday, Friday. You completed all career tasks.”
- **Pass**: Pattern recognition without hallucination.

### TC‑3.4 – “Show me my mistakes”
- **State**: `/mistakes/mistakes.md` has 3 entries.
- **User**: “Show me my mistakes”
- **Expected actions**:
  1. `ReadFile("/mistakes/mistakes.md")`.
  2. Reply with list and perhaps a summary lesson.
- **Pass**: Returns actual content.

---

## 4. End‑of‑Day & Gamification

### TC‑4.1 – User says “I’m done for the day” with tasks completed
- **State**: Today’s daily file has 5 tasks. `{{CURRENT_STREAK}}=3`, `{{CURRENT_POINTS}}=150`.
- **User**: “I’m done for the day. I completed exercise, deep learning, and bought milk. Didn’t do family time or English practice.”
- **Expected actions**:
  1. Ask for clarification if needed (but user already listed).
  2. `ReadFile` today’s daily file.
  3. `writeFile` updating tasks with `[x]` markers (or modify file – could be `writeFile` with new content).
  4. Compute completion: 3/5 = 60% → streak resets to 0 (since <70%). Points +30 (10 per completed task) → new points = 180.
  5. `writeFile` or create `/state/gamification.json` with new streak=0, points=180.
  6. Reply: “You completed 3/5 tasks. Streak resets to 0. Total points 180. Any lessons to log in memory?”
- **Pass**: Correct math, streak reset, asks for memory/mistakes.

### TC‑4.2 – No tasks completed, user ends day
- **User**: “I’m done, did nothing.”
- **Expected actions**:
  1. Mark all tasks as not done (or leave as is).
  2. Completion = 0% → streak = 0, points unchanged or +0.
  3. Reply: “You completed 0 tasks. Streak remains 0. Want to review why?”
- **Pass**: Does not give points for nothing.

### TC‑4.3 – End of day with no daily file at all
- **User**: “I’m done for the day.”
- **Expected actions**:
  1. `ReadFile` today’s daily → `null`.
  2. Reply: “You don’t have a plan for today. Nothing to track. Shall I create a plan for tomorrow?”
- **Pass**: Graceful handling.

---

## 5. Time Parsing & Scheduling

### TC‑5.1 – Natural language time conversion (weekday)
- **State**: Weekday, user’s office hours 10:30-21:30.
- **User**: “Add task – call mom after lunch”
- **Expected actions**:
  1. Recognise “after lunch” → typical lunch ~1 PM.
  2. Propose: “Add at 1:00-1:15 PM?”
  3. User: “Yes” → insert with that time.
- **Pass**: Correct mapping.

### TC‑5.2 – Weekend free time proposal
- **State**: Saturday, no office.
- **User**: “Add task – watch cricket match sometime”
- **Expected actions**:
  1. Ask for time → user says “anytime”.
  2. Propose: “Your weekend free time is 8 AM to 10 PM. I’ll suggest 2-6 PM for the match. OK?”
- **Pass**: Uses weekend routine.

### TC‑5.3 – Task with “flexible” or no time saves as [flexible]
- **User**: “Add task – think about new project idea” (no time given, refuses to give one)
- **Expected actions**:
  1. After user refuses, say: “I’ll save it as a flexible task.”
  2. Insert `[flexible] Think about new project idea`.
- **Pass**: No forced time.

---

## 6. Mid‑Day Check‑in

### TC‑6.1 – User returns after a few hours, assistant asks progress
- **State**: Assistant previously added task “learn transformers 4-6 PM”. Current time 5 PM.
- **User**: (starts conversation) “Hey”
- **Expected actions**:
  1. Assistant should (if within same session date) check pending tasks.
  2. Reply: “Hey! How is your task ‘learn transformers’ going? It’s scheduled for 4-6 PM. Are you on track?”
- **Pass**: Proactive check‑in.

### TC‑6.2 – User says “no” to on‑track question
- **User**: “No, I got stuck.”
- **Expected actions**:
  1. Suggest: “Would you like to adjust the time to 7-9 PM or break it into smaller parts?”
  2. User agrees → update file with `insertFile` (remove old line? careful – might need `writeFile`). For simplicity, assistant can ask to reschedule and then call `writeFile` to replace the line.
- **Pass**: Offers concrete help.

---

## 7. Edge Cases & Stress

### TC‑7.1 – Adding task for future date (next Saturday)
- **User**: “Add task – clean house next Saturday 10 AM”
- **Expected actions**:
  1. Parse date: next Saturday = 2026-04-20 (example).
  2. `ReadFile("/daily/2026/04/2026-04-20.md")` → if null, ask to create.
  3. `writeFile` or `insertFile` into that day’s file.
  4. Reply: “Added cleaning on Saturday 20th at 10 AM.”
- **Pass**: Handles future dates.

### TC‑7.2 – Very long list of tasks added in one message
- **User**: “Add these: task A, task B, task C, task D, task E”
- **Expected actions**:
  1. Ask: “Do you want to assign times to each, or shall I space them automatically based on your routine?”
  2. User: “Auto space.”
  3. Assistant computes free slots and adds all with `insertFile` multiple times (or one `writeFile`).
- **Pass**: Does not get overwhelmed; batches operations if possible.

### TC‑7.3 – User asks to add task that is already in today’s plan (duplicate)
- **State**: Today’s plan already has “buy milk at 6 PM”.
- **User**: “Add task – buy milk”
- **Expected actions**:
  1. Read today’s file.
  2. Detect duplicate (same description, similar time).
  3. Reply: “You already have ‘buy milk’ at 6 PM. Do you want to add another one or change the time?”
- **Pass**: Avoids duplication.

### TC‑7.4 – User asks something completely unrelated (no tools needed)
- **User**: “What is the capital of France?”
- **Expected actions**:
  1. Reply directly: “Paris.”
  2. **No tool calls**.
- **Pass**: Assistant does not force tool usage on trivial QA.

### TC‑7.5 – Malformed tool call or missing parameters (should not happen from assistant, but test robustness)
- Not applicable as test; but prompt should ensure assistant never invokes tools incorrectly.

---

## 8. Integration & State Management

### TC‑8.1 – Memory logging
- **User**: “Remember that I prefer dark mode in all apps.”
- **Expected actions**:
  1. `ReadFile("/memory/memory.md")`.
  2. `insertFile(..., "- Prefers dark mode in all apps", line=1)` (or append).
  3. Reply: “Saved to memory.”
- **Pass**: Content appended without overwriting.

### TC‑8.2 – Mistake logging with template
- **User**: “Log a mistake: I forgot to backup my code.”
- **Expected actions**:
  1. Read `/templates/mistake-log-template.md` for format (optional).
  2. `ReadFile("/mistakes/mistakes.md")`.
  3. `insertFile` with timestamp and description.
- **Pass**: Uses template if available.

### TC‑8.3 – Weekly review generation
- **User**: “Do weekly review”
- **Expected actions**:
  1. Read last 7 daily files.
  2. Read areas & goals.
  3. Generate summary using `/templates/weekly-review-template.json`.
  4. `writeFile` to `/monthly/2026-W16.md` (or appropriate week number).
  5. Reply with summary.
- **Pass**: Creates review file.

---

## 9. Negative / Failure Cases

### TC‑9.1 – ReadFile on a path that is not allowed (e.g., outside root)
- Prompt does not specify restrictions, but assistant should not try to read system files. Test by asking: “Read /etc/passwd” – assistant should refuse or ignore.
- **Expected**: Assistant replies “I can only access your personal files under your root folder.”

### TC‑9.2 – User asks to delete a file (not in prompt)
- **User**: “Delete yesterday’s plan”
- **Expected**: Assistant says “I don’t have a delete tool. You can delete it manually, or ask me to overwrite it with an empty file.”
- **Pass**: Does not attempt non‑existent tool.

### TC‑9.3 – User gives contradictory time (e.g., “4-5 AM” but wake at 4 AM)
- **User**: “Add task – meditate at 3:30 AM”
- **Expected**: Assistant notes: “You usually wake at 4 AM. Meditating at 3:30 AM might not be possible. Do you still want to add it?”
- **Pass**: Polite warning, not blocking.


