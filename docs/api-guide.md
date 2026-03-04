# API Developer Guide

This guide explains how to use the data from the APK Store project as a simple REST API. Since the store is hosted on GitHub Pages, the "API" consists of static JSON files and the GitHub Releases API.

## Base URLs

- **Metadata API**: `https://cfopuser.github.io/app-store/`
- **Releases API**: `https://api.github.com/repos/cfopuser/app-store/releases`

---

## 1. App Discovery

To get a list of all available apps, fetch the `apps.json` file from the root.

**Endpoint:** `GET /apps.json`

**Response:**
```json
[
  "bit",
  "whatsapp",
  "spotify",
  ...
]
```

---

## 2. App Metadata & Status

Each app has its own configuration and status files located in its subfolder under `apps/`.

### App Configuration
Contains name, description, icon, and other metadata.

**Endpoint:** `GET /apps/{app_id}/app.json`

**Example (`/apps/whatsapp/app.json`):**
```json
{
  "id": "whatsapp",
  "name": "WhatsApp",
  "package_name": "com.whatsapp",
  "description": "WhatsApp with kosher patch applied.",
  "icon_url": "https://...",
  "maintainer": "lilor159357"
}
```

### App Status
Contains the result of the last build/patch pipeline.

**Endpoint:** `GET /apps/{app_id}/status.json`

**Example:**
```json
{
  "success": true,
  "updated_at": "Wed Mar 04 12:00:00 UTC 2026"
}
```

---

## 3. Getting Download Links

Downloads are managed via GitHub Releases. Each app update creates a release with a tag formatted as `{app_id}-v{version}`.

**Endpoint:** `GET https://api.github.com/repos/cfopuser/app-store/releases`

### How to filter for a specific app:
Iterate through the releases and find tags that start with your `app_id`.

**JavaScript Example:**
```javascript
const appId = 'whatsapp';
const response = await fetch('https://api.github.com/repos/cfopuser/app-store/releases');
const releases = await response.json();

const appReleases = releases.filter(r => 
    r.tag_name.startsWith(`${appId}-v`) && 
    r.assets.length > 0
);

if (appReleases.length > 0) {
    const latestRelease = appReleases[0];
    const downloadUrl = latestRelease.assets[0].browser_download_url;
    console.log(`Latest APK for ${appId}: ${downloadUrl}`);
}
```

> [!NOTE]
> The `bit` app might use tags starting simply with `v` (e.g., `v1.2.3`) instead of `bit-v1.2.3` for legacy reasons.

---

## Summary Table

| Resource | URL Path | Description |
| :--- | :--- | :--- |
| **App List** | `/apps.json` | Array of app IDs |
| **Metadata** | `/apps/{id}/app.json` | Icon, name, package name |
| **Status** | `/apps/{id}/status.json` | Build success/failure and timestamp |
| **Downloads** | GitHub Releases API | Search for tags starting with `{id}-v` |
