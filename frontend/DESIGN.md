---
name: Luminescent Kinetic Inventory
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#424936'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#727a64'
  outline-variant: '#c1cab0'
  surface-tint: '#416900'
  primary: '#416900'
  on-primary: '#ffffff'
  primary-container: '#84cc16'
  on-primary-container: '#315200'
  inverse-primary: '#91db2a'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#855300'
  on-tertiary: '#ffffff'
  tertiary-container: '#fea518'
  on-tertiary-container: '#684000'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#acf847'
  primary-fixed-dim: '#91db2a'
  on-primary-fixed: '#102000'
  on-primary-fixed-variant: '#304f00'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes a high-precision, luminous visual architecture for inventory operations and stock intelligence. Blending the analytical clarity of modern fintech with tactical warehouse velocity, it treats physical stock tracking with the same rigor and polish as institutional portfolio management.

### Personality & Emotional Tenor
- **Surgical Precision:** Every data point, threshold indicator, and count is legible within milliseconds without perceptual clutter.
- **Controlled Vitality:** An electric lime accent injects kinetic energy into an otherwise calm, light-bathed canvas, framing operational momentum without distraction.
- **Tactile Softness:** Substantial corner radiuses and micro-shadowed planes balance industrial density with approachable, modern software luxury.

### Stylistic Philosophy
The interface operates within an ultra-refined, high-clarity minimalist framework:
- **Base Canvas:** Pale off-white and cool mist backgrounds allow pure white surface cards to advance forward cleanly.
- **Hairline Precision:** Surfaces use delicate structural borders rather than heavy visual separation.
- **Targeted Chromatic Accents:** Saturated lime-green is restricted to primary interactions, active operational states, and positive health metrics. Alert ambers and coral reds are isolated strictly to exceptions, deprecations, and stockout hazards.

## Colors

The palette establishes an ultra-clean, clinical canvas calibrated for extended operational shifts and immediate status comprehension.

### Functional Roles

- **Primary (`#84CC16` - Energetic Lime):** Reserved for high-priority interactive paths, active tabs, confirmed inventory states, positive growth differentials, and critical batch triggers.
- **Secondary (`#0F172A` - Deep Obsidian Slate):** Acts as the foundational structural tone for primary headlines, critical numerical readouts, and high-emphasis controls requiring maximum contrast.
- **Tertiary (`#F59E0B` - Warm Amber):** Dedicated warning indicator for low-stock thresholds, impending reorder deadlines, and transitional synchronization states.
- **Hazard Coral (`#EF4444`):** Strictly reserved for stockouts, negative delta trajectories, batch errors, and destructive operations.
- **Neutral Canvas (`#F8F9FA` to `#F1F5F9`):** Multi-layered backdrop hierarchy providing gentle ambient separation beneath pure white data cards.

### Foreground Hierarchy
- **High Emphasis (`#0F172A` / `#111827`):** Primary metrics, SKU identifiers, column headers, and active state copy.
- **Medium Emphasis (`#64748B` / `#6B7280`):** Supporting metadata, unit indicators, table secondary keys, and placeholder states.
- **Subtle Emphasis (`#94A3B8`):** Disabled states, structural hairline rules, table gridlines, and passive icon artwork.

## Typography

Typography relies exclusively on Inter, deployed with disciplined tracking and strict tabular alignment. The system prioritizes rapid scanning of numeric values, inventory codes, and status tags over decorative expression.

### Typesetting Principles
- **Tabular Figures:** All numeric displays (stock volumes, financial valuations, SKUs, and reorder levels) must enforce tabular numerals (`tnum`) to maintain consistent vertical column geometry during real-time data shifts.
- **Tightened Tracking on Display Scales:** Large display values apply negative tracking down to `-0.03em` to anchor numbers with confidence and prevent visual diffusion.
- **Case Hierarchy:** Primary titles utilize standard sentence casing. Secondary analytical metadata, status badges, and table headers use uppercase tracking (`label-sm`) with deliberate letter spacing for micro-legibility.

## Layout & Spacing

The layout is constructed on an 8-point base grid driving a flexible 12-column layout. The system relies on structured negative space rather than heavy container dividers to group contextual actions.

### Canvas & Breakpoints
- **Desktop (1280px+):** 12-column layout with 24px gutters and 32px outer canvas margins. Maximizes horizontal metric ribbons and parallel analytical views.
- **Tablet (768px - 1279px):** 8-column layout with 20px gutters and 24px margins. Sidebars collapse to icon-rail or top drawer states.
- **Mobile (<768px):** 4-column layout with 16px gutters and 16px outer margins. Data tables shift to vertically stacked card groups.

### Spatial Rhythm
- Dynamic components rely on `space-xs` (4px) and `space-sm` (8px) for micro-gap relationships between labels, counts, and status indicators.
- Interior card padding standardizes on `space-lg` (24px) for desktop data surfaces, dropping to `space-md` (16px) on mobile viewports.

## Elevation & Depth

Visual hierarchy is communicated through luminous layering and hairline structural contours rather than heavy drop shadows. The design emphasizes crisp, planar depth.

### Surface Stratification
- **Floor (Canvas):** Set at `#F8F9FA`. Recedes beneath cards to establish a soft, non-glare workspace.
- **Level 1 (Cards & Data Blocks):** Pure white (`#FFFFFF`) with a 1px solid border (`#E5E7EB` or `#F1F5F9`) and a soft ambient micro-shadow: `0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.02)`.
- **Level 2 (Active States, Flyouts & Modals):** Pure white (`#FFFFFF`) with a 1px border (`#E2E8F0`) elevated by a focused perimeter shadow: `0 10px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.03)`.
- **Specialty Focus Surface (The Kinetic Highlight):** Featured KPI modules (such as top-performing stock items or master turnover rate) utilize solid `#84CC16` fills with slate-tinted interior text and borderless depth.

## Shapes

The geometric personality features generous, rounded radiuses inspired by modern fintech card surfaces and pill-shaped interactive triggers. This softens the visual density of complex inventory data sets.

### Roundness Distribution
- **Cards & Primary Modules (`rounded-xl` / 16px):** All major metric containers, tables, and modal dialogs maintain consistent 16px corner geometry.
- **Interactive Form Inputs & Buttons (`rounded-lg` / 10px - 12px):** Data inputs, search fields, and secondary triggers use an intermediate radius providing clear affordance.
- **Pills & Status Micro-Badges (`rounded-full` / 9999px):** Category chips, inventory condition counters, delta indicators, and status tags are completely rounded into pill formations.

## Components

### Buttons
- **Primary Kinetic:** Solid `#84CC16` background, `#0F172A` high-contrast typography, semibold weight. Borderless, with an interactive hover transition darkening to `#65A30D`.
- **Secondary Neutral:** Pure white card surface, `#0F172A` text, 1px border (`#E5E7EB`). Subtle lift on hover with background transition to `#F8F9FA`.
- **Destructive Action:** Low-saturation light red tint (`#FEF2F2`) with `#EF4444` label text, switching to solid `#EF4444` with white text on explicit active confirmation.

### Data Cards & Metric Panels
- Constructed with `#FFFFFF` background, 1px hairline border in `#E5E7EB`, and `rounded-xl` (16px) corners.
- Internal layout features a top metric label (`label-md` in `#64748B`), an oversized numerical total (`display-lg` in `#0F172A`), and an inline footer housing a pill delta badge (+12.4% in lime-tinted container `#ECFCCB` with `#3F6212` text).

### Chips, Pills & Tags
- **Positive / In Stock:** Pill radius, `#ECFCCB` background, `#3F6212` text, accompanied by an optional 6px solid green status dot.
- **Low Stock Warning:** Pill radius, `#FEF3C7` background, `#92400E` text.
- **Stockout / Critical:** Pill radius, `#FEE2E2` background, `#991B1B` text.
- **Category Filter Pills:** Interactive toggles; inactive states use `#F1F5F9` with `#475569` text, while active states switch to solid `#0F172A` with `#FFFFFF` text.

### Inputs & Search Bars
- Background set to `#FFFFFF` or `#F8F9FA`. Border is 1px `#E2E8F0`, transitioning smoothly to `#84CC16` on focus with an additional subtle 3px outer glow in `rgba(132, 204, 22, 0.15)`.
- Integrated search bars contain crisp, minimal monochrome line icons positioned at `16px` inner inset.

### Data Tables
- Flush borders with horizontal divider lines (`#F1F5F9`). Header cells apply `label-sm` uppercase styling in `#64748B` with solid background `#FAFAFA`.
- Alternating row hover states highlight gently with `#F8F9FA`.
- All inventory counts and monetary valuations are right-aligned using tabular figures to maintain uniform visual alignment.