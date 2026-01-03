# Backup Strategy

This document outlines the backup and restore strategies for the MCC Minecraft server.

## Overview

We have multiple layers of backup protection:

| Layer | Method | Frequency | Location | World Data | Configs | Mods |
|-------|--------|-----------|----------|------------|---------|------|
| World Sync | `world-download` | Manual | LocalServer | Yes | No | No |
| Advanced Backups | Mod | Every 12h | Server `/backups/` | Yes | No | No |
| GitHub Releases | `.mrpack` | Per release | GitHub | No | Yes | Yes |
| Bloom.host | Panel backups | Varies | Bloom.host | Yes | Yes | Yes |

### Interactive Menu

All backup operations are available through the interactive menu:

```bash
python server-config.py    # Then press 'b' for Backup & World Sync
```

The menu organizes options by priority:
1. **World Sync (Primary)** - Download/upload between production and LocalServer
2. **Advanced Backups (Secondary)** - On-server backups via the mod

## Primary Strategy: World Sync

The recommended backup strategy uses `world-download` and `world-upload` commands which sync world data between production (Bloom.host) and LocalServer.

### Why World Sync?

1. **Selective backup** - Only downloads world data (~5GB), not DistantHorizons cache (~15GB)
2. **Off-site storage** - World data stored locally, separate from production
3. **Fast restore** - Two-phase upload minimizes server downtime
4. **Testable** - Can run LocalServer with production world before restoring

### Download Production World

```bash
cd MCC
python server-config.py world-download
```

This will:
1. Connect to Bloom.host via SFTP
2. Scan `/world/`, `/world_nether/`, `/world_the_end/`
3. Show size summary and confirm
4. Backup existing local world (optional)
5. Download all world data to `../LocalServer/world-production/`

**Options:**
- `-y` or `--yes` - Skip confirmation prompts
- `--no-backup` - Skip backing up existing local world

**Storage location:** `../LocalServer/world-production/` (and `_nether`, `_the_end`)

### Upload World to Production

```bash
cd MCC
python server-config.py world-upload
```

This performs a **two-phase upload** to minimize downtime:

**Phase 1 (Server offline):**
1. Stop production server
2. Delete existing world folders on production
3. Upload critical world data:
   - `region/` - Chunk data
   - `entities/` - Entity data
   - `poi/` - Villager job sites
   - `data/` - Map data, raids, etc.
   - `level.dat` - World metadata
4. Start production server

**Phase 2 (Server online):**
5. Upload non-critical data in background:
   - `DistantHorizons.sqlite` - LOD cache (~15GB)
   - `bluemap/` - Map tiles

Players can join during Phase 2. They may not see distant terrain LODs until the upload completes, but gameplay is unaffected.

**Options:**
- `-y` or `--yes` - Skip confirmation prompts

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

### CLI Commands

```bash
python server-config.py backup list              # List all backups
python server-config.py backup create [comment]  # Trigger manual backup
python server-config.py backup snapshot [comment] # Create snapshot
python server-config.py backup restore [number]  # Restore from backup
```

### Limitations

- Backups stored on same server (not off-site)
- Includes DistantHorizons.sqlite (~15GB), making backups large
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
python server-config.py update-pack 0.9.X -p
python server-config.py restart
```

## Restore Procedures

### Scenario 1: Restore World from LocalServer

If you have a recent `world-download` backup:

```bash
cd MCC
python server-config.py world-upload -y
```

### Scenario 2: Restore from Advanced Backups

If Advanced Backups mod is working:

```bash
cd MCC
python server-config.py backup list
python server-config.py backup restore 1    # Restore most recent
```

### Scenario 3: Restore Mods/Configs Only

If world is fine but mods are broken:

```bash
cd MCC
python server-config.py update-pack 0.9.X -p
python server-config.py restart
```

### Scenario 4: Full Disaster Recovery

If everything is lost:

1. Set up fresh server with mrpack4server
2. Restore mods: `python server-config.py update-pack <latest-version> -p`
3. Restore world from LocalServer: `python server-config.py world-upload -y`
4. Restart server

## Recommended Backup Schedule

| Action | Frequency | Command |
|--------|-----------|---------|
| World download | Weekly or before major changes | `world-download` |
| Manual snapshot | Before risky operations | `backup snapshot "pre-update"` |
| Verify backups | Monthly | `backup list` + test restore to LocalServer |

## File Locations

| Data | Production (Bloom.host) | Local Backup |
|------|------------------------|--------------|
| Overworld | `/world/` | `../LocalServer/world-production/` |
| Nether | `/world_nether/` | `../LocalServer/world-production_nether/` |
| The End | `/world_the_end/` | `../LocalServer/world-production_the_end/` |
| Advanced Backups | `/backups/world/` | N/A (on-server only) |
| Mods/Configs | GitHub releases | MCC repo |

## Non-Critical Files

These files are large but can be regenerated, so they're uploaded in Phase 2:

| File | Size | Purpose | Regeneration |
|------|------|---------|--------------|
| `DistantHorizons.sqlite` | ~15GB | LOD terrain cache | Auto-generates as players explore |
| `bluemap/` | Varies | Web map tiles | Regenerates on server start |

## Troubleshooting

### "Advanced Backups commands not recognized"

The mod may not be installed. Check:
```bash
python server-config.py update-pack <current-version> -p
python server-config.py restart
```

### World download is slow

Large worlds take time. The progress bar shows:
- Current file being downloaded
- Overall progress (files and bytes)
- Transfer speed and ETA

Consider running overnight for large worlds.

### Phase 2 upload fails

Non-critical data upload failures don't affect gameplay. You can:
1. Restart the upload: `world-upload -y`
2. Or ignore - data will regenerate over time
