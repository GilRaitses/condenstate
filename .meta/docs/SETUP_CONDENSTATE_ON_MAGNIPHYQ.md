# Clone condenstate on magniphyq

When the local full check reports `condenstate_on_magniphyq: no`, clone the repo on magniphyq so cloud agents can use it.

## From your laptop (one-time)

Resolve magniphyq IP (from `.env` as `MAGNIPHYQ_IP` or via AWS CLI). Then:

```bash
# SSH to magniphyq and clone condenstate into ~/condenstate
ssh -i "${SSH_KEY_PATH:-$HOME/.ssh/pax-ec2-key.pem}" ubuntu@$MAGNIPHYQ_IP "git clone https://github.com/GilRaitses/condenstate.git ~/condenstate"
```

If the repo is **private**, magniphyq needs access. Options:

- **HTTPS with token:** On magniphyq, clone with a URL that includes a token, or run `git config credential.helper` and provide credentials once.
- **SSH deploy key:** Add a deploy key to the GitHub repo, put the private key on magniphyq (e.g. `~/.ssh/condenstate_deploy`), then clone with `git clone git@github.com:GilRaitses/condenstate.git ~/condenstate`.

## Verify

```bash
ssh -i "${SSH_KEY_PATH:-$HOME/.ssh/pax-ec2-key.pem}" ubuntu@$MAGNIPHYQ_IP "test -d ~/condenstate/.sst && test -d ~/condenstate/.ddb && echo ok"
```

Should print `ok`. Then re-run the local full check directive; you should get `condenstate_on_magniphyq: yes` and `ready: yes` (assuming no other gaps).

## Optional: keep magniphyq clone updated

From magniphyq (or via SSH):

```bash
ssh ubuntu@$MAGNIPHYQ_IP "cd ~/condenstate && git fetch origin && git checkout main && git pull origin main"
```

Run after you push changes to condenstate that you want cloud agents to see.
