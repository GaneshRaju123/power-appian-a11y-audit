# Appian SAIL Source MCP Server

Connects directly to your Appian environment to pull SAIL code for accessibility auditing.

## How It Works

```
Appian Environment
    ↓ (Deployment REST API v2 — export application as ZIP)
This MCP Server
    ↓ (parses XML files inside ZIP → extracts SAIL definitions)
Kiro IDE
    ↓ (applies a11y rules from steering files)
Audit Report
```

## Two Modes

### Mode 1: Live Export (connects to Appian)
The server calls Appian's Deployment REST API to export your application as a ZIP, then parses the XML files inside to extract SAIL definitions.

Requirements:
- Appian API key with deployment permissions
- Network access to your Appian environment

### Mode 2: Offline / Pre-exported ZIP
Export your application from Appian Designer manually, then point the server at the ZIP file. No network access needed.

## Setup

### Install dependencies
```bash
pip install -r requirements.txt
```

### Configure in Kiro
Add to your `~/.kiro/settings/mcp.json`:

#### For live Appian connection:
```json
{
  "mcpServers": {
    "appian-sail-source": {
      "command": "python3",
      "args": ["/path/to/power-appian-a11y-audit/mcp-server/server.py"],
      "env": {
        "APPIAN_URL": "https://yoursite.appiancloud.com",
        "APPIAN_API_KEY": "your-api-key-here",
        "APPIAN_APP_UUID": "your-app-uuid-here",
        "APPIAN_APP_NAME": "SourceSelection"
      }
    }
  }
}
```

#### For offline / pre-exported ZIP:
```json
{
  "mcpServers": {
    "appian-sail-source": {
      "command": "python3",
      "args": ["/path/to/power-appian-a11y-audit/mcp-server/server.py"],
      "env": {
        "APPIAN_LOCAL_ZIP": "/path/to/SourceSelection-export.zip",
        "APPIAN_APP_NAME": "SourceSelection"
      }
    }
  }
}
```

## Getting Your Application UUID

1. Open Appian Designer
2. Go to your application (e.g., SourceSelection)
3. Click the application name → Properties
4. The UUID is shown in the properties panel

## Getting an API Key

1. Go to Appian Admin Console
2. Navigate to API Keys
3. Create a new key with deployment permissions
4. Copy the key value

## Caching

Exported ZIPs are cached in `~/.appian-sail-cache/` so repeated queries don't re-export. Delete files from this folder to force a fresh export.

## Tools Provided

| Tool | Description |
|------|-------------|
| `load_application` | Export and load an app by UUID, or load from local ZIP |
| `list_objects` | List all loaded objects, filter by type or name |
| `get_sail_code` | Get full SAIL definition of any object |
| `search_objects` | Search by name, description, or code content |
| `get_interfaces_using_component` | Find interfaces using a specific SAIL component |
| `get_a11y_checklist` | Fetch the latest a11y checklist from Aurora Design System |
