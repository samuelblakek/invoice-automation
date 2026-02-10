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

## Completed: Project Structure Cleanup

- [x] Delete CLI entry point (`main.py`) and config (`config.yaml`)
- [x] Delete CLI workflow scripts (`RUN_AUTOMATION.bat`, `RUN_AUTOMATION.command`, `SETUP_WINDOWS.bat`, `SETUP_MAC.command`)
- [x] Delete `invoice_automation/config/` directory (only used by main.py)
- [x] Delete empty `output/` directory
- [x] Remove unused `Config` import from `web_app.py`
- [x] Update `README.md` — remove CLI references and update project tree
- [x] Update `CLAUDE.md` — remove main.py entry point, config package, CLI test command
- [x] Update `docs/user-guide.md` — remove CLI Workflow section
- [x] Update `docs/deployment.md` — remove main.py from upload list
- [x] Clean up `.gitignore` — remove CLI-only entries

## Pending

- [ ] User confirming results with colleague
- [ ] Grey row styling in Excel (user may request)
- [ ] Authorised column handling (user may request)
