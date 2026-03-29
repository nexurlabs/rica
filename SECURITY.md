# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Rica, please report it by:

1. **Do not** open a public GitHub issue.
2. Email: `security@nexurlabs.com`
3. Include as much detail as possible — we will acknowledge within 48 hours.

We aim to triage and fix reported vulnerabilities promptly. We request that you give us a reasonable time before disclosing any vulnerability publicly.

## Security Best Practices (Self-Hosted)

When self-hosting Rica:

- **Never** commit your `config.yaml` or API keys to version control
- Use environment variables for secrets where possible
- Keep your Discord bot token private — treat it like a password
- Restrict access to the machine running Rica
- Keep Rica updated — run `git pull` periodically to get the latest patches
- The `online-mode=false` setting means Rica trusts Discord's authentication — do not expose the Minecraft server port to untrusted networks without additional authentication
