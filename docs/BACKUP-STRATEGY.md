# Backup Strategy

This document outlines the backup and restore strategies for the TBA (The Block Academy) Minecraft server.

## Overview

We have multiple layers of backup protection:

| Layer | Method | Frequency | Location | World Data | Configs | Mods |
|-------|--------|-----------|----------|------------|---------|------|
| World Sync | LocalServer commands | Manual | LocalServer | Yes | No | No |
| Advanced Backups | Mod | Every 12h | Server `/backups/` | Yes | No | No |
| GitHub Releases | `.mrpack` | Per release | GitHub | No | Yes | Yes |
| Bloom.host | Panel backups | Varies | Bloom.host | Yes | Yes | Yes |

### Interactive Menus

World sync operations are available in **LocalServer**:

```bash
cd LocalServer
python server-config.py    # Interactive menu with World Sync section
```

Server management and Advanced Backups are in **TBA**:

```bash
cd TBA
python server-config.py    # Then press 'b' for Backup & World Sync
```

## Primary Strategy: World Sync (LocalServer)

The recommended backup strategy uses LocalServer's world sync commands which handle DistantHorizons data separately for efficiency.

### Why This Approach?

1. **Selective backup** - Downloads world data (~5GB) separately from DistantHorizons (~1-2GB)
2. **Cold storage** - DH files stored separately, rarely need updating
3. **Fast restore** - Upload world first, DH can follow while server is online
4. **Testable** - Can run LocalServer with production world before restoring

### DistantHorizons Handling

DistantHorizons SQLite files are large LOD caches that:
- Exist in each dimension (`world/data/`, `world/DIM-1/data/`, `world/DIM1/data/`)
- Can be ~1-2GB total across all dimensions
- Are NOT required for server startup
- Can regenerate automatically as players explore

Because of this, they're handled separately:
- **Cold storage location:** `LocalServer/distant-horizons-cold/`
- Download once, keep indefinitely
- Upload after server is back online (not a hard dependency)

### Download Production World

```bash
cd LocalServer
python server-config.py download-world       # Excludes DH (default)
python server-config.py download-world --full  # Include DH (rare)
python server-config.py download-world -y    # Skip prompts
python server-config.py download-world --no-backup  # Skip local backup
```

This will:
1. Connect to Bloom.host via SFTP
2. Scan `/world/`, `/world_nether/`, `/world_the_end/`
3. Show size summary (with DH exclusion info)
4. Backup existing local world (optional)
5. Download world data to `world-production/`
6. Display elapsed time on completion

**Storage location:** `LocalServer/world-production/` (excludes DH by default)

### Download DistantHorizons (Cold Storage)

```bash
cd LocalServer
python server-config.py download-dh       # Download to cold storage
python server-config.py download-dh -y    # Skip prompts
```

Downloads DH files to `distant-horizons-cold/` with subdirectories:
- `overworld/` - Main world DH data
- `nether/` - Nether DH data
- `end/` - End DH data

**When to use:** Rarely. Only needed when setting up a new local environment or if DH data is corrupted.

### Local Testing with Backup Preservation

When you run LocalServer in production mode, **the backup is preserved**:

```
world-production/         <- Pristine backup (never modified by LocalServer)
world-local/              <- Working copy for Production mode testing
world-fresh/              <- Fresh World mode (clean slate, all mods)
world-vanilla/            <- Vanilla Debug mode (Fabric only)
distant-horizons-cold/    <- DH cold storage (separate from world data)
```

**Workflow:**
1. `download-world` (LocalServer) -> Downloads to `world-production/`
2. `mode production` (LocalServer) -> Copies to `world-local/` if needed
3. Server runs on `world-local/` - backup stays clean
4. To reset: `reset-local` (LocalServer) -> Re-copies from backup

This means you can break things locally, then reset to the clean backup state anytime.

**Other LocalServer modes** (for testing without production data):
- `mode fresh` - New world with all mods (test mod initialization)
- `mode vanilla` - New world with Fabric only (isolate mod issues)

### Upload World to Production

```bash
cd LocalServer
python server-config.py upload-world       # Requires server offline
python server-config.py upload-world -y    # Skip prompts
```

**Important:** This uploads from `world-production/` (the backup), NOT `world-local/`. Local test changes are not pushed to production.

**Requires server offline** - You'll be prompted to confirm the server is stopped.

This will:
1. Connect to Bloom.host via SFTP
2. Clear existing world folders on production
3. Upload all world data (excluding DH)
4. Display elapsed time on completion

### Upload DistantHorizons

```bash
cd LocalServer
python server-config.py upload-dh       # Server can be online
python server-config.py upload-dh -y    # Skip prompts
```

**Server can remain online** - DH files are not required for gameplay.

Uploads from `distant-horizons-cold/` to production. Players may not see distant terrain LODs until upload completes, but gameplay is unaffected.

### Standard Restore Workflow

1. **Stop production server** (via Bloom.host panel or TBA commands)
2. `upload-world` - Upload world data (server offline)
3. **Start production server**
4. `upload-dh` - (Optional) Upload DistantHorizons while server runs

## Alternative: TBA World Sync Commands

TBA also has world sync commands that download/upload everything including DH:

```bash
cd TBA
python server-config.py world-status     # View backup status
python server-config.py world-download   # Download ALL data (including DH)
python server-config.py world-upload     # Two-phase upload
```

**TBA's `world-upload`** performs a two-phase upload:
- Phase 1 (server offline): Critical world data
- Phase 2 (server online): DistantHorizons and BlueMap

**When to use TBA commands:** When you want a complete backup/restore including all DH data in one operation.

**When to use LocalServer commands:** When you want control over DH handling (recommended for routine backups).

## Secondary: Advanced Backups Mod

The server runs the **Advanced Backups** mod for automated on-server backups.

### Configuration

Located at `config/AdvancedBackups.properties`:

| Setting | Value | Description |
|---------|-------|-------------|
| Schedule | Every 12h uptime | Backup frequency |
| Type | Differential | Only changed files after first full backup |
| Retention | 5GB / 14 days / 30 backups | Whichever limit is hit first |
| On shutdown | Enabled | Backup when server stops |

### In-Game Commands (Ops)

```
/backup start           # Trigger manual backup
/backup list            # List available backups
/backup snapshot        # Create snapshot (immune to auto-purge)
```

### CLI Commands (from TBA)

```bash
cd TBA
python server-config.py backup list              # List all backups
python server-config.py backup create [comment]  # Trigger manual backup
python server-config.py backup snapshot [comment] # Create snapshot
python server-config.py backup restore [number]  # Restore from backup
```

### Limitations

- Backups stored on same server (not off-site)
- Includes DistantHorizons.sqlite, making backups large
- Restore requires full server downtime

## Tertiary: GitHub Releases

Every modpack version is preserved as a GitHub release containing:

- All mod JARs (via mrpack format)
- All config files
- Shader packs
- Default settings

**Does NOT include:** World data

To restore mods/configs to a specific version:
```bash
cd TBA
python server-config.py update-pack 0.9.X -p
python server-config.py restart
```

## Restore Procedures

### Scenario 1: Restore World from LocalServer

If you have a recent backup:

```bash
cd LocalServer
python server-config.py upload-world -y   # Server must be offline
# Start server
python server-config.py upload-dh -y      # Optional, server can be online
```

### Scenario 2: Restore from Advanced Backups

If Advanced Backups mod is working:

```bash
cd TBA
python server-config.py backup list
python server-config.py backup restore 1    # Restore most recent
```

### Scenario 3: Restore Mods/Configs Only

If world is fine but mods are broken:

```bash
cd TBA
python server-config.py update-pack 0.9.X -p
python server-config.py restart
```

### Scenario 4: Full Disaster Recovery

If everything is lost:

1. Set up fresh server with mrpack4server
2. Restore mods: `cd TBA && python server-config.py update-pack <latest-version> -p`
3. Restore world: `cd LocalServer && python server-config.py upload-world -y`
4. Start server
5. (Optional) Upload DH: `python server-config.py upload-dh -y`

## Recommended Backup Schedule

| Action | Frequency | Command (from LocalServer) |
|--------|-----------|----------------------------|
| World download | Weekly or before major changes | `download-world` |
| DH cold storage | Once, then rarely | `download-dh` |
| Manual snapshot | Before risky operations | (TBA) `backup snapshot "pre-update"` |
| Verify backups | Monthly | Test restore to LocalServer |

## File Locations

| Data | Production (Bloom.host) | Local Backup |
|------|------------------------|--------------|
| World (all dimensions) | `/world/` | `LocalServer/world-production/` |
| - Overworld | `/world/region/` | `LocalServer/world-production/region/` |
| - Nether | `/world/DIM-1/` | `LocalServer/world-production/DIM-1/` |
| - The End | `/world/DIM1/` | `LocalServer/world-production/DIM1/` |
| DistantHorizons | `/world/*/data/` | `LocalServer/distant-horizons-cold/` |
| Advanced Backups | `/backups/world/` | N/A (on-server only) |
| Mods/Configs | GitHub releases | TBA repo |

**Note:** Vanilla Minecraft stores all dimensions inside the main world folder (DIM-1 = Nether, DIM1 = The End).

## DistantHorizons Files

These files are large LOD caches stored separately:

| Location | Contents | Size |
|----------|----------|------|
| `/world/data/DistantHorizons.sqlite` | Overworld LODs | ~500MB-1GB |
| `/world/DIM-1/data/DistantHorizons.sqlite` | Nether LODs | ~200-500MB |
| `/world/DIM1/data/DistantHorizons.sqlite` | End LODs | ~100-200MB |

Each also has `-shm` and `-wal` journal files.

**Cold storage structure:**
```
distant-horizons-cold/
├── overworld/
│   ├── DistantHorizons.sqlite
│   ├── DistantHorizons.sqlite-shm
│   └── DistantHorizons.sqlite-wal
├── nether/
│   └── ...
└── end/
    └── ...
```

## Troubleshooting

### "Advanced Backups commands not recognized"

The mod may not be installed. Check:
```bash
cd TBA
python server-config.py update-pack <current-version> -p
python server-config.py restart
```

### World download is slow

Large worlds take time. The progress bar shows:
- Current file being downloaded
- Overall progress (files and bytes)
- Transfer speed and ETA
- Elapsed time on completion

Consider running overnight for large worlds.

### Upload fails mid-transfer

For world uploads:
1. Ensure server is offline
2. Retry: `upload-world -y`

For DH uploads:
1. Server can stay online
2. Retry: `upload-dh -y`
3. Or ignore - data will regenerate over time

### SFTP credentials not configured

Both TBA and LocalServer need `.env` files with SFTP credentials:

```bash
# Copy template and fill in credentials
cp .env.example .env
```

Required variables: `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`
