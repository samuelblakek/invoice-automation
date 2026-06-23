# Design System Spec — Invoice Automation

> Single source of truth for the Menkind Maintenance PO Processing UI.
> Every value here is exact (number / hex / token). No adjectives.
> Derived by reverse-engineering the existing `web_app.py` UI (see [`REVIEW.md`](./REVIEW.md)), with two accessibility fixes applied (A11Y-1, A11Y-2).

---

## 1. Context and goals

- **Project:** Rule-based invoice extraction + PO matching dashboard (Streamlit).
- **Platform:** Web — Streamlit + injected global CSS (`GLOBAL_CSS` in `web_app.py`), single page, `layout="wide"`.
- **Visual direction:** Dark slate/navy glassmorphism. Layered radial-gradient background, SVG grain overlay, frosted translucent cards and sidebar, near-white neutral primary action.
- **Density:** Standard (data-dense 3-column board; spacing scale starts at 4px).
- **Theme constraint:** `.streamlit/config.toml` `[theme]` tokens must stay in sync with the colour tokens below.

---

## 2. Design tokens and foundations (Layer 1)

All tokens live in `:root`. The **only** raw values permitted outside `:root` are `0` and the SVG data-URI in the grain overlay.

### 2.1 Typography
```
--text-xs:   12px;   /* warnings, fine print */
--text-sm:   13px;   /* card detail, error, supplier lines */
--text-base: 14px;   /* column headers, inline metrics, button labels */
--text-md:   15px;   /* invoice number (card title) */
--text-lg:   16px;   /* invoice amount, metric values */
--text-2xl:  21px;   /* section headings */

--font-primary: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-icon:    'Material Symbols Rounded', sans-serif;  /* preserve for Streamlit icon glyphs */

--weight-regular:  400;
--weight-medium:   500;
--weight-semibold: 600;
--weight-bold:     700;

--line-tight: 1.3;
--line-body:  1.4;
```

### 2.2 Colours (23 + 4 new)

**Surface / text**
```
--bg-primary:    #0F1923;                    /* app background base */
--bg-card:       rgba(255,255,255,0.05);     /* generic translucent surface */
--bg-card-hover: rgba(255,255,255,0.08);
--bg-elevated:   rgba(255,255,255,0.10);
--bg-card-solid:       rgba(22,34,49,0.85);  /* .inv-card resolved bg (no backdrop-filter) */
--bg-card-solid-hover: rgba(26,40,56,0.90);
--border-subtle: rgba(255,255,255,0.08);
--border-medium: rgba(255,255,255,0.15);
--text-primary:  #E2E8F0;   /* 13.20:1 on card — AAA */
--text-secondary:#94A3B8;   /*  6.35:1 on card — AA  */
--text-muted:    #7C8BA1;   /*  4.70:1 on card — AA  (A11Y-1: was #64748B / 3.42:1) */
--accent:        #E2E8F0;
```

**Status (each: solid / 10% bg fill / 25% border)**
```
--green:        #34D399;  --green-bg:  rgba(52,211,153,0.10);  --green-border:  rgba(52,211,153,0.25);  /* 8.46:1 */
--amber:        #FBBF24;  --amber-bg:  rgba(251,191,36,0.10);  --amber-border:  rgba(251,191,36,0.25);  /* 9.75:1 */
--red:          #F87171;  --red-bg:    rgba(248,113,113,0.10); --red-border:    rgba(248,113,113,0.25); /* 5.88:1 */
```
Mapping to framework status roles: success = `--green`, warning = `--amber`, danger/destructive = `--red`. (Brighter tints than the framework defaults `#16A34A/#D97706/#DC2626`, chosen for legibility on the dark surface — all exceed AA.)

**Primary action (near-white neutral)**
```
--btn-primary-bg:        #E2E8F0;  --btn-primary-bg-hover:  #FFFFFF;
--btn-primary-text:      #0F1923;  --btn-primary-text-hover:#000000;   /* 14.39:1 */
```

**Focus / interaction (A11Y-2, new)**
```
--ring:              #38BDF8;   /* 7.60:1 card / 8.28:1 app — UI-component min is 3:1 */
--focus-ring-width:  2px;
--focus-ring-offset: 2px;
--disabled-opacity:  0.5;
--press-scale:       0.98;
```

### 2.3 Spacing
```
--space-1: 4px;  --space-2: 8px;  --space-3: 12px;
--space-4: 16px; --space-5: 24px; --space-6: 32px;
```
4px base unit. No spacing value outside this scale.

### 2.4 Borders & radius
```
--border-width: 1px;
--border-style: solid;
--radius-sm: 8px;    /* buttons, column-header pills */
--radius-md: 10px;   /* cards */
--card-accent-width: 3px;   /* .inv-card left status stripe */
```

### 2.5 Shadows
```
--shadow-card:       0 4px 16px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.05);
--shadow-card-hover: 0 8px 24px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.08);
--shadow-none:       none;
```

### 2.6 Transitions
```
--transition-fast:   0.15s;
--transition-easing: ease;
```

### 2.7 Layout & effects
```
--sidebar-blur:        16px;       /* backdrop-filter on sidebar */
--sidebar-bg:          rgba(255,255,255,0.03);
--sidebar-border:      rgba(255,255,255,0.06);
--grain-opacity:       0.04;
--grain-tile:          200px;
--touch-target-min:    44px;       /* WCAG 2.5.5 */
--board-columns:       3;          /* Matched / Review / Failed */
```
Background composition (literal, lives on `.stApp`, references no raw colour outside this list):
```
--glow-sky:    rgba(56,189,248,0.06);
--glow-violet: rgba(139,92,246,0.04);
--bg-gradient-top: #1A2A3A;   /* radial centre at 50% 0% */
```

---

## 3. Composition rules (Layer 3) — Standard density

| Relationship | Value | Applied to |
|---|---|---|
| icon-to-text | `--space-2` (8px) | sidebar header, buttons |
| button-group-gap | `--space-2` (8px) | Approve/Skip pair, download row |
| label-to-input | `--space-1` (4px) | uploaders, code editor |
| field-to-field | `--space-3` (12px) | sidebar uploaders |
| card-grid-gap | `--space-4` (16px) | 3-column board |
| list-item-gap | `--space-3` (12px) | stacked invoice cards (`margin-bottom`) |
| card-padding | `--space-4 --space-5` (16px 24px) | `.inv-card` |
| header-pill-padding | `--space-2 --space-4` (8px 16px) | `.col-header` |
| header-to-body | `--space-4` (16px) | column header → first card |
| inline-metrics-gap | `--space-6` (32px) | metric row |
| section-to-section | `--space-6` (32px) | `.section-divider` margin |
| sidebar-to-content | `--space-5` (24px) | Streamlit default, do not shrink |

---

## 4. Component-level rules (Layer 2)

This app renders a focused subset of the 35 framework component families. Families **present** get full state tables; families **not used** are listed N/A so coverage is explicit.

**Present:** buttons (primary / secondary / destructive / download), cards (`.inv-card`), badges/pills (`.col-header`), stats/metrics (`.inline-metric`), file uploaders, selects, text/code inputs (nominal-code editor), expanders (accordions), sidebar, top heading, alerts (Streamlit `st.warning/error/success`), empty states.

**N/A (not in product):** comboboxes, checkboxes/radios/switches, date/time pickers, tables/data-grids, charts, avatars, breadcrumbs, pagination, steppers, modals, drawers, tooltips, popovers, command palette, tabs, carousels, skeletons, notifications centre, onboarding, auth screens (handled by `_check_password` text input only), pricing.

### 4.1 Buttons — primary (near-white neutral)
| State | Values |
|---|---|
| default | bg `--btn-primary-bg`, text `--btn-primary-text`, border `--border-width --border-style --btn-primary-bg`, radius `--radius-sm`, font `--text-base`/`--weight-semibold`, letter-spacing 0.01em, transition `background --transition-fast --transition-easing` |
| hover | bg `--btn-primary-bg-hover`, text `--btn-primary-text-hover`, border `--btn-primary-bg-hover` |
| focus-visible | outline `--focus-ring-width --border-style --ring`, outline-offset `--focus-ring-offset` |
| active | transform `scale(--press-scale)` |
| disabled | opacity `--disabled-opacity`, cursor `not-allowed` |
| loading | Streamlit spinner, colour `--btn-primary-text`, inline |
| error | N/A (action button, no validation state) |

Min height `--touch-target-min` for the primary process/approve actions.

### 4.2 Buttons — secondary (ghost)
| State | Values |
|---|---|
| default | bg `transparent`, text `--text-secondary`, border `--border-width --border-style --border-medium`, radius `--radius-sm`, font `--text-base`/`--weight-medium` |
| hover | bg `--bg-elevated`, text `--text-primary`, border `--text-muted` |
| focus-visible | outline `--focus-ring-width --border-style --ring`, offset `--focus-ring-offset` |
| active | transform `scale(--press-scale)` |
| disabled | opacity `--disabled-opacity`, cursor `not-allowed` |
| loading / error | N/A |

### 4.3 Buttons — destructive (Reset App, `.st-key-reset_app`)
| State | Values |
|---|---|
| default | bg `transparent`, text `--red`, border `--border-width --border-style --red-border`, radius `--radius-sm`, font `--text-base`/`--weight-semibold` |
| hover | bg `--red-bg`, border `--red`, text `--red` |
| focus-visible | outline `--focus-ring-width --border-style --red`, offset `--focus-ring-offset` |
| active | transform `scale(--press-scale)` |
| disabled | opacity `--disabled-opacity`, cursor `not-allowed` |

### 4.4 Buttons — download
Default: radius `--radius-sm`, font `--text-base`/`--weight-semibold`, min-height `--touch-target-min`, inner `<p>` `--text-base`/line-height `--line-tight`. States inherit secondary unless Streamlit overrides; focus-visible ring as above.

### 4.5 Card — `.inv-card`
| State | Values |
|---|---|
| default | bg `--bg-card-solid`, border `--border-width --border-style --border-subtle`, left-border `--card-accent-width --border-style var(--card-accent, --border-subtle)`, radius `--radius-md`, padding `--space-4 --space-5`, margin-bottom `--space-3`, shadow `--shadow-card`, transition `border-color, background, box-shadow --transition-fast --transition-easing` |
| hover | bg `--bg-card-solid-hover`, border `--border-medium`, shadow `--shadow-card-hover` |
| focus-visible | N/A (non-interactive container; action lives in child buttons) |
| status accent | `--card-accent` set per card to `--green` / `--amber` / `--red` / `--border-subtle` |

Card text: `.inv-num` `--text-md`/`--weight-bold`/`--text-primary`; `.inv-supplier` `--text-sm`/`--text-secondary`; `.inv-amount` `--text-lg`/`--weight-semibold`/`--text-primary`; `.inv-detail` `--text-sm`/`--text-muted`; `.inv-error` `--text-sm`/`--red`; `.inv-warning` `--text-xs`/`--amber`/line-height `--line-body`.

### 4.6 Badge / column-header pill — `.col-header`
Default: padding `--space-2 --space-4`, radius `--radius-sm`, font `--text-base`/`--weight-semibold`, text-align center, border `--border-width --border-style`. Variants: green = `--green-bg`/`--green`/`--green-border`; amber = `--amber-*`; red = `--red-*`. Static (no hover/focus — N/A).

### 4.7 Stat / inline metric — `.inline-metric`
Row: display flex, gap `--space-6`, border-bottom `--border-width --border-style --border-subtle`, padding-block `--space-3`. Label `--text-base`/`--text-secondary`; value `strong` `--text-lg`/`--weight-bold`/`--text-primary`.

### 4.8 Inputs / selects / file uploader (Streamlit-rendered)
All must receive: focus-visible outline `--focus-ring-width --border-style --ring` offset `--focus-ring-offset`; disabled opacity `--disabled-opacity`. Error state uses Streamlit's `st.error` (border/text `--red`, bg `--red-bg`). Preserve `--font-icon` on uploader/dropzone glyphs.

### 4.9 Sidebar
bg `--sidebar-bg`, backdrop-filter `blur(--sidebar-blur)`, border-right `--border-width --border-style --sidebar-border`.

### 4.10 Alerts / empty states
Alerts via Streamlit `st.warning/error/success` — colours map to `--amber`/`--red`/`--green`. Empty state (no files): `--text-secondary`, `--text-base`, centred prompt text.

---

## 5. Named interaction patterns (exact CSS)

```
/* Colour-change hover — surfaces & ghost buttons */
transition: background var(--transition-fast) var(--transition-easing),
            border-color var(--transition-fast) var(--transition-easing),
            box-shadow var(--transition-fast) var(--transition-easing);
/* on :hover swap bg/border/shadow tokens per component table */

/* Focus ring — every interactive element */
:focus-visible {
  outline: var(--focus-ring-width) var(--border-style) var(--ring);
  outline-offset: var(--focus-ring-offset);
}

/* Press */
:active { transform: scale(var(--press-scale)); }

/* Disabled treatment */
:disabled, [aria-disabled="true"] {
  opacity: var(--disabled-opacity);
  cursor: not-allowed;
  pointer-events: none;
}

/* Card lift — shadow-only (no translate, avoids scroll artefacts noted in CLAUDE.md) */
.inv-card:hover { box-shadow: var(--shadow-card-hover); background: var(--bg-card-solid-hover); }
```

---

## 6. Accessibility requirements (WCAG 2.2 AA — testable)

| ID | Requirement | Acceptance test |
|---|---|---|
| A11Y-1 | Text ≥ 4.5:1 (normal), 3:1 (≥18.66px bold/24px) | All `--text-*` colour pairs computed ≥ threshold; `--text-muted` = `#7C8BA1` ≥ 4.5:1 on card & app bg |
| A11Y-2 | Visible focus on every interactive element | Tab through app: each button/input/expander shows `--ring` outline at `--focus-ring-offset` |
| A11Y-3 | Touch targets ≥ 44px | Primary/approve/download buttons `min-height: var(--touch-target-min)` |
| A11Y-4 | Reduced motion respected | `@media (prefers-reduced-motion: reduce)` sets `transition: none` and `transform: none` |
| A11Y-5 | Semantic HTML / keyboard order | No positive `tabindex`; native `<button>`/inputs (Streamlit defaults) preserved |
| A11Y-6 | Focus not `:focus` but `:focus-visible` | Mouse click does not trigger ring; keyboard does |

```
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition-duration: 0.01ms !important; }
  :active { transform: none !important; }
}
```

---

## 7. Anti-patterns and prohibited implementations

1. **No raw values in CSS rules.** Every length/colour/duration references a token. Only `0` and the grain SVG data-URI are exempt. (Was the dominant defect — see TOKEN-1/2/3.)
2. **No off-scale spacing.** Only `--space-1..6`. No `1.1rem`, `0.78rem`, etc.
3. **No `:hover`-only interactivity.** Every hover rule needs a matching `:focus-visible`.
4. **No `--text-muted` below 4.5:1.** Never revert `#7C8BA1` → `#64748B`.
5. **No new radius/shadow literals.** Use `--radius-sm/md`, `--shadow-card/-hover`.
6. **Do not strip `--font-icon` restores.** Material Symbols glyphs break if Outfit overrides them (expanders, uploader, sidebar toggle).
7. **`!important` only to override Streamlit defaults** — never to win a battle against our own tokens.
8. **Keep `config.toml` in sync** with `--bg-primary`, `--btn-primary-bg`, `--text-primary`, and `#162231` secondary background.

---

## 8. QA checklist (code-review executable)

- [ ] No length/colour/duration literal in `GLOBAL_CSS` outside `:root` (except `0` and grain SVG).
- [ ] `--text-muted` is `#7C8BA1`; grep finds no `#64748B`.
- [ ] Every `:hover` rule has a sibling `:focus-visible` (or component is non-interactive).
- [ ] `prefers-reduced-motion` block present.
- [ ] Primary/approve/download buttons have `min-height: var(--touch-target-min)`.
- [ ] Spacing values all reference `--space-*`; no bare `rem`/`px` gaps/padding.
- [ ] Radius only `--radius-sm`/`--radius-md`; shadow only `--shadow-*`.
- [ ] `config.toml` `[theme]` matches colour tokens.
- [ ] Material Symbols icons still render (expander arrows, uploader, sidebar toggle).
- [ ] Visual diff vs. `main`: only muted-text colour and focus rings differ; layout unchanged.
