# OpenCode AI Design Specification (VoiceGuard Enterprise)

Extracted directly from **VoltAgent/awesome-design-md** (`opencode.ai/DESIGN.md`).

---

## 1. Design System Philosophy & Core Tokens

The OpenCode AI design system is a monochrome, terminal-native layout built on a warm cream canvas:
* **Typography:** ONE font family across the entire application—**JetBrains Mono** (open-source substitute for Berkeley Mono)—in weights 400, 500, and 700. No sans-serif or display fonts.
* **Canvas & Surfaces:** Warm cream canvas (`#fdfcfc`) for the main background and all containers. Elevated surfaces use Surface Soft (`#f8f7f7`) or Surface Card (`#f1eeee`).
* **Reserved Dark Surface Rule:** The design system reserves dark surfaces (`Surface Dark` `#201d1d`) for **exactly ONE high-emphasis element per page**. In VoiceGuard, this is reserved specifically for the **`CRITICAL` Risk Alert Banner**, providing a single high-impact focal point when a dangerous call is detected.
* **Borders & Radii:** 
  - Containers, sections, and cards use **0px sharp rectangles** with hairline borders (`1px solid rgba(15,0,0,0.12)`).
  - Interactive elements (buttons, inputs, status tags) use a **4px border-radius** (`rounded-[4px]`).
* **Elevation & Shadows:** **NO drop shadows anywhere. NO gradients.** All surfaces are flat with hairline borders.
* **Semantic Signals:** Monochromatic canvas where color is strictly reserved for actual risk-tier signals:
  - **Success / LOW Risk:** `#30d158`
  - **Warning / MEDIUM/HIGH Risk:** `#ff9f0a` (hover `#cc7f08`, active `#995f06`)
  - **Danger / CRITICAL Risk:** `#ff3b30` (hover `#d70015`, active `#a50011`)
  - **Accent / Info:** `#007aff`

---

## 2. Token Definitions

```yaml
colors:
  canvas: "#fdfcfc"
  ink: "#201d1d"
  ink-deep: "#0f0000"
  charcoal: "#302c2c"
  body: "#424245"
  mute: "#646262"
  stone: "#6e6e73"
  ash: "#9a9898"
  surface-soft: "#f8f7f7"
  surface-card: "#f1eeee"
  surface-dark: "#201d1d"
  surface-dark-elevated: "#302c2c"
  hairline: "rgba(15,0,0,0.12)"
  hairline-strong: "#646262"
  accent: "#007aff"
  danger: "#ff3b30"
  danger-hover: "#d70015"
  danger-active: "#a50011"
  warning: "#ff9f0a"
  warning-hover: "#cc7f08"
  warning-active: "#995f06"
  success: "#30d158"

typography:
  display-xl: "38px / 700 / line-height 1.5"
  heading-md: "16px / 700 / line-height 1.5"
  body-md: "16px / 400 / line-height 1.5"
  body-strong: "16px / 500 / line-height 1.5"
  button-md: "16px / 500 / line-height 2.0"
  caption-md: "14px / 400 / line-height 2.0"

shape:
  container: "0px radius, 1px hairline border"
  interactive: "4px radius (buttons, inputs, pills)"
  shadows: "NONE"
  gradients: "NONE"
```

---

## 3. Marketing-to-Dashboard Adaptation Rationale

Since the source `DESIGN.md` was extracted from OpenCode's marketing/landing pages, we translated marketing component patterns into operational dashboard equivalents:

1. **`hero-tui-mockup` Dark Full-Bleed Pattern (`#201d1d` Surface Dark):**
   * *Source Use:* Hero block showcasing the OpenCode TUI terminal interface.
   * *Dashboard Translation:* Reserved as the single high-emphasis dark surface on the page for the **`CRITICAL` Risk Action Banner**. When a call hits CRITICAL tier, the Action Banner switches from a flat cream card to a stark full-bleed `#201d1d` dark card with `#ff3b30` text, drawing immediate urgency without violating the single dark surface rule.

2. **`list-row` Bracket-Bullet Pattern (`[+]` / `[-]` / `[x]`):**
   * *Source Use:* Feature lists and comparison tables.
   * *Dashboard Translation:* Applied to the **Evidence Breakdown** rows and status indicators. `[+]` indicates positive/verification signals (e.g. ECAPA-TDNN speaker match), `[-]` indicates neutral/contextual factors (e.g. caller number), and `[x]` indicates detected anomalies or synthetic risk contributions.

3. **`badge-section-label` Pattern:**
   * *Source Use:* Uppercase monospaced section headers.
   * *Dashboard Translation:* Applied to panel headers across all dashboard cards (e.g., `[CALLER IDENTIFIER]`, `[REAL-TIME RISK METER]`, `[EVIDENCE MATRIX]`, `[TRANSACTION CONTEXT]`).

4. **Flat Hairline Card Pattern:**
   * *Source Use:* Bordered text blocks sitting directly on cream canvas.
   * *Dashboard Translation:* All major panels (`CallerPanel`, `RiskMeter`, `EvidenceBreakdown`, `TransactionForm`, `EnrollmentForm`) are rendered as flat `#fdfcfc` rectangles bounded by `1px solid rgba(15,0,0,0.12)` hairline rules with 0px border-radius.

5. **Spacing Scale Rhythm:**
   * *Source Use:* 96px section padding for landing pages.
   * *Dashboard Translation:* Scaled down to **32px–48px gap rhythm** between major dashboard panels (`gap-6` / `space-y-6`). 96px is a marketing page rhythm; 32px-48px provides the required operational density for live fraud monitoring.

6. **Modal Border Radius Adaptation:**
   * *Source Use:* 0px containers vs 4px interactive elements.
   * *Dashboard Translation:* `ChallengeModal` content container uses **4px border-radius** (`rounded-[4px]`) to establish explicit visual popup boundary against the backdrop overlay, maintaining 4px consistency for floating dialog surfaces.
