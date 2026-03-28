# Commit Message Convention

This file defines the convention the agent must follow when suggesting commit messages.

## Goal
- Keep commit messages clear, consistent, and easy to scan in history.
- Produce commit suggestions in English only.

## Required format
`<type>(<scope>): <subject>`

Rules:
1. `type` is mandatory and lowercase.
2. `scope` is optional, lowercase, and should match the impacted area (for example: `frontend`, `backend`, `device`, `docs`, `api`, `legacy`, `build`).
3. `subject` is mandatory, in imperative mood, and starts with a verb (`add`, `fix`, `update`, `refactor`, etc.).
4. No trailing period in the subject.
5. Keep subject length <= 72 characters.

## Allowed types
- `feat`: new user-facing behavior or capability
- `fix`: bug fix or regression fix
- `refactor`: internal code change without behavior change
- `docs`: documentation only
- `test`: test additions or updates
- `chore`: maintenance, tooling, or non-functional updates
- `build`: build/dependency/release pipeline changes
- `ci`: CI workflow changes
- `perf`: performance improvement
- `revert`: rollback of a previous change

## Selection rules
1. Pick the most specific `type` that matches the main change.
2. Use a `scope` whenever the touched area is clear.
3. If multiple unrelated changes exist, suggest splitting commits instead of using a vague message.
4. Prefer precision over generic wording (avoid subjects like `update files`).

## Subject writing rules
1. Use imperative form: `add`, `fix`, `remove`, `rename`, `improve`, `align`.
2. Mention what changed, not why in detail.
3. Keep acronyms and product names as-is (`API`, `ESP32`, `Grafana`).
4. Avoid filler words (`some`, `various`, `minor`).

## Examples
- `feat(frontend): add sidebar link for legacy diagnostics`
- `fix(api): handle null device status in metrics endpoint`
- `docs(readme): document local simulator startup steps`
- `refactor(device): simplify web ui route registration`
- `chore(build): pin vite version for reproducible installs`

## Output requirement for the agent
When providing a commit suggestion, always output exactly one line:
`Suggested commit message: <message>`
