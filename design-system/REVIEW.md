# UI Design Review — Invoice Automation

**Reviewed:** 2026-06-23 · **Branch:** `ui-design-review` · **Scope:** `web_app.py` `GLOBAL_CSS` (L40–300), `.streamlit/config.toml`
**Rubric:** `sk-design-system-framework` (three-layer spec, no-adjective values, WCAG 2.2 AA, token completeness, full interaction states)

Companion docs: [`SPEC.md`](./SPEC.md) is the canonical source of truth derived from this review.

---

## Verdict

The current UI is a **coherent, well-built dark glassmorphism system** — it already has a real `:root` token layer, a disciplined status-colour scheme, and consistent transitions. It is *above* the baseline most apps start from. The gaps are not aesthetic; they are **systematisation gaps**: half the design (colour) is tokenised and half (spacing, radius, shadow, type, motion, focus) is hardcoded inline. This review snaps the whole system onto tokens and fixes one real accessibility failure.

Overall grade against the framework: **B** — strong foundation, incomplete token coverage, two accessibility gaps.

---

## What's already good (keep)

| Area | Evidence | Verdict |
|---|---|---|
| Colour token layer | `:root` block, L77–97 — 23 named colour tokens | ✅ Real semantic tokens |
| Status colour contrast | green `#34D399` 8.46:1, amber `#FBBF24` 9.75:1, red `#F87171` 5.88:1 on cards | ✅ All pass AA |
| Body text contrast | `--text-primary #E2E8F0` 13.20:1, `--text-secondary #94A3B8` 6.35:1 | ✅ Pass AAA / AA |
| Transition consistency | `0.15s ease` used uniformly | ✅ One timing, just not tokenised |
| Theme/CSS sync | `config.toml` tokens match CSS (`#0F1923`, `#E2E8F0`, `#162231`) | ✅ In sync |
| XSS discipline | `inv_card_html` escapes all untrusted fields (L308–328) | ✅ Not a design issue but worth noting |

---

## Findings

Ordered by severity. IDs are referenced by `SPEC.md` and the refactor commit.

### A11Y-1 — Muted text fails WCAG AA contrast (High)
`--text-muted #64748B` is used for `.inv-detail` (Store / PO lines, `0.8rem`), `.inv-warning` indent, and other small secondary text.

| Background | Ratio | AA (4.5:1 normal text) |
|---|---|---|
| Card `#15212F` (rgba(22,34,49,.85) over bg) | **3.42:1** | ❌ Fail |
| App bg `#0F1923` | **3.73:1** | ❌ Fail |

These are `0.8rem`/`0.78rem` (≈12.5px) lines — squarely "normal text", so 4.5:1 applies, not the 3:1 large-text allowance.

**Fix (specified):** lighten `--text-muted` to **`#7C8BA1`** → 4.70:1 (card) / 5.12:1 (app). Minimal hue shift, preserves the grey-blue character. *(`#74829A` is the absolute floor at 4.19:1 card — rejected; sits below 4.5:1 on cards.)*

### A11Y-2 — No visible focus states for keyboard users (High)
The framework mandates `focus-visible` on every interactive component (WCAG 2.2 §2.4.11/2.4.7). The CSS defines `:hover` everywhere but **never `:focus-visible`**. Buttons, the file uploader, expanders, and selects rely on Streamlit/browser defaults, which the heavy `!important` overrides can suppress.

**Fix (specified):** tokenised focus ring — `--ring #38BDF8`, `--focus-ring-width 2px`, `--focus-ring-offset 2px`. Ring contrast: 7.60:1 (card) / 8.28:1 (app), well above the 3:1 UI-component minimum. Applied via `:focus-visible` (not `:focus`, so it doesn't fire on mouse click).

### TOKEN-1 — Spacing is hardcoded and off-grid (Medium)
No spacing tokens exist. Inline values: `0.15rem, 0.2rem, 0.3rem, 0.4rem, 0.5rem, 0.75rem, 1rem, 1.1rem, 1.4rem, 1.5rem, 2rem` — eleven ad-hoc values, several off any 4px grid (`1.1rem`=17.6px, `1.4rem`=22.4px).

**Fix:** adopt the framework spacing scale **4 / 8 / 12 / 16 / 24 / 32** (`--space-1..6`). Snap each current value to nearest step (max shift ≈2px — visually imperceptible). E.g. card padding `1.1rem 1.4rem` → `16px 24px`; margin `0.75rem` → `12px`.

### TOKEN-2 — Radius, shadow, and motion not tokenised (Medium)
- **Radius** drifts: cards `10px`, headers/buttons `8px`. No token.
- **Shadow** literals repeated inline (`0 4px 16px rgba(0,0,0,.3)…`, hover `0 8px 24px…`).
- **Transition** `0.15s ease` copy-pasted into ~6 rules.

**Fix:** `--radius-sm 8px`, `--radius-md 10px`; `--shadow-card`, `--shadow-card-hover`; `--transition-fast 0.15s`, `--transition-easing ease`. Radius standardised: pills/buttons/headers `--radius-sm`, cards `--radius-md`.

### TOKEN-3 — Typography scale is unsystematic (Medium)
Seven near-duplicate font sizes: `0.78, 0.8, 0.85, 0.875, 0.95, 1rem` (12.5–16px) plus Streamlit heading defaults. No scale, no weight tokens (weights `500/600/700` inline).

**Fix:** 6-step scale **12 / 13 / 14 / 15 / 16 / 21** (`--text-xs..2xl`), weights `--weight-regular 400 / -medium 500 / -semibold 600 / -bold 700`. Each component maps to the nearest step (≤1px shift). Font family already correct (Outfit).

### ARCH-1 — `!important` saturation and Streamlit-coupled selectors (Low)
Nearly every rule uses `!important` and targets internal Streamlit testids (`data-testid="stBaseButton-primary"`, `.st-key-reset_app`). This is **partly unavoidable** (Streamlit injects its own high-specificity styles), but it makes the system brittle across Streamlit upgrades.

**Disposition:** Keep `!important` where it fights Streamlit defaults (documented as a constraint, not a defect), but route every *value* through a token so a Streamlit change only needs selector edits, never value hunts. No selector rewrite in this pass.

### ARCH-2 — Interaction values not named/tokenised (Low)
Hover changes background + shadow but there's no named "lift/press" pattern, no `--disabled-opacity`. Active/pressed and disabled states are undefined for custom elements.

**Fix:** define named patterns (Colour-change hover, Focus ring, Press, Disabled) with exact values in `SPEC.md` §5; add `--disabled-opacity 0.5`, `--press-scale 0.98`.

---

## Token coverage scorecard (framework quality gate 5)

| Token group | Before | After (SPEC + refactor) |
|---|---|---|
| Colour | ✅ tokenised | ✅ |
| Spacing | ❌ hardcoded | ✅ `--space-1..6` |
| Radius | ❌ hardcoded | ✅ `--radius-sm/md` |
| Shadow | ❌ inline literals | ✅ `--shadow-*` |
| Typography (size/weight) | ❌ inline | ✅ `--text-*`, `--weight-*` |
| Motion | ❌ inline | ✅ `--transition-*` |
| Focus / interaction | ❌ absent | ✅ `--ring`, `--focus-ring-*`, `--disabled-opacity`, `--press-scale` |

---

## Accessibility summary (WCAG 2.2 AA)

| Criterion | Status before | After |
|---|---|---|
| 1.4.3 Contrast (text) | ❌ muted text 3.42:1 | ✅ 4.70:1 (`#7C8BA1`) |
| 1.4.11 Non-text contrast | ⚠️ borders low but decorative | ✅ focus ring 7.6:1 |
| 2.4.7 / 2.4.11 Focus visible | ❌ none defined | ✅ `:focus-visible` ring |
| 2.5.5 Target size (44px) | ⚠️ some buttons `<44px` tall | ✅ min-height tokenised to 44px |
| 2.3.3 / prefers-reduced-motion | ❌ not handled | ✅ `@media (prefers-reduced-motion)` block |

---

## Recommendation & sequencing

1. **Adopt `SPEC.md`** as the single source of truth (done in this branch).
2. **Refactor `GLOBAL_CSS`** to consume tokens with **visual parity** — only A11Y-1/-2 change pixels; everything else snaps within ≤2px (done in this branch, `web_app.py`).
3. Keep `config.toml` in sync (no token changes needed — values unchanged).
4. Future: revisit ARCH-1 selector coupling when Streamlit is next upgraded.
