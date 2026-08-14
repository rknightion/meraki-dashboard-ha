# GitHub Issues archive

`github-issues-2026-08-14.json` is the complete contents of this repository's GitHub Issues tracker
as of **2026-08-14**, captured immediately before the issues themselves were deleted. The project
moved to Backlog.md on that date; see the *Closed GitHub issues* doc (`backlog doc list --plain`)
for the browsable index, and this file for the bodies and replies behind it.

**This is the record, not a convenience copy.** Most of the issues it describes no longer exist on
GitHub, so `gh issue view <N>` will 404 for them. Anything in the repository that cites `#NNN` —
`AGENTS.md`, commit messages, code comments — resolves here.

## What it contains

16 issues and all 18 comments, verified against the REST API's own per-issue comment counts before
capture — an exact per-issue match, not merely an equal total. Per issue: number, title, body, state,
state reason, author, labels, milestone, assignees, created/updated/closed timestamps, URL, and every
comment with its author and timestamp.

```sh
jq '.[] | select(.number == 303)' archive/github-issues-2026-08-14.json           # one issue
jq -r '.[] | select(.number == 303) | .comments[].body' archive/github-issues-2026-08-14.json
jq -r '.[] | select(.title | test("MT20"; "i")) | "#\(.number) \(.title)"' archive/github-issues-2026-08-14.json
jq -r '.[] | "#\(.number)\t\(.state)\t\(.title)"' archive/github-issues-2026-08-14.json  # the lot
```

## It is redacted, and the placeholders are stable

Bug reports quoted Meraki tenant identifiers and a third party's Home Assistant system-health dump —
exactly what this repository's own rules keep out of tracked files. Committing them raw would have
moved those details from somewhere deletable into permanent public git history at the moment the
issues were being deleted, so they were replaced first. 41 substitutions over 16 distinct
placeholders.

| Placeholder | Was |
| --- | --- |
| `<contributor-N>` | GitHub handles of external reporters |
| `<meraki-network-id-N>` | Meraki network IDs (`L_…`) |
| `<meraki-serial-N>` | Meraki device serials |
| `<network-name-N>` | Meraki network names |
| `<timezone>`, `<cloud-region>`, `<nabucasa-remote-host>` | a reporter's locale and Nabu Casa remote endpoint |
| `<subscription-expiry>` | a reporter's HA Cloud subscription expiry |
| `<installed-addons-list>` | a reporter's installed add-on inventory |
| `<veth-iface>` | Docker veth interface names |

**One distinct real value maps to one placeholder throughout**, so a reader can still tell that two
issues discuss the same network without learning which network. `<network-name-3>` covers a name that
appeared in both cases in the source logs.

Redaction was applied and verified over **decoded fields**, never over the serialized JSON. Sweeping
the serialized blob is the convenient method and it produces false passes: a `\n` escape leaves a
literal `n` against the following word and breaks a `\b` word boundary. On this particular dump the
two methods happened to agree (32 occurrences each pre-redaction) because no target value sat next to
an escape — that is luck, not a reason to trust the blob sweep next time.

## What was deliberately left in

- **Pinned GitHub Action commit SHAs** in the Renovate dependency dashboards (#50, #256). These are
  40-hex and look exactly like Meraki API keys to a naive scan; they are public upstream references
  and one is a commit in this repository. Checked individually, not assumed.
- **`1.1.1.1` and `8.8.8.8`** — Cloudflare and Google public resolvers listed in a `nameservers`
  field, not addresses belonging to anyone.
- **GitHub comment IDs** inside `comments[].url`, which are 9–10 digit numbers and trip an org-ID
  pattern. They identify a comment on a deleted issue, nothing else.
- **Versions, counts, sizes and timings** from the system-health dump. Aggregate figures are fine
  under the repository rules; only the identifying fields were replaced.

## Issues that still exist on GitHub

Deletion was scoped to the **ten issues authored by the repository owner** — #293, #295–#303. Those
now 404.

Six issues were deliberately kept and still exist on GitHub:

| # | Author | Why it stayed |
| --- | --- | --- |
| 132, 143, 144 | external contributor | filed by someone else; not ours to delete |
| 218 | external contributor | filed by someone else; not ours to delete |
| 50, 256 | Renovate | dependency dashboards, recreated on the next run anyway |

The tracker remains enabled for new external bug reports. It is no longer where this project's own
work is planned — that is `backlog/`.

This archive contains all **16**, kept and deleted alike, so it is a superset of what was removed.
