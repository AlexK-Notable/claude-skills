# Reference: Common Cache Directories

## Cache Table

| Path | Regenerable? | Typical Size | Rebuild Cost |
|------|-------------|-------------|-------------|
| `~/.cache/pip` | Yes (re-download) | 1-5 GB | Low — next pip install |
| `~/.cache/uv` | Yes (re-download) | 1-10 GB | Low — next uv install |
| `~/.cache/paru` | Yes (re-download) | 1-5 GB | Low — next paru install |
| `~/.cache/yay` | Yes (re-download) | 1-5 GB | Low — next yay install |
| `~/.npm/_cacache` | Yes (re-install) | 1-10 GB | Low — next npm install |
| `~/.npm/_npx` | Yes (re-run) | 1-3 GB | Low — next npx execution |
| `~/.cache/huggingface` | Yes (re-download) | 1-50 GB | **High** — large model downloads |
| `~/.cache/go-build` | Yes (re-build) | 0.5-5 GB | Medium — next go build |
| `~/.cache/cargo` | Yes (re-build) | 0.5-5 GB | Medium — next cargo build |
| `~/.cache/puppeteer` | Yes (re-install) | 0.5-2 GB | Medium — browser download |
| `~/.cache/playwright` | Yes but slow | 0.5-2 GB | **High** — multiple browsers |
| `~/.cache/wallust` | Yes but slow | 1-5 GB | Medium — re-process wallpapers |
| `~/.local/share/Trash` | Yes (it's trash) | 0-50 GB | None |
| `~/.cache/thumbnails` | Yes | 0.1-1 GB | Low — regenerated on browse |
| `~/.cache/fontconfig` | Yes | < 10 MB | Low — rebuilt on font access |
| `~/.cache/mesa_shader_cache` | Yes | 0.1-1 GB | Low — rebuilt on GPU use |
| `~/.cache/mozilla` | Yes | 0.5-5 GB | Medium — browser re-caches |
| `node_modules/` (per-project) | Yes | 0.1-2 GB each | Low — `npm install` |
| `target/` (Rust per-project) | Yes | 0.5-10 GB each | Medium — `cargo build` |
| `__pycache__/` | Yes | < 100 MB each | None — auto-created |

## Deletion Priority

When reclaiming space, prioritize by size-to-rebuild-cost ratio:

1. **Trash** (`~/.local/share/Trash`) — zero rebuild cost
2. **Package caches** (pip, uv, npm, paru) — low rebuild cost, often large
3. **Build caches** (go-build, cargo) — medium cost but good space savings
4. **Thumbnails/font caches** — tiny, rarely worth the effort
5. **Playwright/HuggingFace** — large but expensive to rebuild; ask user

## Safe Deletion Commands

```bash
# Clear trash
rm -rf ~/.local/share/Trash/files/* ~/.local/share/Trash/info/*

# Clear package manager caches
rm -rf ~/.cache/pip ~/.cache/uv ~/.npm/_cacache

# Clear build caches
rm -rf ~/.cache/go-build ~/.cache/cargo

# Clear AUR caches (keeps installed package versions)
paru -Sc --noconfirm 2>/dev/null
# Or manual: rm -rf ~/.cache/paru/clone/*

# Clear thumbnails
rm -rf ~/.cache/thumbnails/*
```

## Warning: Don't Delete Entire ~/.cache

Some cache subdirectories contain state that's expensive or impossible to recreate:
- `~/.cache/wallust` — processed wallpaper data
- `~/.cache/playwright` — multiple browser installations
- Application-specific session caches

Always target specific subdirectories, never `rm -rf ~/.cache`.
