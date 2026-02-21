# ♿ Appian A11y Audit Power

Accessibility audit assistant for Appian SAIL interfaces. Catches a11y issues at two stages — **mockup screenshots** and **SAIL code** — before they become bugs.

---

## What This Power Does

| Feature | Description |
|---------|-------------|
| 🔍 SAIL Code Auditing | Pulls SAIL directly from Appian, checks 50+ a11y rules |
| 🖼️ Mockup Analysis | Analyzes feature screenshots for visual a11y issues |
| 🐛 Jira Awareness | Cross-references historical GAM a11y bugs |
| 🧩 Component Search | Finds all interfaces using a specific SAIL component |
| 📄 Audit Reports | Generates categorized findings (must-fix, verify, watch-out) |

---

## Installation

1. In Kiro IDE, go to the **Powers** tab (puzzle icon in sidebar)
2. Click **Add Power**
3. Paste this URL:

```
https://github.com/GaneshRaju123/power-appian-a11y-audit
```

4. Wait for installation to complete

---

## Setup

After installing, click **Open Power Config** and fill in your env vars:

### Option A: Live Appian Connection

| Variable | Value |
|----------|-------|
| `APPIAN_URL` | `https://yoursite.appiancloud.com` |
| `APPIAN_API_KEY` | Your API key with deployment permissions |
| `APPIAN_APP_UUID` | Default app UUID *(optional)* |
| `APPIAN_APP_NAME` | e.g. `SourceSelection` |

> **Multi-app support:** The API key works across all apps on your site. Set a default UUID for convenience, or load any app on the fly from chat.

### Option B: Offline ZIP

| Variable | Value |
|----------|-------|
| `APPIAN_LOCAL_ZIP` | `/path/to/export.zip` |
| `APPIAN_APP_NAME` | e.g. `SourceSelection` |

### Option C: Paste SAIL Directly

No setup needed. Just paste SAIL code into Kiro chat.

After configuring, go to **MCP Servers** panel → find `appian-sail-source` → click **Reconnect**.

---

## Prerequisites

- **Python 3.10+** on your machine
- **Kiro IDE** installed
- Appian environment access (Options A/B only)

> Dependencies (`mcp`, `httpx`) auto-install in an isolated venv on first run. No manual pip install needed.

---

## Example Usage

**Audit a specific interface:**
```
Load SourceSelection and audit AS_GSS_FM_addVendors
```

**Switch between apps:**
```
Load CaseManagementStudio and audit AS_CMS_FM_createCase
```

**Paste SAIL directly:**
```
Check this SAIL for accessibility issues
```

**Audit a mockup screenshot:**
> Drag a screenshot into Kiro chat and say: `Run an a11y audit on this mockup`

**Find component usage:**
```
Find all interfaces using a!gridField in SourceSelection
```

**Full audit with Jira history:**
```
Full a11y audit for SourceSelection. Check Jira too.
```

> You can load multiple apps in the same session. All objects stay in memory.

---

## What Gets Checked

50+ rules from the Solutions A11y Checklist:

| Category | Key Rules |
|----------|-----------|
| Form Inputs | labels, choiceLabels, inputPurpose |
| Grids | label, rowHeader, column headers, accessibilityText |
| Headings | semantic headings, heading hierarchy |
| Cards | link conflicts, selection state |
| Icons | altText, caption for standalone/decorative |
| File Upload | label, instructions |
| Charts | label, data table alternative |
| Dynamic Content | messageBanner, announceBehavior |

---

## MCP Server Tools

| Tool | Description |
|------|-------------|
| `load_application` | Export and load an app by UUID or local ZIP |
| `list_objects` | List all loaded objects, filter by type/name |
| `get_sail_code` | Get full SAIL definition of any object |
| `search_objects` | Search by name, description, or code content |
| `get_interfaces_using_component` | Find interfaces using a specific component |

---

## Documentation

- 📖 [Detailed Installation Guide](POWER.md) — Full setup, usage workflows, and all rule categories
- 📋 [A11y Rules Reference](steering/a11y-sail-rules.md) — Complete 50+ rule checklist
- 🔄 [Audit Workflow](steering/a11y-audit-workflow.md) — How the audit process works

---

## License

MIT
