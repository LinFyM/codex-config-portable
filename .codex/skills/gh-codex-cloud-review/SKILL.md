---
name: gh-codex-cloud-review
description: Check Codex "cloud review" signals on a GitHub PR (thumbs-up reactions, comments/reviews, checks) and troubleshoot cases where the review appears to have "no feedback". Use when a PR is expected to be reviewed by Codex but gh/CLI output shows nothing.
---

# GH Codex Cloud Review

## When To Use

- You asked Codex to do a cloud review on a PR (or your org runs it automatically), but you "can't see any feedback".
- You saw a 👍 in the GitHub UI, but `gh pr view` output looks empty.
- You need to confirm whether Codex reviewed, and if the result is "pass" (👍 only) vs "needs changes" (comment/review/check).

## Key Point (Why You Miss The 👍)

- `gh pr view <N>` default output does **not** show reactions.
- In this repo/org, Codex cloud review may signal "no issues" by adding a `+1` reaction from
  `chatgpt-codex-connector[bot]` on the PR (GitHub issue) and **not** posting any comment/review.
- To see it, query `reactionGroups` or the Reactions API via `gh api`.

## Workflow

### 0) Preconditions

```bash
gh auth status -h github.com
```

If unauthenticated: the user must run `gh auth login`.

Get current repo (optional):

```bash
gh repo view --json nameWithOwner
```

### 1) Fast Check: PR Has 👍 Reaction?

This shows counts (not who reacted):

```bash
gh pr view <PR_NUMBER> --json reactionGroups
```

If you see `THUMBS_UP` totalCount > 0, it's likely the "pass" signal.

### 2) Authoritative Check: Was The 👍 From Codex Bot?

List reactions and confirm the actor:

```bash
# Replace owner/repo if not in current repo.
gh api -H "Accept: application/vnd.github+json" \
  repos/<OWNER>/<REPO>/issues/<PR_NUMBER>/reactions
```

Look for:
- `user.login == "chatgpt-codex-connector[bot]"`
- `content == "+1"` (thumbs up)

Example (this repo):

```bash
gh api -H "Accept: application/vnd.github+json" \
  repos/LinFyM/Episodic-Memory-Chatbot/issues/18/reactions
```

### 3) If There Are Findings: Check Comments / Reviews

Codex may post a comment/review instead of (or in addition to) reactions.

```bash
gh pr view <PR_NUMBER> --json comments,reviews
```

If needed, query the full timeline (heavier):

```bash
gh api -H "Accept: application/vnd.github+json" \
  repos/<OWNER>/<REPO>/issues/<PR_NUMBER>/comments
```

### 4) Don’t Confuse With CI Checks

Some repos have no GitHub Actions checks configured. In that case:

```bash
gh pr checks <PR_NUMBER>
```

may show nothing, and that is OK. The Codex signal can still be a 👍 reaction.

### 5) Troubleshooting: Truly No Feedback

If there is no bot reaction and no bot comments/reviews after ~10-15 minutes:

1. Confirm the PR is in the repo/org where the Codex GitHub connector is installed (permissions matter).
2. Confirm you are looking at the correct PR number and repository.
3. Re-trigger (only if your org uses a mention-trigger flow):

```bash
gh pr comment <PR_NUMBER> -b \"@chatgpt-codex-connector please review\"
```

4. If still nothing: treat it as an infra/integration issue (not code) and escalate with:
   - PR URL
   - `gh auth status -h github.com`
   - outputs of steps 1-3 above
