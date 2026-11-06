# Security policy

CNTXT1 is a starter kit: markdown conventions plus scripts that run on your own
machine against your own vault, and optional add-ons (`SYSTEM/optional/`) that
can expose parts of a vault to the network, such as `remote-access/`.

## Reporting a vulnerability

**Please don't open a public issue.** Report it privately instead:

- Go to the repo's **Security** tab and choose **Report a vulnerability**
  (GitHub private vulnerability reporting).
- Include what's affected (file or add-on), how to reproduce it, and the impact.

You'll get an acknowledgement within a few days. Fixes land on `main`; there are
no separately maintained release branches.

## In scope

- Anything that could leak vault content beyond the machine or the private remote
  you chose: path traversal, unsafe file writes, auth bypass in the
  `remote-access/` add-ons, secrets ending up in logs or commits.
- The privacy gate (`.github/scripts/pr-gate.sh`) failing to catch personal content.

## Out of scope

- Issues in your own vault's content or in third-party tools the kit calls
  (Claude Code, Obsidian, Syncthing, Cloudflare). Report those upstream.
