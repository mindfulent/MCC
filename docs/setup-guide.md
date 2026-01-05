# The Block Academy 1.21.1 Fabric Server & Modpack Setup Guide

A complete walkthrough for setting up your Bloom.host server with Fabric 1.21.1, optimized JVM flags for 12GB RAM, and creating/distributing a custom modpack via Modrinth.

---

## Table of Contents

1. [Part 1: Server Setup on Bloom.host](#part-1-server-setup-on-bloomhost)
2. [Part 2: Modpack Creation with Packwiz](#part-2-modpack-creation-with-packwiz)
3. [Part 3: Modpack Distribution](#part-3-modpack-distribution)
4. [Part 4: Player Onboarding](#part-4-player-onboarding)
5. [Part 5: Maintenance & Updates](#part-5-maintenance--updates)

---

## Part 1: Server Setup on Bloom.host

### Step 1.1: Set Server Type to Fabric 1.21.1

1. Log into [Bloom.host Panel](https://mc.bloom.host)
2. Select your Minecraft server
3. Go to **Settings** tab
4. Find **Change Server Type** on the right side
5. Set:
   - **Platform:** Fabric
   - **Minecraft Version:** 1.21.1
   - **Loader Version:** Latest stable (0.16.x as of writing)
6. Click **Change Server Type**
7. Wait for installation to complete

### Step 1.2: Set Java Version

1. Go to **Startup** tab
2. Find **Java Version** dropdown (usually top-right)
3. Select **Java 21** (required for Minecraft 1.20.5+)
4. Save changes

### Step 1.3: Configure Optimized JVM Flags

Bloom.host uses Aikar's flags by default, but since you have 12GB RAM (which is at the threshold for adjusted flags), verify your startup configuration.

**Navigate to Startup → Startup Flags** and ensure these flags are set:

```
-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true
```

**Memory allocation:** Bloom.host handles `-Xms` and `-Xmx` automatically based on your plan. With 12GB, expect ~10.5-11GB allocated to the JVM (overhead reserved for OS/container).

> **Note:** If you see RAM usage appearing "maxed out" in the panel, this is normal behavior with Aikar's flags. Use `/spark health` in-game to see actual memory usage.

### Step 1.4: Upload Server-Side Performance Mods

Connect via **SFTP** (recommended for bulk uploads) or use the **File Manager**.

**SFTP Connection:**
- Host: `sftp.bloom.host`
- Port: `2022`
- Username/Password: Same as panel login

Create/navigate to the `/mods` folder and upload these server-side mods:

#### Core Performance Stack (Required)
| Mod | Download Link | Purpose |
|-----|--------------|---------|
| **Fabric API** | [Modrinth](https://modrinth.com/mod/fabric-api) | Required dependency |
| **Lithium** | [Modrinth](https://modrinth.com/mod/lithium) | Game logic optimization (~50% tick improvement) |
| **FerriteCore** | [Modrinth](https://modrinth.com/mod/ferrite-core) | Memory optimization (~45% RAM reduction) |
| **Krypton** | [Modrinth](https://modrinth.com/mod/krypton) | Network stack optimization |
| **ModernFix** | [Modrinth](https://modrinth.com/mod/modernfix) | Faster loading, dynamic resources |

#### Recommended Server Utilities
| Mod | Download Link | Purpose |
|-----|--------------|---------|
| **Spark** | [Modrinth](https://modrinth.com/mod/spark) | Performance profiling |
| **Chunky** | [Modrinth](https://modrinth.com/mod/chunky) | World pre-generation |

> **Important:** Only upload mods marked as `server` or `both` for environment. Client-only mods will cause crashes.

### Step 1.5: Configure server.properties

Edit `server.properties` in File Manager:

```properties
# Performance settings
view-distance=10
simulation-distance=8
max-players=20
network-compression-threshold=256

# World settings
level-name=world
level-type=default
spawn-protection=0

# Gameplay
difficulty=normal
gamemode=survival
pvp=true
enable-command-block=false

# MOTD (shows in server list)
motd=\u00A7b\u00A7lThe Block Academy\u00A7r \u00A77| \u00A7fWhere Creativity Meets Community
```

### Step 1.6: Pre-generate the World (Recommended)

Before launch, pre-generate chunks to prevent lag when players explore:

1. Start the server
2. Run in console: `chunky radius 3000`
3. Run: `chunky start`
4. Monitor progress with: `chunky progress`
5. When complete, run: `chunky cancel`

For a snowy spawn, either:
- Use a seed that spawns in a snowy biome
- Or use: `chunky center <x> <z>` to center on known snowy coordinates

### Step 1.7: Server File Structure

After setup, your server directory should look like:

```
/
├── mods/
│   ├── fabric-api-x.x.x.jar
│   ├── lithium-x.x.x.jar
│   ├── ferrite-core-x.x.x.jar
│   ├── krypton-x.x.x.jar
│   ├── modernfix-x.x.x.jar
│   ├── spark-x.x.x.jar
│   └── chunky-x.x.x.jar
├── config/
├── world/
├── server.properties
├── eula.txt (set to true)
└── fabric-server-launch.jar
```

---

## Part 2: Modpack Creation with Packwiz

Packwiz creates TOML metadata files that track your mods, making version control and updates easy.

### Step 2.1: Install Packwiz

**Windows:**
1. Download latest release from [GitHub Actions](https://github.com/packwiz/packwiz/actions)
2. Extract `packwiz.exe` to a folder (e.g., `C:\Tools\packwiz`)
3. Add folder to PATH:
   - Search "Environment Variables" in Windows
   - Edit Path → Add `C:\Tools\packwiz`
4. Open new terminal, verify: `packwiz --version`

**Alternative (Go install):**
```bash
go install github.com/packwiz/packwiz@latest
```

### Step 2.2: Initialize Your Modpack

```bash
# Create and enter modpack directory
cd C:\Users\slash\Projects
mkdir minecraft-college-pack
cd minecraft-college-pack

# Initialize packwiz
packwiz init
```

When prompted:
- **Pack name:** `The Block Academy`
- **Pack version:** `1.0.0`
- **Pack author:** `Slash`
- **Minecraft version:** `1.21.1`
- **Mod loader:** `fabric`
- **Loader version:** (accept latest/default)

This creates:
- `pack.toml` - Main pack definition
- `index.toml` - File index with hashes

### Step 2.3: Add Mods from Modrinth

```bash
# Performance Core (client-side)
packwiz mr install sodium
packwiz mr install lithium
packwiz mr install ferrite-core
packwiz mr install modernfix
packwiz mr install iris

# Shader support
packwiz mr install iris

# Content mods
packwiz mr install farmers-delight-refabricated
packwiz mr install chipped
packwiz mr install handcrafted

# Macaw's building suite
packwiz mr install macaws-doors
packwiz mr install macaws-windows
packwiz mr install macaws-bridges
packwiz mr install macaws-roofs
packwiz mr install macaws-fences-and-walls
packwiz mr install macaws-trapdoors
packwiz mr install macaws-furniture
packwiz mr install macaws-lights-and-lamps

# Storage
packwiz mr install sophisticated-storage

# Quality of Life
packwiz mr install journeymap
packwiz mr install appleskin
packwiz mr install jade
packwiz mr install mouse-tweaks
packwiz mr install inventory-profiles-next
packwiz mr install controlling

# Ambience (client-side)
packwiz mr install effective
packwiz mr install mambience
```

### Step 2.4: Set Client/Server Side Correctly

Edit individual `.pw.toml` files in `mods/` to ensure correct side:

For **client-only** mods (shaders, visual effects), add:
```toml
[option]
side = "client"
```

For **server-only** mods:
```toml
[option]
side = "server"
```

For **both** (default, usually auto-detected):
```toml
[option]
side = "both"
```

### Step 2.5: Add Config Files (Optional)

Create an `overrides/` folder for pre-configured settings:

```
minecraft-college-pack/
├── mods/
├── overrides/
│   ├── config/
│   │   └── iris.properties
│   └── options.txt
├── pack.toml
└── index.toml
```

Example `overrides/options.txt`:
```
renderDistance:12
guiScale:3
gamma:0.5
```

After adding overrides, refresh the index:
```bash
packwiz refresh
```

### Step 2.6: Create .packwizignore

Create `.packwizignore` to exclude files from the pack:

```
# Exclude packwiz executable
packwiz.exe
packwiz

# Exclude git files
.git/
.gitignore

# Exclude exports
*.mrpack
*.zip
```

### Step 2.7: Test Locally

Start a local HTTP server to test:
```bash
packwiz serve
```

This starts a server at `http://localhost:8080` - you can use this URL with packwiz-installer to test.

---

## Part 3: Modpack Distribution

### Option A: Publish to Modrinth (Recommended)

#### Step 3.1: Export to .mrpack

```bash
packwiz modrinth export
```

This creates `Minecraft-College-1.0.0.mrpack` with:
- All mod references (downloaded from Modrinth on install)
- Bundled JARs for any CurseForge-only mods
- Config overrides
- Client/server side metadata

#### Step 3.2: Upload to Modrinth

1. Go to [modrinth.com/dashboard/projects](https://modrinth.com/dashboard/projects)
2. Click **Create a project**
3. Select **Modpack**
4. Fill in details:
   - **Name:** The Block Academy
   - **Slug:** `the-block-academy`
   - **Summary:** "Where Creativity Meets Community - A Fabric 1.21.1 modpack for learning and mastering creative crafts"
   - **Categories:** Education, Lightweight, Multiplayer
5. Upload your `.mrpack` file as a version
6. Set version number, changelog, supported Minecraft versions
7. Submit for review

#### Step 3.3: Install on Server via mrpack4server

For easy server installation, use [mrpack4server](https://github.com/Patbox/mrpack4server):

1. Download `mrpack4server.jar` from GitHub releases
2. Upload to Bloom.host server root via SFTP
3. Create `modpack-info.json`:
```json
{
  "project_id": "minecraft-college",
  "version_id": "1.0.0"
}
```
4. In Bloom panel → Startup → Server Jar File: `mrpack4server.jar`
5. Start server - it will auto-download the modpack

**Alternative: Manual server install**
1. Export pack: `packwiz modrinth export`
2. Use [mrpack-install](https://github.com/nothub/mrpack-install):
```bash
mrpack-install minecraft-college --server-dir /path/to/server
```

### Option B: Self-Host with packwiz-installer (Auto-Updates)

If you want players to auto-update without re-downloading:

#### Step 3.1: Host pack files

Push your packwiz files to GitHub and enable GitHub Pages, or use any static hosting (Netlify, Cloudflare Pages).

Your pack files should be accessible at a URL like:
`https://yourdomain.com/pack/pack.toml`

#### Step 3.2: Create a pre-configured Prism instance

1. Create a barebones Prism Launcher instance with Fabric 1.21.1
2. Download [packwiz-installer-bootstrap.jar](https://github.com/packwiz/packwiz-installer-bootstrap/releases)
3. Place it in the instance's `.minecraft` folder
4. Edit Instance → Settings → Custom Commands
5. Add Pre-launch command:
```
"$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://yourdomain.com/pack/pack.toml
```
6. Export instance as `.zip`

Players import this instance, and it auto-updates every launch.

---

## Part 4: Player Onboarding

### For Players: Prism Launcher Setup

Create this guide for your community:

---

#### Installing The Block Academy Modpack

**Step 1: Download Prism Launcher**
- Visit [prismlauncher.org](https://prismlauncher.org)
- Download for your OS (Windows/Mac/Linux)
- Install and open

**Step 2: Sign In**
- Click **Accounts** (top-right) → **Manage Accounts**
- Click **Add Microsoft** → Sign in with your Minecraft account

**Step 3: Add the Modpack**

*Option A: From Modrinth (if published)*
1. Click **Add Instance**
2. Select **Modrinth** on the left
3. Search "The Block Academy"
4. Click the modpack → **OK**
5. Wait for download

*Option B: From .mrpack file*
1. Download the `.mrpack` file from Discord/website
2. Click **Add Instance**
3. Select **Import** on the left
4. Browse to your downloaded `.mrpack`
5. Click **OK**

**Step 4: Allocate RAM**
1. Right-click the instance → **Edit**
2. Go to **Settings** → Check **Memory**
3. Set **Maximum memory** to `4096 MB` (4GB) minimum
   - 6GB recommended if you have 16GB+ system RAM
   - 8GB if using heavy shaders

**Step 5: (Optional) Add Shaders**
1. Download a shader pack:
   - [Complementary Reimagined](https://modrinth.com/shader/complementary-reimagined) (best performance scaling)
   - [BSL Shaders](https://modrinth.com/shader/bsl-shaders) (high quality)
2. Right-click instance → **Edit** → **Shader packs**
3. Click **Add** → Select your downloaded `.zip`
4. Enable in-game: Options → Video Settings → Shader Packs

**Step 6: Launch & Connect**
1. Double-click the instance to launch
2. In Minecraft, click **Multiplayer** → **Add Server**
3. Server Address: `play.theblock.academy`
4. Click **Done** → Connect!

---

### Recommended Client Settings

Share these with your community for optimal experience:

**Video Settings:**
- Render Distance: 12-16 (adjust based on performance)
- Simulation Distance: 8
- VSync: Off (enable if screen tearing)
- Max Framerate: Match your monitor refresh rate

**For Lower-End PCs:**
- Use Complementary Shaders "Potato" preset
- Reduce render distance to 8
- Disable Effective water effects in mod settings

---

## Part 5: Maintenance & Updates

### Updating the Modpack

```bash
# Update all mods to latest compatible versions
packwiz update --all

# Update specific mod
packwiz update sodium

# Refresh index after any manual changes
packwiz refresh

# Export new version
packwiz modrinth export
```

Then upload new `.mrpack` to Modrinth as a new version.

### Updating the Server

**If using mrpack4server:**
1. Edit `modpack-info.json` with new version
2. Restart server - it auto-updates

**If using manual installation:**
1. Stop server
2. Backup `/mods` and `/config` folders
3. Delete contents of `/mods`
4. Run `mrpack-install minecraft-college <new-version>`
5. Start server

### Syncing Server and Client Mods

The `.mrpack` format handles this automatically via the `env` field:
- Mods marked `"server": "required"` install on servers
- Mods marked `"client": "required"` install on clients
- Mods marked `"both"` install everywhere

### Version Control with Git

Initialize git in your packwiz folder:

```bash
git init
git add .
git commit -m "Initial The Block Academy modpack v1.0.0"
```

Create `.gitattributes` to prevent line-ending issues:
```
* text=auto
*.toml text eol=lf
```

---

## Quick Reference

### Key Commands

| Task | Command |
|------|---------|
| Initialize pack | `packwiz init` |
| Add mod from Modrinth | `packwiz mr install <slug>` |
| Add mod from CurseForge | `packwiz cf install <slug>` |
| Update all mods | `packwiz update --all` |
| Refresh index | `packwiz refresh` |
| Export to Modrinth format | `packwiz modrinth export` |
| Test locally | `packwiz serve` |

### Key URLs

- **Bloom.host Panel:** https://mc.bloom.host
- **Modrinth:** https://modrinth.com
- **Prism Launcher:** https://prismlauncher.org
- **Packwiz Docs:** https://packwiz.infra.link

### File Locations

| What | Path |
|------|------|
| Local packwiz project | `C:\Users\slash\Projects\minecraft-college-pack` |
| Server mods | `/mods` on Bloom.host |
| Player instance | `%APPDATA%\PrismLauncher\instances\<instance>\` (Windows) |

---

## Troubleshooting

### Server won't start after adding mods
- Check `/logs/latest.log` for errors
- Ensure all mods are for Fabric 1.21.1
- Verify no client-only mods in server `/mods`

### Players can't connect
- Verify server is running and not crashed
- Check that client and server mod versions match
- Ensure Fabric API versions are compatible

### Low TPS on server
- Run `/spark tps` to check performance
- Run `/spark profiler` to identify lag sources
- Pre-generate more chunks with Chunky
- Reduce view-distance in `server.properties`

### Modpack not updating for players
- If using packwiz-installer, verify the hosted `pack.toml` is updated
- If using Modrinth, ensure players update the instance in Prism

---

*Last updated: December 2024*
*For Minecraft 1.21.1 | Fabric Loader | Season 1 Launch*
