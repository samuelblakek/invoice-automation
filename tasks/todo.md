# Project Status

## Completed: Invoice Extraction & PO Matching (Phase 2)

- [x] Fix Excel reader header row detection (headers at row 5-6, not row 0)
- [x] Fix PO cell matching (substring/contains for embedded newlines)
- [x] Overhaul generic extractor patterns for real-world invoice formats
- [x] Add new supplier types to sheet selector (Sunbelt, Maxwell Jones, Metro Security, LampShop, ILUX, Store Maintenance)
- [x] Implement multi-strategy PO matching (PO -> invoice # -> fuzzy multi-field)
- [x] Make PO optional throughout pipeline
- [x] Verify all 7 example invoices extract and match correctly

## Completed: Documentation Consolidation

- [x] Create project-level `CLAUDE.md` with architecture, patterns, and gotchas
- [x] Rewrite `README.md` — concise overview with no redundancy
- [x] Create `docs/deployment.md` — merged from 4 deployment docs
- [x] Create `docs/user-guide.md` — merged web app + CLI guides
- [x] Delete 6 obsolete markdown files (QUICK_START, SETUP_GUIDE, DEPLOYMENT_GUIDE, DEPLOYMENT_SUMMARY, HOW_THE_APP_WORKS, AMOUNT_EXTRACTION_FIXES)
- [x] Delete stale output files

## Pending

- [ ] User confirming results with colleague
- [ ] Grey row styling in Excel (user may request)
- [ ] Authorised column handling (user may request)
