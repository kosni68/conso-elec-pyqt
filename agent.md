# Agent Instructions

## Commit suggestion

At the end of every response, suggest a commit message in English.

Apply `COMMIT_MESSAGE_CONVENTION.md` strictly.

The commit suggestion must:
- follow `<type>(<scope>): <subject>` when a scope is relevant
- keep `type` lowercase
- use an imperative English subject
- have no trailing period
- keep the subject at 72 characters or fewer

Output exactly one final line in this form:

`Suggested commit message: <message>`

Do not add any text after that line.
