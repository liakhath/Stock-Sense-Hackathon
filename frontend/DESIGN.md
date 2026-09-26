---
name: Luminescent Kinetic Inventory
colors:
  surface: '#000000'
  surface-dim: '#111111'
  surface-bright: '#2a2a2a'
  surface-container-lowest: '#111111'
  surface-container-low: '#171717'
  surface-container: '#202020'
  surface-container-high: '#252525'
  surface-container-highest: '#2a2a2a'
  on-surface: '#ffffff'
  on-surface-variant: '#b0b0b0'
  inverse-surface: '#111111'
  inverse-on-surface: '#ffffff'
  outline: '#999999'
  outline-variant: '#2a2a2a'
  surface-tint: '#a84691'
  primary: '#a84691'
  on-primary: '#ffffff'
  primary-container: '#a84691'
  on-primary-container: '#ffffff'
  inverse-primary: '#a84691'
  secondary: '#999999'
  on-secondary: '#ffffff'
  secondary-container: '#262626'
  on-secondary-container: '#b0b0b0'
  tertiary: '#855300'
  on-tertiary: '#ffffff'
  tertiary-container: '#fea518'
  on-tertiary-container: '#684000'
  error: '#ff6b6b'
  on-error: '#ffffff'
  error-container: '#351717'
  on-error-container: '#ffb3ae'
  primary-fixed: '#a84691'
  primary-fixed-dim: '#a84691'
  on-primary-fixed: '#ffffff'
  on-primary-fixed-variant: '#ffffff'
  secondary-fixed: '#262626'
  secondary-fixed-dim: '#333333'
  on-secondary-fixed: '#ffffff'
  on-secondary-fixed-variant: '#b0b0b0'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#000000'
  on-background: '#ffffff'
  surface-variant: '#202020'
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

This design system establishes a high-precision, dark visual architecture for inventory operations and stock intelligence. Black surfaces and restrained magenta accents keep the interface focused while preserving rapid operational scanning.

### Personality & Emotional Tenor
- **Surgical Precision:** Every data point, threshold indicator, and count is legible within milliseconds without perceptual clutter.
- **Controlled Vitality:** A restrained magenta accent marks primary actions and active states against a predominantly black canvas.
- **Tactile Softness:** Substantial corner radiuses and micro-shadowed planes balance industrial density with approachable, modern software luxury.

### Stylistic Philosophy
The interface operates within an ultra-refined, high-clarity dark framework:
- **Base Canvas:** Black backgrounds and near-black surfaces provide depth without decorative panels.
- **Hairline Precision:** Surfaces use subtle charcoal borders rather than heavy visual separation.
- **Targeted Chromatic Accents:** Magenta is restricted to primary interactions and active operational states. Amber and red remain reserved for warnings and errors.

## Colors

The palette establishes a dark, low-distraction canvas calibrated for extended operational shifts and immediate status comprehension.

### Functional Roles

- **Primary (`#A84691` - Brand Magenta):** Reserved for high-priority interactive paths, active tabs, positive highlights, and critical batch triggers. Text and icons on solid magenta are white.
- **Secondary (`#999999` - Neutral Gray):** Used for secondary icons, muted UI elements, and non-active controls.
- **Tertiary (`#F59E0B` - Warm Amber):** Dedicated warning indicator for low-stock thresholds, impending reorder deadlines, and transitional synchronization states.
- **Hazard Coral (`#EF4444`):** Strictly reserved for stockouts, negative delta trajectories, batch errors, and destructive operations.
- **Neutral Canvas (`#000000` to `#2A2A2A`):** Layered dark surfaces and subtle borders provide structure beneath white and gray typography.

### Foreground Hierarchy
- **High Emphasis (`#FFFFFF`):** Primary metrics, SKU identifiers, column headers, and active state copy.
- **Medium Emphasis (`#B0B0B0`):** Supporting metadata, unit indicators, table secondary keys, and placeholder states.
- **Subtle Emphasis (`#999999` / `#2A2A2A`):** Secondary icons, disabled states, structural hairline rules, and table gridlines.

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
- **Floor (Canvas):** Set at `#000000`, with the deepest surface receding behind data panels.
- **Level 1 (Cards & Data Blocks):** Near-black (`#111111`) with a 1px charcoal border (`#2A2A2A`) and restrained shadow.
- **Level 2 (Active States, Flyouts & Modals):** Dark layered surfaces from `#171717` to `#252525` with a 1px `#2A2A2A` border.
- **Specialty Focus Surface (The Brand Highlight):** Featured KPI modules use solid `#A84691` fills with white text and icons.

## Shapes

The geometric personality features generous, rounded radiuses inspired by modern fintech card surfaces and pill-shaped interactive triggers. This softens the visual density of complex inventory data sets.

### Roundness Distribution
- **Cards & Primary Modules (`rounded-xl` / 16px):** All major metric containers, tables, and modal dialogs maintain consistent 16px corner geometry.
- **Interactive Form Inputs & Buttons (`rounded-lg` / 10px - 12px):** Data inputs, search fields, and secondary triggers use an intermediate radius providing clear affordance.
- **Pills & Status Micro-Badges (`rounded-full` / 9999px):** Category chips, inventory condition counters, delta indicators, and status tags are completely rounded into pill formations.

## Components

### Buttons
- **Primary Action:** Solid `#A84691` background with `#FFFFFF` text and icons, semibold weight.
- **Secondary Neutral:** Dark outlined surface, `#B0B0B0` text, and a 1px `#2A2A2A` border.
- **Destructive Action:** Dark red-tinted surface with readable red text, retaining red for explicit errors and destructive actions.

### Data Cards & Metric Panels
- Constructed with `#111111` background, 1px hairline border in `#2A2A2A`, and `rounded-xl` (16px) corners.
- Internal layout features a top metric label (`label-md` in `#B0B0B0`), an oversized numerical total (`display-lg` in `#FFFFFF`), and an inline footer using restrained magenta highlights.

### Chips, Pills & Tags
- **Positive / In Stock:** Pill radius, dark magenta-tinted background, white text, with magenta reserved for brand indicators.
- **Low Stock Warning:** Pill radius, dark amber-tinted background, readable amber text.
- **Stockout / Critical:** Pill radius, dark red-tinted background, readable red text.
- **Category Filter Pills:** Interactive toggles; inactive states use dark gray surfaces with `#B0B0B0` text, while active states use `#A84691` with white text.

### Inputs & Search Bars
- Background set to `#171717` or `#202020`. Border is 1px `#2A2A2A`, transitioning to `#A84691` on focus with a subtle outer glow in `rgba(168, 70, 145, 0.15)`.
- Integrated search bars contain crisp, minimal monochrome line icons positioned at `16px` inner inset.

### Data Tables
- Flush borders with horizontal divider lines (`#2A2A2A`). Header cells apply `label-sm` uppercase styling in `#B0B0B0` against dark surfaces.
- Alternating row hover states highlight gently with layered charcoal surfaces.
- All inventory counts and monetary valuations are right-aligned using tabular figures to maintain uniform visual alignment.