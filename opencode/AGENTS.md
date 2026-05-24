# Global safety rules

## Git and GitHub safety

Never push to any remote repository.

Do not run:

- `git push`
- `git push --force`
- `git push --force-with-lease`
- `git push --tags`
- `git push --mirror`
- `gh repo delete`
- `gh repo edit`
- `gh repo rename`
- `gh pr merge`
- `gh pr close`
- `gh pr ready`
- `gh pr review --approve`
- `gh issue close`
- `gh release delete`
- `gh workflow disable`
- `gh api` for write, delete, patch, or mutation operations

Allowed GitHub CLI usage is read-only by default, such as:

- `gh pr view`
- `gh pr list`
- `gh pr status`
- `gh issue view`
- `gh issue list`
- `gh run list`
- `gh run view`
- `gh repo view`

Creating local commits is allowed only when explicitly requested.

Creating pull requests with `gh pr create` requires explicit user approval in the current conversation.

Before any command that changes remote GitHub state, stop and ask for explicit confirmation.
