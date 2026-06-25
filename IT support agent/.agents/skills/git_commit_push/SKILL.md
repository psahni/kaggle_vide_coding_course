---
name: Git Commit and Push
description: Generates a descriptive commit message based on changes, commits them, and pushes to the main branch.
---
# Git Commit and Push

When the user asks you to commit and push changes, follow these steps:

1. **Check Status**: Run `git status` to see what files have been modified.
2. **Stage Changes**: If there are unstaged changes, stage them using `git add .` (or add specific files if the user requested).
3. **Analyze Changes**: If needed, run `git diff --cached` to understand the scope of the modifications.
4. **Generate Commit Message**: Formulate a concise and descriptive commit message based on the changes. Use the Conventional Commits format if appropriate (e.g., `feat: added agent logic`, `fix: corrected session error`).
5. **Commit**: Run `git commit -m "<your message>"`.
6. **Push**: Run `git push origin main`. (If the default branch is not `main`, determine the correct branch name first using `git branch --show-current`).

Always provide a brief summary to the user of what was committed and pushed.
