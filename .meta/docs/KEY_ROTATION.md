# Rotate the EC2 SSH key (magniphyq / condenstate)

**When to do this:** The key was pasted in chat, committed, or otherwise exposed. Treat it as compromised and rotate.

**Important:** Do **not** paste the new private key in chat or in the repo. Use file copy (e.g. `scp`) or Cursor’s secret-file attachment so the key never appears in logs or history.

---

## 1. Generate a new key on your Mac

```bash
ssh-keygen -t ed25519 -f ~/.ssh/pax-ec2-key-new.pem -N "" -C "magniphyq-rotated"
```

Keep the **old** key (`~/.ssh/pax-ec2-key.pem`) for one more step so you can still SSH to magniphyq to add the new key.

---

## 2. Add the new public key to magniphyq (using the old key)

From your Mac:

```bash
MAGNIPHYQ_IP=3.81.174.42   # or get via: aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Name,Values=magniphyq" --query 'Reservations[*].Instances[*].PublicIpAddress' --output text
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@$MAGNIPHYQ_IP "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@$MAGNIPHYQ_IP "cat >> ~/.ssh/authorized_keys" < ~/.ssh/pax-ec2-key-new.pem.pub
```

(If your new key has a different name, use that `.pub` file.)

---

## 3. Test SSH with the new key

```bash
ssh -i ~/.ssh/pax-ec2-key-new.pem ubuntu@$MAGNIPHYQ_IP "echo ok"
```

You should see `ok`. If not, fix before removing the old key.

---

## 4. Remove the old public key from magniphyq

SSH with the **new** key and edit `authorized_keys`:

```bash
ssh -i ~/.ssh/pax-ec2-key-new.pem ubuntu@$MAGNIPHYQ_IP "cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak && nano ~/.ssh/authorized_keys"
```

Delete the line that corresponds to the **old** key (the one that was exposed). Save and exit. Alternatively, from your Mac you can pipe a filtered list:

```bash
ssh -i ~/.ssh/pax-ec2-key-new.pem ubuntu@$MAGNIPHYQ_IP "grep -v 'OLD_KEY_FINGERPRINT_OR_LINE' ~/.ssh/authorized_keys > ~/.ssh/authorized_keys.new && mv ~/.ssh/authorized_keys.new ~/.ssh/authorized_keys"
```

(Replace with the actual old public-key line or a unique part of it.)

---

## 5. Switch your Mac to the new key

```bash
mv ~/.ssh/pax-ec2-key.pem ~/.ssh/pax-ec2-key.pem.old
mv ~/.ssh/pax-ec2-key-new.pem ~/.ssh/pax-ec2-key.pem
chmod 600 ~/.ssh/pax-ec2-key.pem
```

Confirm SSH still works:

```bash
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@$MAGNIPHYQ_IP "echo ok"
```

---

## 6. Update the key on the Cursor cloud VM

The cloud agent uses the key at `SSH_KEY_PATH` on the **cloud VM**. Update that file to the new key **without pasting it in chat**:

- **Preferred:** From your Mac, `scp` the new key to the cloud VM (e.g. Cursor gives you an SSH host for the cloud workspace):  
  `scp -i <key-to-cloud-vm> ~/.ssh/pax-ec2-key.pem ubuntu@<cloud-vm>:<SSH_KEY_PATH>`
- **Or:** In Cursor, if you use “Secret files” or “Attach file” for the cloud environment, replace the attached key file with the new one (e.g. re-upload).
- On the cloud VM, run: `chmod 600 "$SSH_KEY_PATH"` (or have the agent run that only; the agent should not create or edit the key file from chat).

Then re-run the SSH check in the cloud agent; it should still return `ok` using the new key.

---

## 7. Other EC2 instances (PHY600 fleet)

If other instances (e.g. rerun_v2 workers) were launched with the same key and you still use them, repeat steps 2–4 for each: add the new public key, test, then remove the old public key from `~/.ssh/authorized_keys`. For **new** launches, create or import the new key pair in EC2 and use it when launching instances so they get the new key from the start.

---

## 8. Optional: AWS key pair (for new launches)

In **EC2 → Key Pairs**, you can register the new key so future instances get it at launch:

- **Create key pair** → paste the **new public** key (from `~/.ssh/pax-ec2-key.pem.pub` or the `.pub` file you generated), name it e.g. `pax-ec2-key-2025`.
- When launching new instances, select this new key pair. Existing instances are already updated via `authorized_keys` in steps 2–4.

---

**See also:** `.meta/docs/SECRETS_FOR_CLOUD_AGENTS.md`, `.meta/docs/CLOUD_AGENT_SETUP_GUIDE.md`.
