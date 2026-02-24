# Appian A11y SAIL Rules (Fallback)

> **SOURCE OF TRUTH:** The authoritative checklist is maintained by the Appian Accessibility team in the Aurora Design System:
> https://appian-design.github.io/aurora/accessibility/checklist/
>
> **Always call the `get_a11y_checklist` MCP tool first** to fetch the latest version.
> This file is a fallback only — used when the Aurora checklist cannot be fetched (e.g., network issues).

Complete Solutions A11y Checklist rules for automated SAIL analysis.

## SAIL-Testable Rules

### Form Inputs
- RULE-FI-01: Every enabled/disabled input MUST have `label` parameter set (not null). Applies to: a!textField, a!paragraphField, a!integerField, a!floatingPointField, a!dropdownField, a!multipleDropdownField, a!dateField, a!dateTimeField, a!pickerField, a!userPickerField, a!groupPickerField
- RULE-FI-02: Each checkbox/radio MUST have `choiceLabels` set (not null). Applies to: a!checkboxField, a!radioButtonField
- RULE-FI-03: Checkbox/radio with multiple options MUST have `label` set. Applies to: a!checkboxField, a!radioButtonField
- RULE-FI-04: Text fields for personal info MUST have `inputPurpose` set. Applies to: a!textField
- RULE-FI-05: Duplicated controls with same name MUST have `accessibilityText` or be in labeled section/box layout

### Validations
- RULE-VA-01: Required inputs MUST have `required: true`
- RULE-VA-02: Use OOTB validation: `validations`, `validationGroup`, `validationMessage` parameters

### Instructions
- RULE-IN-01: Visible form instructions MUST use `instructions` parameter on the input

### Grids
- RULE-GR-01: Every grid MUST have `label` set. Applies to: a!gridField, a!gridLayout
- RULE-GR-02: Each data/input column MUST have `label` on a!gridColumn or a!gridLayoutHeaderCell
- RULE-GR-03: Set `rowHeader` when a cell uniquely identifies the row
- RULE-GR-04: Empty grid columns MUST NOT be used for spacing
- RULE-GR-05: Grid instructions MUST use `instructions` parameter (not external text). Do not use "grid" in text, use "table"
- RULE-GR-06: Selectable grids MUST have `accessibilityText` warning about controls above grid. Do not use "grid", use "table"

### Headings
- RULE-HD-01: Text headings MUST use `a!headingField` or layout with `labelHeadingTag`
- RULE-HD-02: Heading levels must be appropriate via `headingTag` or `labelHeadingTag`. Do not skip levels.

### Lists
- RULE-LI-01: Visual lists MUST use `a!richTextBulletedList` or `a!richTextNumberedList`

### Pane Layout
- RULE-PL-01: Each `a!pane` MUST have `accessibilityText`. Do not use: pane, main, navigation, section, form, search, header, footer, article, region

### Section/Box Layout
- RULE-SB-01: Expandable `a!sectionLayout` MUST have `label` AND `labelHeadingTag`
- RULE-SB-02: Expandable `a!boxLayout` MUST have `label` AND `labelHeadingTag`

### Cards
- RULE-CA-01: Cards with `link` parameter MUST NOT contain other controls/inputs inside
- RULE-CA-02: Cards with `link` MUST NOT have `label` on the link
- RULE-CA-03: Selected cards MUST have `accessibilityText: "Selected"` (removed when deselected)

### Links
- RULE-LK-01: Rich text links MUST use `linkStyle: "INLINE"` or other differentiation
- RULE-LK-02: Selected rich text links: use icon `altText: "Selected"` (prefer over accessibilityText on richTextDisplayField)

### Breadcrumbs
- RULE-BC-01: Breadcrumbs MUST have `accessibilityText` identifying breadcrumb and current page. Example: "Breadcrumbs, corporate is the current page"

### Icons
- RULE-IC-01: Standalone icon in link MUST have `altText` or `caption` (prefer altText)
- RULE-IC-02: Icon with text in link: `altText` only if link text doesn't convey same info
- RULE-IC-03: Standalone icon in button MUST have `accessibilityText` or `tooltip` on button
- RULE-IC-04: Icon with text in button: `accessibilityText` only if button label doesn't convey icon info
- RULE-IC-05: Standalone icon conveying info MUST have `altText` or `caption`
- RULE-IC-06: Decorative/redundant icons MUST NOT have `altText` or `caption`

### Charts
- RULE-CH-01: Charts MUST have `label` parameter set

### Progress Bar
- RULE-PB-01: `a!progressBarField` MUST have `label`

### File Upload
- RULE-FU-01: `a!fileUploadField` MUST have `label`
- RULE-FU-02: `a!fileUploadField` MUST have `instructions`

### Stamp
- RULE-ST-01: `a!stampField` MUST NOT use `tooltip` or `helpTooltip` for important info

### Date & Time
- RULE-DT-01: `a!dateTimeField` MUST NOT be used

### Card Choice / Card Group
- RULE-CC-01: `a!cardChoiceField` with multiple cards MUST have `label`
- RULE-CG-01: `a!cardGroupLayout` with multiple cards MUST have `label`

### Custom Pagination
- RULE-CP-01: Inactive pagination links MUST NOT have accessibilityText indicating "disabled"
- RULE-CP-02: Adjacent active pagination links MUST have 24x24px target size or non-overlapping circles

### Dynamic Content
- RULE-DC-01: Dynamic status messages MUST use `a!messageBanner` with `announceBehavior`

### Simulated Grid
- RULE-SG-01: Data visually output as grid but not using grid MUST have `accessibilityText` on each cell with column header and row header text

### Modal Dialog
- RULE-MD-01: Focus MUST NOT move to input when important info precedes it. Set `focusOnFirstInput: false`

### Forms
- RULE-FM-01: Focus MUST NOT move to input when important info precedes it. Set `focusOnFirstInput: false`
- RULE-FM-02: Info user must re-enter MUST be auto-populated or available to select

## Visual/Manual Rules (Flag When Components Detected)

- RULE-VM-01: Placeholder text alone MUST NOT convey important info
- RULE-VM-02: Every input MUST have persistently visible label (flag when labelPosition: COLLAPSED)
- RULE-VM-03: Required fields MUST have asterisk legend at form start
- RULE-VM-04: Focus MUST NOT move past important info on form/dialog init
- RULE-VM-05: Color MUST NOT be only means of identification
- RULE-VM-06: Text contrast: 4.5:1 regular, 3:1 large (18pt or 14pt bold)
- RULE-VM-07: Icon/image contrast: 3:1
- RULE-VM-08: Content readable at 200% zoom (CTRL+"+", 5 times) and 400% zoom (8 times) at 1280px width
- RULE-VM-09: Touch targets: 24x24px minimum or non-overlapping 24px circles
- RULE-VM-10: Signature component MUST have keyboard alternative
- RULE-VM-11: Tooltips MUST be keyboard accessible
- RULE-VM-12: Images of text MUST NOT be used (except logos)
- RULE-VM-13: Validation error messages MUST include input name
- RULE-VM-14: Grid row drag-and-drop MUST have single-click alternative (up/down links)
- RULE-VM-15: Workflow Visualization plugin MUST have alternative view
