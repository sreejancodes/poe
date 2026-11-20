# Glossary

**Analysis**: One unit of data-analysis work in a poe task: a question, the notebook cells run to answer it, the result, its interpretation, and the next analysis chosen. Recorded in one file per analysis.
_Avoid_: analysis step, step, finding

**Results page**: Project-wide page showing every analysis result (poe and untracked) grouped by task and thread, rebuilt from the analysis log and records. Not a chronology and not an agent-activity report.
_Avoid_: dashboard, report, all-analysis page

**Step**: One event in an agent transcript as shown in the report (a message, tool call, or tool result).
_Avoid_: using "step" for a unit of analysis work

**Untracked work**: Analysis done outside poe, by the user or by an agent not using poe. Enters the analysis log as a `manual` entry through a note or the catch-up check.
_Avoid_: hand-written work, manual work
