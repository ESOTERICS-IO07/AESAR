---
name: Arachnid Technical Interface
colors:
  surface: '#f9f9ff'
  surface-dim: '#d9d9e1'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fa'
  surface-container: '#ededf5'
  surface-container-high: '#e8e7ef'
  surface-container-highest: '#e2e2e9'
  on-surface: '#1a1b21'
  on-surface-variant: '#45464f'
  inverse-surface: '#2e3036'
  inverse-on-surface: '#f0f0f7'
  outline: '#757680'
  outline-variant: '#c5c6d0'
  surface-tint: '#4c5d8e'
  primary: '#000928'
  on-primary: '#ffffff'
  primary-container: '#0b1f4d'
  on-primary-container: '#7788bc'
  inverse-primary: '#b4c5fd'
  secondary: '#395aac'
  on-secondary: '#ffffff'
  secondary-container: '#89a8ff'
  on-secondary-container: '#113a8b'
  tertiary: '#1b0600'
  on-tertiary: '#ffffff'
  tertiary-container: '#3e1600'
  on-tertiary-container: '#ba7a58'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5fd'
  on-primary-fixed: '#031846'
  on-primary-fixed-variant: '#344574'
  secondary-fixed: '#dae2ff'
  secondary-fixed-dim: '#b2c5ff'
  on-secondary-fixed: '#001848'
  on-secondary-fixed-variant: '#1c4293'
  tertiary-fixed: '#ffdbcb'
  tertiary-fixed-dim: '#ffb690'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#6c391d'
  background: '#f9f9ff'
  on-background: '#1a1b21'
  surface-variant: '#e2e2e9'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  data-mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 16px
  margin: 24px
  max_width: 1440px
---

## Brand & Style

The design system is a high-precision, premium framework tailored for advanced robotics and autonomous systems. It prioritizes clarity, technical authority, and a "white-first" aesthetic to ensure operators can process complex telemetry without cognitive fatigue.

The style is **Professional Minimalism** with **Technical Brutalist** accents. It leverages expansive white space (70-80% of the UI) to signify a clean, controlled laboratory environment. Visual interest is driven by high-precision geometry, thin 1px lines, and atmospheric mists that bridge the gap between hardware engineering and software elegance. The emotional response is one of calm reliability, surgical precision, and cutting-edge sophistication.

## Colors

The palette is anchored in **Deep Spider Blue**, used primarily for structural navigation and high-level headers to provide a sense of stability. **Spider Red** is reserved strictly for high-priority signals: active missions, target acquisition, and emergency overrides.

- **Primary Canvas:** Utilize `#FFFFFF` for almost all surfaces. Use `#F7F8FA` sparingly to differentiate nested panels or technical sidebars.
- **Accents:** Use `Soft Red` and `Soft Blue` as low-contrast background fills for status badges or selected states to maintain a clean aesthetic while providing clear affordance.
- **Atmospheric Gradients:** For header backgrounds, implement a subtle radial gradient transition from Deep Spider Blue to a soft mist effect, or a sharp linear transition to Spider Red for "Active Alert" modes.

## Typography

This design system uses a dual-font strategy to separate intent. 

- **Inter** is the primary interface font, used for all instructional text, navigation, and general UI labels. It ensures maximum readability and a modern, approachable feel.
- **JetBrains Mono** is utilized for the "Technical Layer." Any value derived from hardware—GPS coordinates, LIDAR distances, battery percentages, or system logs—must be set in JetBrains Mono. This creates a clear visual distinction between "Software UI" and "Machine Logic."

For mobile devices, reduce `display-lg` to 32px and `headline-md` to 20px. Data-heavy tables should always use `data-mono-sm` for density and alignment.

## Layout & Spacing

The layout follows a **Rigid Technical Grid**. It uses a 4px baseline unit to ensure all elements align with mathematical precision. 

- **Grid:** Use a 12-column fluid grid for main dashboards. On mobile, transition to a single-column stack with 16px margins.
- **Eight-Directional Geometry:** UI containers and background patterns should reference octagonal/radial symmetry. For example, decorative corner markers or "spider-web" line patterns should use 45-degree angles.
- **Density:** Maintain high information density in sidebars (using 8px spacing) while allowing the central viewing area (map or camera feed) to have large 40px+ breathing room.

## Elevation & Depth

Elevation is primarily communicated through **Thin Borders** and **Tonal Layering** rather than heavy shadows.

- **Surface Tiers:** The main background is Level 0 (#FFFFFF). Floating panels or toolbars are Level 1 (#FFFFFF with a 1px #E4E7EC border and a very subtle 4px blur shadow).
- **Interactive Depth:** When a card or element is hovered, do not move it physically; instead, change the border color to `Primary Blue` or apply a subtle 1px "inner-glow" using `Soft Blue`.
- **Atmospheric Depth:** Use semi-transparent overlays (80% opacity) for modal backdrops to maintain visibility of underlying telemetry data. Background blurs should be kept to a minimum (4-8px) to preserve technical sharpness.

## Shapes

The shape language is **Technical and Crisp**. 

- **Corner Radius:** Elements use a default `0.25rem` (4px) radius. This provides a "softened-industrial" look—precise enough for a machine, but refined enough for a premium product.
- **Octagonal Truncation:** For primary action buttons or high-level status indicators, consider using 45-degree chamfered corners (clipped corners) instead of standard rounding to reinforce the arachnid/geometric theme.
- **Lines:** Dividers and borders must be strictly 1px. Avoid 2px+ borders except for the E-STOP button.

## Components

### Buttons
- **Primary:** Deep Spider Blue background, white text. Rectangular with 4px radius.
- **Secondary:** White background, 1px Border (#E4E7EC), Text Primary.
- **E-STOP:** High-visibility Spider Red (#D71920). Large, 2px border, bold white text. This button is the only element allowed to break the minimal aesthetic for safety.

### Technical Cards
- White background, 1px border. No shadow or very faint 2px ambient shadow.
- Headers should include a small "data-label" in JetBrains Mono at the top right (e.g., "SENS-04").

### Status Indicators
- **Connected:** Soft Blue background, Primary Blue text, small pulsing blue dot.
- **Autonomous/Active:** Soft Red background, Spider Red text, small solid red dot.
- All indicators use `label-caps` typography.

### Input Fields
- Subtle #F7F8FA background with a bottom-only 1px border that turns Primary Blue on focus. Labels should be placed above in `data-mono-sm`.

### Mapping & Occupancy Grids
- The "Occupancy Grid" should use a monochromatic scale (White for clear, #E4E7EC for unknown, #111318 for obstacles). 
- Use 45-degree hatching patterns to indicate restricted zones.