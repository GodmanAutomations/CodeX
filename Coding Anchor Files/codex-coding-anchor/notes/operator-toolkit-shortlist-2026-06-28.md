# Operator Toolkit Shortlist - 2026-06-28

Source inspected:

- https://github.com/trimstray/the-book-of-secret-knowledge
- https://github.com/trimstray/the-book-of-secret-knowledge/blob/master/README.md
- https://github.com/trimstray/the-book-of-secret-knowledge/blob/master/LICENSE.md

## Decision

Use The Book of Secret Knowledge as an external operator reference, not as
startup context and not as an install-everything list.

The useful shape for CodeX is a small read-only toolkit inventory that supports
diagnostics, production hygiene, and repeatable evidence:

- HTTP/API smoke tests
- TLS and certificate checks
- DNS and network debugging
- logs, disk, and performance inspection
- container and security hygiene

Keep offensive, exploit, mass-scan, and public-target recon material as
reference-only unless Stephen gives an explicit authorized target and scope.

## Local Checker

Run:

```bash
bin/coding-anchor-toolkit-check
```

JSON mode:

```bash
bin/coding-anchor-toolkit-check --json
```

The command is read-only. It reports installed and missing optional tools and
prints a Homebrew install command for the missing shortlist. It does not install
packages.

## Shortlist

HTTP/API:

- `hurl` - plain-text HTTP/API smoke tests.
- `httpstat` - curl timing visualization.

TLS/certs:

- `testssl` - TLS protocol and cipher checks.
- `sslscan` - TLS cipher enumeration.
- `mkcert` - local trusted development certificates.

DNS/network:

- `mtr` - combined traceroute and ping evidence.
- `iperf3` - bandwidth checks between controlled hosts.
- `socat` - socket relay and local connectivity probes.
- `ngrep` - grep-like packet payload inspection.
- `tshark` - CLI packet capture inspection.
- `dnstwist` - typosquat and lookalike-domain checks.
- `ssh-audit` - SSH server configuration review.

Logs/performance:

- `lnav` - interactive log navigation.
- `goaccess` - web access log analysis.
- `hyperfine` - command benchmarking.
- `dust` - fast disk usage breakdowns.
- `ncdu` - interactive disk usage analysis.
- `git-delta` - readable git diffs.

Containers/security:

- `trivy` - container and dependency vulnerability scans.
- `lynis` - macOS/Linux security audit.

Operator basics:

- `yq` - YAML query and transformation.
- `aria2` - resumable multi-source downloads.

## CodeX Routing

- CodeX infra work should use `codex-infra-ops` and production hygiene first.
- Security review work should use `security-best-practices` or the relevant
  cybersecurity skill lane before tool-specific scans.
- Public scanning, exploit research, or recon must stay explicit-scope only.
- This packet should keep the checker as a local capability map, not a daemon
  and not a global workstation mutation.
