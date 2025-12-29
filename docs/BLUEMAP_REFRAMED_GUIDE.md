# BlueMap + ReFramed Integration Guide

A guide for rendering [ReFramed](https://modrinth.com/mod/reframed) blocks in [BlueMap](https://bluemap.bluecolored.de/) web maps.

**Tested with:** ReFramed 1.6.6 / BlueMap 5.x / Minecraft 1.21.1 (Fabric)

---

## The Problem

ReFramed blocks appear invisible or broken on BlueMap renders because:

1. **ReFramed uses runtime texture swapping** - When you apply a "camo" texture (e.g., oak planks) to a ReFramed stair, the mod dynamically swaps textures at runtime using Fabric's rendering API
2. **BlueMap reads static assets only** - BlueMap parses `blockstates/*.json` and `models/block/*.json` directly from mod JARs, with no access to runtime-generated textures
3. **Result:** BlueMap can't find valid model definitions, so blocks render as invisible or use fallback pink/black textures

This is a fundamental limitation of all web-based map renderers (BlueMap, Dynmap, Squaremap) - they can't execute mod code to see runtime textures.

---

## The Solution

Create a **BlueMap resource pack** containing ReFramed's static model definitions. This gives BlueMap the geometry it needs to render blocks correctly.

### What You'll Get

| Aspect | Result |
|--------|--------|
| **Geometry** | Correct shapes (stairs, slopes, slabs, panels, etc.) |
| **Textures** | Base frame texture (the "empty" frame look) |
| **Camo textures** | Not rendered (limitation - see below) |

### Why Camo Textures Can't Be Rendered

True camo rendering would require:
- Creating a separate model variant for every block × every camo combination
- Oak stairs, stone stairs, dirt stairs... × 50+ block types = thousands of variants
- This doesn't scale and would bloat the resource pack enormously

The workaround provides **correct geometry with placeholder textures** - far better than invisible blocks.

---

## Step-by-Step Implementation

### Step 1: Extract Assets from ReFramed JAR

Download or locate `ReFramed-x.x.x.jar` and extract the assets folder:

```bash
# Using unzip (Linux/Mac/Git Bash)
mkdir -p reframed_assets
unzip ReFramed-1.6.6.jar -d reframed_assets "assets/reframed/*"

# Using 7-Zip (Windows GUI)
# Right-click JAR → 7-Zip → Open Archive → Extract assets/reframed/
```

You need these folders:
- `assets/reframed/blockstates/` - Block state → model mappings
- `assets/reframed/models/block/` - 3D model JSON definitions
- `assets/reframed/textures/` - Base textures (if present)

### Step 2: Create BlueMap Resource Pack

Create this folder structure in your BlueMap config:

```
config/bluemap/packs/
└── reframed-compat/
    ├── pack.mcmeta
    └── assets/
        └── reframed/
            ├── blockstates/
            │   └── (extracted files)
            ├── models/
            │   └── block/
            │       └── (extracted files)
            ├── textures/
            │   └── (extracted files, if any)
            └── blockProperties.json
```

### Step 3: Create pack.mcmeta

```json
{
  "pack": {
    "pack_format": 34,
    "description": "ReFramed block models for BlueMap compatibility"
  }
}
```

| Minecraft Version | pack_format |
|-------------------|-------------|
| 1.21.x | 34 |
| 1.20.5-1.20.6 | 32 |
| 1.20.2-1.20.4 | 22 |

### Step 4: Create blockProperties.json

This file tells BlueMap how to render ReFramed blocks:

```json
{
  "*": {
    "culling": true,
    "occluding": false,
    "cullingIdentical": true
  },
  "cube": {
    "occluding": true
  },
  "double_slab": {
    "occluding": true
  }
}
```

**Properties explained:**
- `culling: true` - Hide faces obscured by adjacent blocks (improves performance)
- `occluding: false` - Partial blocks don't cast ambient occlusion shadows
- `cullingIdentical: true` - Only cull faces between identical block states
- Full blocks (`cube`, `double_slab`) should have `occluding: true`

### Step 5: Handle Fabric-Specific Models (If Needed)

Some ReFramed models may use Fabric Rendering API extensions. If you see errors about unknown loaders:

```json
// Remove Fabric-specific loaders:
"loader": "fabric:dynamic_block_model"  // DELETE THIS LINE

// Ensure parent references are valid:
"parent": "minecraft:block/cube_all"
```

Most static geometry models should work without modification.

### Step 6: Deploy and Reload

Copy the pack to your server and reload BlueMap:

```bash
# Reload BlueMap configuration
/bluemap reload

# CRITICAL: Purge old renders (required for changes to take effect)
/bluemap purge <map-name>

# Trigger fresh render
/bluemap update <map-name>
```

**Important:** The purge step is mandatory. Old cached renders with broken ReFramed data won't update automatically.

---

## Troubleshooting

### Blocks Still Invisible

1. **Check folder structure** - Must be `packs/reframed-compat/assets/reframed/blockstates/`, not `packs/reframed-compat/reframed/blockstates/`

2. **Check BlueMap logs** for parsing errors:
   ```
   bluemap/logs/debug.log
   ```

3. **Validate JSON syntax:**
   ```bash
   python -c "import json; json.load(open('blockstates/cube.json'))"
   ```

4. **Verify purge completed** - Render cache must be cleared

### Pink/Black Textures

Missing texture references. Check that:
- All parent models exist
- Texture paths in models are correct
- `assets/reframed/textures/` contains required PNGs

### Only Some Blocks Render

The blockstates folder may be incomplete. Ensure you extracted:
- All `*.json` files from `blockstates/`
- All model files they reference from `models/block/`

---

## Alternative Approaches

### For Mod Developers

Consider shipping a BlueMap-specific resource pack or adding static model fallbacks:

```
assets/reframed/bluemap/blockstates/  ← BlueMap checks this first
assets/reframed/blockstates/          ← Standard location
```

BlueMap automatically prefers `assets/<namespace>/bluemap/` paths, allowing mods to provide optimized static models without affecting in-game rendering.

### Native BlueMap Support

A cleaner long-term solution would be:
1. ReFramed exports static model variants for common camo textures
2. BlueMap add-on that reads ReFramed's block entity data to select correct texture

This would require coordination between both projects.

---

## Technical Background

### How ReFramed Works (In-Game)

1. Player right-clicks frame block with source block (e.g., oak planks)
2. ReFramed stores camo block ID in BlockEntity NBT data
3. At render time, Fabric Rendering API intercepts and swaps textures
4. Client sees oak-textured stairs; server stores frame + NBT reference

### How BlueMap Works

1. Reads `blockstates/<block>.json` to find model for each block state
2. Loads referenced `models/block/<model>.json` for geometry
3. Bakes textures from `textures/` into 3D tiles
4. Serves pre-rendered tiles via web interface

### The Incompatibility

BlueMap has no mechanism to:
- Execute Fabric rendering callbacks
- Read BlockEntity NBT to determine camo texture
- Dynamically swap textures per-block-instance

Hence the need for static model fallbacks.

---

## References

- [BlueMap - Configuring Mods](https://bluemap.bluecolored.de/wiki/customization/Mods.html)
- [BlueMap - Resource Packs](https://bluemap.bluecolored.de/wiki/customization/ResourcePacks.html)
- [ReFramed on Modrinth](https://modrinth.com/mod/reframed)
- [Minecraft Resource Pack Format](https://minecraft.wiki/w/Resource_pack)

---

## Credits

Guide created for [MCC (MinecraftCollege.com)](https://github.com/mindfulent/MCC) modpack.

If you found this useful, consider supporting the mod developers:
- **ReFramed** by Quilt Team - [Modrinth](https://modrinth.com/mod/reframed)
- **BlueMap** by BlueColored - [Ko-fi](https://ko-fi.com/bluecolored) / [Patreon](https://www.patreon.com/bluecolored)
