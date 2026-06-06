# Publishing the public version

`claude-skills-public.bundle` is a **self-contained git repo with zero history** — a
single "Initial public release" commit containing the sanitized tree. Publish it like this:

```bash
# 1. Clone the bundle into a fresh working copy
git clone claude-skills-public.bundle claude-skills-public
cd claude-skills-public

# 2. (Optional) re-author the single commit under your own identity
git config user.name  "Your Name"
git config user.email "you@example.com"
git commit --amend --reset-author --no-edit

# 3. Create a NEW empty public repo on GitHub first (e.g. your-username/claude-skills),
#    then point origin at it (the clone's origin currently points at the bundle file):
git remote set-url origin git@github.com:your-username/claude-skills.git

# 4. (Optional) use 'main' instead of 'master', then push
git branch -M main
git push -u origin main
```

That's it — the published repo carries **no commit history** from your private repo, only
the one clean release commit.

## Before you push, optionally personalize the placeholders

The tree ships with neutral placeholders and example data. Search-and-replace as desired:

- `your-username` → your real (or intended public) GitHub handle, in `README.md`,
  `CLAUDE.md`, every `plugins/*/.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`.
- `Your Name` / `you@example.com` → whatever you want as the public author identity.
- `home-network` / `home-assistant` example device tables → leave as illustrative template,
  or fill with your own (consider keeping real data only in a git-ignored `*.local.md`).
- Bitwarden `<your-project-id>` / `<your-secret-id>` → leave as placeholders for readers.

See `../SANITIZATION-REPORT.md` for the full list of what was changed and a few
"how generic do you want it" judgment calls to confirm.
