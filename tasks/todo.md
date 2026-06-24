# Todo

## Action Required

- [ ] **Enable the access password on the live app** — the password gate is in the
      code but inactive until the secret is set. In Streamlit Cloud: Manage app →
      Settings → Secrets, add `app_password = "..."`. Until then the deployed app
      is open to anyone with the link. (See `.streamlit/secrets.toml.example`.)

## Action Required (next)

- [ ] **Persistent storage for the editable config lists (nominal codes + store names)**
      — currently both are read-only in the app ("contact Samuel"), because edits to
      `data/nominal_codes.json` / `data/known_stores.json` are wiped on Streamlit Cloud
      redeploys (ephemeral filesystem). To make them genuinely team-editable, move the
      backing store off the local filesystem. Options discussed: Google Sheets
      (`st-gsheets-connection`, also editable in a spreadsheet), Supabase (free Postgres),
      GitHub commit-back, or moving host to one with a persistent volume. Recommended:
      Google Sheets. Brainstorm/spec before building. Pairs with a general sidebar
      polish (the config editors felt fiddly/unpolished).

## Possible Future Work

- [ ] Per-user login via `st.login` (OIDC / Google `@giftuniverse.com`) instead of a shared password
- [ ] Full `Optional[Decimal]` migration for amount fields (deeper than the invariant refactor already done)
- [ ] CJL `286301` VAT mis-read (£20 instead of £1,736.40) — CJLExtractor-specific
- [ ] Grey row styling in Excel output (user may request)
- [ ] Authorised column handling (user may request)
- [x] Automated tests for extraction and matching (added: test_generic_extractor, test_matching, test_models)
- [ ] Handle multi-page invoice tables (e.g. Amazon page 2 line items)
