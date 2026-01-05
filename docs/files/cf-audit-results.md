# TBA CurseForge Audit Results

**Audit Date:** December 27, 2025
**Pack Version:** 0.9.36 (88 mods after CF additions)

---

## Executive Summary

**Result: 85% Ready for CurseForge**

| Category | Count | Status |
|----------|-------|--------|
| Referenced in manifest.json | 73 | ✅ Ready |
| On Approved Non-CF List | 8 | ✅ Can bundle |
| Need Approval Requests | 4 | ⚠️ Submit requests |
| Omitted from CF Version | 1 | ❌ User decision |
| Server-side only | 2 | ➖ Not in client export |

---

## Verified On CurseForge (Can Reference in Manifest)

All mods below were verified to have Fabric 1.21.1 versions on CurseForge:

### Performance & Core
- Fabric API
- Fabric Language Kotlin
- FerriteCore
- ModernFix
- Krypton
- Spark
- Chunky
- Distant Horizons

### Libraries
- Architectury API
- Cloth Config API
- Balm
- Puzzles Lib
- Moonlight Lib
- CreativeCore
- Resourceful Lib
- Forge Config API Port
- Bad Packets
- Searchables
- Konkrete
- CraterLib
- Lithostitched
- JinxedLib

### Building & Decoration
- Macaw's Doors, Windows, Bridges, Roofs, Fences, Trapdoors, Furniture, Lights
- Chipped
- Handcrafted
- Adorn
- Excessive Building
- Supplementaries
- Arts & Crafts
- Reintegrated: Arts and Crafts
- Storage Drawers
- Underlay
- Connectible Chains
- WindChime Unofficial Continued
- Armor Statues
- Little Joys

### Content & Food
- Farmer's Delight Refabricated
- [Let's Do] Vinery (1.5.2 on CF!)
- [Let's Do] Farm & Charm
- [Let's Do] Bakery - Farm&Charm Compat
- Universal Sawmill

### Maps & Info
- JourneyMap
- BlueMap
- REI (Roughly Enough Items)
- WTHIT
- AppleSkin

### Utilities & QoL
- Controlling
- Mouse Tweaks
- ItemSwapper
- Just Zoom
- Camerapture
- Joy of Painting
- Better Sleep
- Simple Discord RPC
- Amendments

### Multimedia
- WATERFrAMES
- WATERMeDIA
- WATERMeDIA Youtube Plugin
- WATERViSION

### Server/Multiplayer
- Simple Voice Chat
- Universal Graves
- Flan
- Advanced Backups
- AutoWhitelist
- Polymer

### Other
- Axiom (AxiomTool) - All Rights Reserved but on CF
- Minescript
- Gamemode Unrestrictor
- Athena (CTM)

---

## Verified on Approved Non-CF List (Bundle in Overrides)

These mods are officially approved for bundling:

| Mod | License | Source |
|-----|---------|--------|
| Sodium | LGPL v3 | Approved List |
| Lithium | LGPL-3.0 | Approved List |
| Iris Shaders | GPL v3 | Approved List |
| MaLiLib | LGPL 2.1 | Approved List |
| Litematica | LGPL 2.1 | Approved List |
| Effortless Structure | GNU | Approved List |
| ReFramed | MIT | Approved List |
| Fabricord | Apache | Approved List |
| Fabric Seasons | - | Approved List |
| Fabric Seasons: Extras | - | Approved List |

**Note:** WATERMeDIA family is on CF now, so doesn't need approved list.

---

## Bundled Mods Analysis

### ✅ On Approved Non-CF List (8 mods - Can Bundle)

| Mod | License | Approved? |
|-----|---------|-----------|
| MaLiLib | LGPL 2.1 | ✅ Yes |
| Lithium | LGPL-3.0 | ✅ Yes |
| Litematica | LGPL 2.1 | ✅ Yes |
| ReFramed | MIT | ✅ Yes |
| Fabric Seasons | - | ✅ Yes |
| Fabric Seasons: Extras | - | ✅ Yes |
| Iris Shaders | GPL v3 | ✅ Yes |
| Effortless Structure | GNU | ✅ Yes |

### ⚠️ Need Approval Requests (4 mods)

| Mod | License | Modrinth Link | Action |
|-----|---------|---------------|--------|
| Better Sleep | Check | https://modrinth.com/mod/better-sleep | Submit approval |
| Chunky | GPL-3.0 | https://modrinth.com/mod/chunky | Submit approval |
| FerriteCore | MIT | https://modrinth.com/mod/ferrite-core | Submit approval |
| Simple Voice Chat | All Rights Reserved | - | Try CF project ID directly |

### ❌ Omitted from CF Version (1 mod - User Decision)

| Mod | Reason |
|-----|--------|
| Fairy Lights (Fabric) | Modrinth-only community port. User chose to omit. |

### ➖ Server-Side Only (2 mods - Not in Client Export)

| Mod | Purpose |
|-----|---------|
| AutoWhitelist | Discord-based whitelist |
| Fabricord | Discord integration |

---

## Next Steps

1. [ ] Submit approval requests for: Better Sleep, Chunky, FerriteCore
2. [ ] Try adding Simple Voice Chat via CF file ID
3. [ ] Wait for approvals (~3-5 business days)
4. [ ] Create CurseForge project page
5. [ ] Export and upload CF version

---

## Approval Request Template

**For Fairy Lights Fabric Port:**

```
Mod Name: Fairy Lights (Fabric Port)
Modrinth Link: https://modrinth.com/mod/fairy-lights
License: MIT License
Minecraft Version: 1.21.1
Mod Loader: Fabric

Justification:
This is a community Fabric port of the popular Fairy Lights mod (originally by pau101).
The MIT license permits redistribution. The mod adds decorative string lights and is
commonly used in building-focused modpacks. Including it in our CurseForge modpack
would provide a consistent experience across both platforms.
```

---

## Notes

- The `packwiz curseforge detect` command failed with 400 error (API issue)
- Manual verification was performed via web search
- All "blocker" mods from initial analysis (Polymer, Minescript, AutoWhitelist, etc.)
  are actually ON CurseForge - initial analysis was overly cautious
