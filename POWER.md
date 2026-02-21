# Appian A11y Audit Power

Accessibility audit assistant for Appian low-code developers. Catches a11y issues at two stages — mockup screenshots and SAIL code — before they become bugs.

**This power includes its own MCP server** that connects directly to your Appian environment to pull SAIL code.

## What This Power Does

- Pulls SAIL code directly from your Appian environment (via Deployment API export)
- Analyzes feature mockup screenshots for visual accessibility issues
- Audits SAIL code against the complete Solutions A11y Checklist (50+ rules)
- Cross-references historical Jira bugs for repeat patterns (supports any Jira project — GAM, CMS, etc.)
- Generates categorized audit reports (must-fix, verify, watch-out)
- Finds all interfaces using a specific component (e.g., all grids, all file uploads)

## Setup

### Option A: Live connection to Appian (recommended)
Set these environment variables in the MCP server config:
- `APPIAN_URL` — Your Appian site URL (e.g., `https://mysite.appiancloud.com`)
- `APPIAN_API_KEY` — API key with deployment permissions
- `APPIAN_APP_UUID` — UUID of your application (e.g., SourceSelection)

### Option B: Pre-exported ZIP (offline)
1. Export your application from Appian Designer (Build > Export)
2. Save the ZIP file somewhere on your machine
3. Set `APPIAN_LOCAL_ZIP` to the path of the ZIP file
4. Set `APPIAN_APP_NAME` to a short recognizable name (e.g., "SourceSelection")

> **APPIAN_APP_NAME** is a friendly label — it doesn't need to match the Appian application name. Use whatever short name your team recognizes. It tags objects in tool output.

### Option C: Paste SAIL directly
No setup needed — just paste SAIL code into Kiro chat.

### Loading Multiple Applications
The env vars configure one default app that auto-loads on startup. To work with additional apps in the same session, load them from chat:
```
Load application with UUID _a-xxxx-yyyy and name CaseManagement
```
Or from a ZIP:
```
Load application from ~/exports/CaseManagement.zip with name CaseManagement
```
All loaded objects stay in memory. You can search and audit across all loaded apps.

## MCP Server Tools

The `appian-sail-source` MCP server provides:

- `load_application` — Export and load an Appian app by UUID, or load from a local ZIP
- `list_objects` — List all loaded design objects, filter by type or name
- `get_sail_code` — Get the full SAIL definition of any interface or expression rule
- `search_objects` — Search objects by name, description, or code content
- `get_interfaces_using_component` — Find all interfaces using a specific SAIL component

## How to Use

### Audit a mockup screenshot
Drag a screenshot into Kiro chat and say:
```
Run an a11y audit on this mockup
```

### Audit SAIL code from your Appian environment
```
Load SourceSelection and run an a11y audit on AS_GSS_FM_addVendors
```

### Audit from a pre-exported ZIP
```
Load the application from ~/exports/SourceSelection.zip and audit all interfaces
```

### Audit pasted SAIL code
Paste SAIL code into chat and say:
```
Check this SAIL for accessibility issues
```

### Find all interfaces using a specific component
```
Find all interfaces using a!gridField in SourceSelection
```

### Full audit (code + Jira)
```
Full a11y audit for SourceSelection. Check Jira for past a11y bugs too.
```

## Rule Categories

The power checks against these rule categories:
- Form Inputs (labels, choiceLabels, inputPurpose)
- Validations (required, validation messages)
- Grids (label, rowHeader, column headers, accessibilityText)
- Headings (semantic headings, heading hierarchy)
- Cards (link conflicts, selection state)
- Icons (altText, caption for standalone/decorative)
- Links (differentiation, selection state)
- File Upload (label, instructions)
- Charts (label, data table alternative)
- Color Contrast (text, icons, selected state)
- Touch Targets (24x24px minimum)
- Dynamic Content (messageBanner, announceBehavior)

## Report Structure

Every audit generates:
1. **Automated SAIL Findings** — issues found by inspecting code parameters
2. **Manual Checks Required** — things that need visual/keyboard testing
3. **Historical Bug Patterns** — past Jira bugs on similar components
4. **Component A11y Summary** — all rules per component type
