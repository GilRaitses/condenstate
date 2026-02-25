# condenstate dev container

When you **build** or **reopen in container** this repo (Cursor or VS Code), the container:

- Gets these env vars from the **host**: `MAGNIPHYQ_IP`, `SSH_KEY_PATH`, `PHY600_ROOT`.
- Mounts the host’s `~/.ssh` into the container at `/home/vscode/.ssh` (read-only), so the key file at `SSH_KEY_PATH` on the host should be under `~/.ssh` (e.g. `~/.ssh/pax-ec2-key.pem`). Inside the container it will be at `/home/vscode/.ssh/pax-ec2-key.pem`; set `SSH_KEY_PATH` to that path if the container expects it.

The host must have the vars set (and the key in `~/.ssh`) before or when the container starts.

## Local (your laptop)

- Copy `.env.example` to `.env` in the repo root and set the vars there.
- If your editor/terminal loads `.env` when opening the project, those values become the “host” env that gets passed into the container.
- If not: in the same terminal where you run “Reopen in Container”, run `set -a && source .env && set +a` (or `export MAGNIPHYQ_IP=...` etc.), then reopen in container.

## Cursor cloud

- In **Cursor** → **Settings** for this project/cloud environment, set **Environment variables**: `MAGNIPHYQ_IP`, `SSH_KEY_PATH`, `PHY600_ROOT` (and ensure the SSH key file exists on the host at `SSH_KEY_PATH`).
- When Cursor builds the dev container in the cloud, it passes those host vars into the container via `containerEnv`.

## After opening in container

In the container terminal, run:

```bash
echo "MAGNIPHYQ_IP=${MAGNIPHYQ_IP:-<unset>}" "SSH_KEY_PATH=${SSH_KEY_PATH:-<unset>}" "PHY600_ROOT=${PHY600_ROOT:-<unset>}"
```

If any show `<unset>`, set them on the host (see above) and reopen the container, or export them in the container for the current session only.
