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

### Force Refresh
By default, the server caches exported ZIPs in `~/.appian-sail-cache/` to avoid re-exporting on every load. To force a fresh export from your live Appian environment (e.g., after deploying new changes):
```
Load application with UUID _a-xxxx-yyyy, name SourceSelection, and force_refresh=true
```
This clears the cached ZIP for that app and re-exports from the live environment.

### Caching
- Exported ZIPs are cached at `~/.appian-sail-cache/`
- On startup, the server auto-loads any cached ZIPs matching your configured app
- Delete files from this folder to manually clear the cache
- Use `force_refresh=true` on `load_application` to clear and re-export programmatically

## MCP Server Tools

The `appian-sail-source` MCP server provides:

- `load_application` — Export and load an Appian app by UUID, or load from a local ZIP
- `list_objects` — List all loaded design objects, filter by type or name
- `get_sail_code` — Get the full SAIL definition of any interface or expression rule
- `search_objects` — Search objects by name, description, or code content
- `get_interfaces_using_component` — Find all interfaces using a specific SAIL component
- `get_a11y_checklist` — Fetch the latest accessibility checklist from the Aurora Design System

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

## Checklist Source

The power fetches the latest accessibility checklist directly from the **Aurora Design System** at audit time:
https://appian-design.github.io/aurora/accessibility/checklist/

This is the authoritative checklist maintained by the Appian Accessibility team. When the a11y team updates the checklist, the power automatically picks up the changes — no code changes needed.

A static fallback (`steering/a11y-sail-rules.md`) is used only if the Aurora page can't be reached.

Use the `get_a11y_checklist` MCP tool to fetch the latest checklist on demand.

## Parsed vs Skipped Object Types

The MCP server parses Appian export ZIPs and extracts SAIL definitions from XML files. Not all object types in an Appian application are relevant for SAIL auditing.

### Parsed (extracted and available for auditing)
| Object Type | Export Folder |
|-------------|---------------|
| Interfaces | `content/` |
| Expression Rules | `content/` |
| Constants | `content/` |
| Decisions | `content/` |
| Integrations | `content/` |
| Process Models | `processModel/` |
| Record Types | `recordType/` |
| Web APIs | `webApi/` |
| Connected Systems | `connectedSystem/` |
| Data Stores | `dataStore/` |
| Sites | `site/` |

### Skipped (not relevant for SAIL auditing)
| Object Type | Reason |
|-------------|--------|
| CDTs (Data Types) | `.xsd` files, not XML with SAIL definitions |
| Groups | Structural/permissions only |
| Folders | Structural only |
| Documents | Binary files (images, PDFs, etc.) |
| AI Skills / AI Agents | Not SAIL-based |
| Application Metadata | App-level config, not auditable |

> This means the loaded object count will be lower than what Appian Designer shows, since Designer counts all object types including groups, folders, documents, and CDTs.

## Rule Categories

The power checks against these rule categories (sourced from Aurora):
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
