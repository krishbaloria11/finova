---
name: Finova Silk & Glass
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#434655'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#747686'
  outline-variant: '#c4c5d7'
  surface-tint: '#2151da'
  primary: '#0037b0'
  on-primary: '#ffffff'
  primary-container: '#1d4ed8'
  on-primary-container: '#cad3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#006c4a'
  on-secondary: '#ffffff'
  secondary-container: '#82f5c1'
  on-secondary-container: '#00714e'
  tertiary: '#6b3700'
  on-tertiary: '#ffffff'
  tertiary-container: '#8d4b00'
  on-tertiary-container: '#ffcba3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001551'
  on-primary-fixed-variant: '#0039b5'
  secondary-fixed: '#85f8c4'
  secondary-fixed-dim: '#68dba9'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#005137'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 38px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.005em
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  financial-numeric:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
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
  margin: 3rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system projects absolute financial poise, calm confidence, and understated luxury. Designed for high-end consumer banking and wealth management, the aesthetic fuses Scandinavian minimalism with tactile hardware-inspired glassmorphism, evoking the immaculate industrial finish of precision-milled glass and anodized ceramic.

### Core Attributes
- **Calm & Pristine:** High visual breathing room, light-first clarity, and unhurried visual pacing.
- **Tactile Refinement:** Semi-translucent layered glass planes, whisper-thin rim lighting, and atmospheric depth without chromatic noise.
- **Architectural Discipline:** Precise typographical scales, strict baseline rhythms, and intentional micro-interactions that reassure users with every interaction.

## Colors

The palette relies on light, airy foundations with hyper-restrained color interventions. Surfaces favor cool alabaster and silk-like frosted whites, anchoring visual tension strictly through precision typography and deliberate accent placement.

### Functional Roles
- **Canvas Base:** Soft Alabaster (`#F8FAFC`) grading seamlessly into muted slate undertones (`#F1F5F9`).
- **Glass Layers:** `rgba(255, 255, 255, 0.72)` to `rgba(255, 255, 255, 0.90)` backed by `backdrop-filter: blur(24px) saturate(180%)`.
- **Text & Hierarchy:** Deep Slate Charcoal (`#0F172A`) for headlines and numbers; Muted Steel (`#64748B`) for structural body and captions; Subtle Mist (`#94A3B8`) for secondary watermarks and disabled indicators.
- **Primary Brand Accent:** Royal Sapphire (`#1D4ED8`) reserved exclusively for primary transaction drivers, verified markers, and primary focus rings.
- **Financial Status Accents:** 
  - Inflow & Growth: Deep Pure Emerald (`#059669`)
  - Yield & Pending: Balanced Warm Amber (`#D97706`)
  - Outflow & Critical: Soft Crimson Slate (`#E11D48`)

## Typography

The typography hierarchy communicates high-end financial clarity through optical weight balance. Plus Jakarta Sans handles titles, display numbers, and expressive layout cues, while Inter provides structural, unambiguous legibility across micro-labels, tabular data, and input controls.

### Implementation Guidelines
- **Tabular Figures:** Always apply `font-feature-settings: "tnum" on, "cv05" on` to currency metrics, balances, and ledger tables.
- **Tight Headings:** High-scale display typography utilizes negative tracking to simulate high-precision editorial publishing.

## Layout & Spacing

The structural rhythm follows an 8pt architectural grid, paired with generous open fields to ensure visual weight never clusters uncomfortably around financial records.

### Breakpoints & Adaptive Layouts
- **Desktop (1280px+):** Max-width canvas capped at 1440px with a 12-column layout, 24px gutters, and 48px outer margins.
- **Tablet (768px – 1279px):** 8-column layout, 20px gutters, and 32px margins.
- **Mobile (< 768px):** 4-column layout, 16px gutters, and 20px edge margins. Stack grouped cards vertically with `space-md` gaps.

## Elevation & Depth

Depth is established strictly through translucent physical optical phenomena rather than heavy artificial shadows.

### Glass Surface Tokens
- **Surface Level 0 (Base Canvas):** Solid wash with subtle linear atmospheric gradient from `#F8FAFC` to `#F1F5F9`.
- **Surface Level 1 (Resting Cards):** `background: rgba(255, 255, 255, 0.75)`, `backdrop-filter: blur(20px) saturate(160%)`, bordered by `1px solid rgba(226, 232, 240, 0.8)`. Soft diffuse shadow: `0 8px 32px -4px rgba(15, 23, 42, 0.04), 0 2px 8px -2px rgba(15, 23, 42, 0.02)`.
- **Surface Level 2 (Floating Modals & Dropdowns):** `background: rgba(255, 255, 255, 0.88)`, `backdrop-filter: blur(32px)`, bordered by `1px solid rgba(255, 255, 255, 0.95)`. Shadow: `0 20px 48px -12px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.03)`.
- **Specular Top Highlight:** Elevated floating components feature an inner shadow rim: `inset 0 1px 1px 0 rgba(255, 255, 255, 0.9)`.

## Shapes

The interface adopts soft, continuous squircle-like curvatures, mirroring the physical contours of premium hardware.

### Radius Assignments
- **Micro (Inputs, Badges, Chips):** `0.5rem` (8px).
- **Default (Standard Cards, Panels):** `1rem` (16px).
- **Large (Hero Banners, Primary Modals):** `1.5rem` (24px).
- **Interactive Controls (Action Pills):** Fully circular pill boundaries (`9999px`) applied deliberately to quick actions and floating action controls.

## Components

### Buttons
- **Primary:** Deep Sapphire (`#1D4ED8`) solid base, crisp pure-white text (`#FFFFFF`), with an imperceptible inset top border `inset 0 1px 0 rgba(255, 255, 255, 0.2)`. Hover shifts to `#1E40AF` with smooth 150ms cubic easing.
- **Glass / Secondary:** `rgba(255, 255, 255, 0.65)` fill with `1px solid rgba(226, 232, 240, 0.9)`. Charcoal text (`#0F172A`). Hover state elevates surface opacity to `0.9` and introduces a subtle `-1px` transform.

### Cards & Ledger Tiles
- Framed in frosted glass (`Level 1`). Inner content follows a minimum padding of `space-lg` (24px). Dividers between items utilize hairline strokes (`1px solid rgba(226, 232, 240, 0.5)`).

### Input Fields
- Structured at a height of 48px. Background is `rgba(255, 255, 255, 0.6)` with a `1px solid rgba(203, 213, 225, 0.6)` frame.
- **Focus State:** `background: rgba(255, 255, 255, 0.95)`, ring transition with `0 0 0 3px rgba(29, 78, 216, 0.12)`, and border color snapping to `#1D4ED8`.

### Chips & Metrics Badges
- Compact pill silhouettes with `space-xs` vertical and `space-sm` horizontal padding. Status indicators combine a soft tint background (e.g., emerald at 8% opacity: `rgba(5, 150, 105, 0.08)`) with high-contrast text (`#059669`).

### Checkboxes & Segmented Controls
- Segmented switches nest inside an inset glass track (`rgba(226, 232, 240, 0.4)`), while the active pill indicator transitions smoothly on a raised white glass tile with a subtle micro-shadow.