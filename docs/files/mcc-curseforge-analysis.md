# TBA Modpack CurseForge Compatibility Analysis

**Modpack:** TBA v0.9.36 (88 mods)  
**Analysis Date:** December 27, 2025

---

## Executive Summary

**Good news:** Your modpack is largely CurseForge-compatible. Of your 88 mods, most critical Modrinth-exclusives (Sodium, Lithium, Iris, Litematica, MaLiLib) are already on the approved non-CurseForge list.

**Estimated lift:** Medium - requires verification of ~15-20 mods against CurseForge availability, with likely 3-5 requiring manual approval requests or alternatives.

---

## Status Categories

| Status | Count | Action Required |
|--------|-------|-----------------|
| ✅ On CurseForge | ~60 | Reference via manifest.json |
| ✅ Approved Non-CF | ~15 | Bundle in overrides folder |
| ⚠️ Needs Verification | ~10 | Check CF availability |
| ❌ Potential Blockers | ~3 | Find alternatives or request approval |

---

## Detailed Mod Analysis

### ✅ CONFIRMED ON APPROVED LIST (Can bundle in overrides)

These Modrinth-only mods are **pre-approved** for CurseForge modpacks:

| Mod | License | Status |
|-----|---------|--------|
| **Sodium** | LGPL v3 | ✅ Approved |
| **Lithium** | LGPL-3.0 | ✅ Approved |
| **Iris Shaders** | GPL v3 | ✅ Approved |
| **MaLiLib** | LGPL 2.1 | ✅ Approved |
| **Litematica** | LGPL 2.1 | ✅ Approved |
| **Effortless Structure** | GNU | ✅ Approved |
| **ReFramed** | MIT | ✅ Approved |
| **Fabricord** | Apache | ✅ Approved |

### ✅ LIKELY ON CURSEFORGE (Need verification)

These mods typically have CurseForge presence - verify and reference via manifest:

| Mod | Author | Notes |
|-----|--------|-------|
| **Fabric API** | FabricMC | ✅ On CurseForge |
| **Architectury API** | shedaniel | ✅ On CurseForge |
| **Cloth Config API** | shedaniel | ✅ On CurseForge |
| **JourneyMap** | techbrew | ✅ On CurseForge |
| **Chipped** | Terrarium Earth | ✅ On CurseForge |
| **Handcrafted** | Terrarium Earth | ✅ On CurseForge |
| **Macaw's Doors** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Windows** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Bridges** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Roofs** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Fences and Walls** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Trapdoors** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Furniture** | sketch_macaw | ✅ On CurseForge |
| **Macaw's Lights and Lamps** | sketch_macaw | ✅ On CurseForge |
| **Storage Drawers** | Texelsaur | ✅ On CurseForge |
| **Supplementaries** | MehVahdJukaar | ✅ On CurseForge |
| **REI** | shedaniel | ✅ On CurseForge |
| **Simple Voice Chat** | henkelmax | ✅ On CurseForge |
| **Controlling** | jaredlll08 | ✅ On CurseForge |
| **AppleSkin** | squeek502 | ✅ On CurseForge |
| **Mouse Tweaks** | YaLTeR | ✅ On CurseForge |
| **Balm** | BlayTheNinth | ✅ On CurseForge |
| **Puzzles Lib** | Fuzs | ✅ On CurseForge |
| **Moonlight Lib** | MehVahdJukaar | ✅ On CurseForge |
| **CreativeCore** | CreativeMD | ✅ On CurseForge |
| **Farmer's Delight** | vectorwing | ✅ On CurseForge (original) |
| **spark** | lucko | ✅ On CurseForge |
| **Chunky** | pop4959 | ✅ On CurseForge |
| **Distant Horizons** | jeseibel | ✅ On CurseForge |
| **BlueMap** | BlueColored | ✅ On CurseForge |

### ⚠️ NEEDS VERIFICATION (Check CurseForge + Approved List)

| Mod | Author | Risk Level |
|-----|--------|------------|
| **Farmer's Delight Refabricated** | Lesbian, MehVahdJukaar | Medium - Fabric port may differ from original |
| **[Let's Do] Vinery** | satisfyu | Low - Check CF presence |
| **[Let's Do] Bakery** | satisfyu | Low - Check CF presence |
| **[Let's Do] Farm & Charm** | satisfyu | Low - Check CF presence |
| **Fabric Seasons** | D4rkness_King | Medium - May be Modrinth-only |
| **Fabric Seasons: Extras** | D4rkness_King | Medium - May be Modrinth-only |
| **Axiom** | Moulberry | Medium - Premium mod, check distribution |
| **WATERMeDIA** | SrRapero720 | Medium - Check "watermine" on approved list |
| **WATERFrAMES** | SrRapero720 | Medium - Same author as watermine |
| **Adorn** | Juuz | Low - Check CF presence |
| **Excessive Building** | Yirmiri | Low - Check CF presence |

### ❌ POTENTIAL BLOCKERS (Require action)

| Mod | Issue | Solution |
|-----|-------|----------|
| **Polymer** | Modrinth-only, server-side mod | Check license (MIT by Patbox) - submit approval request |
| **Minescript** | Niche mod, likely Modrinth-only | Check MIT license - submit approval request |
| **AutoWhitelist** | Modrinth-only server mod | Check license - may need approval request |
| **Gamemode Unrestrictor** | Small mod, likely Modrinth-only | Check license - may need alternative |
| **WindChime Unofficial Continued** | Unofficial port | May have licensing issues |
| **Joy of Painting** | Check distribution rights | Verify CurseForge presence |
| **Camerapture** | Newer mod | Verify CurseForge presence |

---

## Action Plan

### Phase 1: Automated Verification (30 minutes)

Run `packwiz curseforge detect` on your existing pack to auto-identify CurseForge equivalents:

```bash
cd C:\Users\slash\Projects\TBA
packwiz curseforge detect
```

This will add CF metadata to any mods that exist on both platforms.

### Phase 2: Manual Audit (1-2 hours)

For each mod without CF metadata after detect:

1. Search CurseForge manually for the mod
2. If found: Add CF metadata manually to .pw.toml
3. If not found: Check approved non-CF list
4. If approved: Mark for overrides bundle
5. If neither: Check license and submit approval request

### Phase 3: Approval Requests (2-3 days wait)

For mods not on CurseForge AND not on approved list:

1. Verify license is MIT, GPL, Apache, or similar permissive license
2. Submit via [CurseForge approval form](https://forms.monday.com/forms/a46faa60c3d9cf097763311811db5bbd)
3. Wait for approval (typically 3-5 business days)

### Phase 4: Export & Test

```bash
# Export CurseForge version
packwiz curseforge export -o TBA-curseforge.zip

# Verify structure
unzip -l TBA-curseforge.zip
# Should show:
# - manifest.json (with CF mod references)
# - overrides/mods/ (only approved non-CF mods)
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Mod not approved | Low | High | Find CurseForge alternative |
| Approval denied | Very Low | Medium | Contact mod author directly |
| Version mismatch | Medium | Low | Use packwiz curseforge detect |
| Review rejection | Low | Medium | Follow submission guidelines exactly |

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Automated detect | 30 min | None |
| Manual audit | 1-2 hours | Phase 1 complete |
| Approval requests | 3-5 days | Phase 2 complete |
| Export & test | 1 hour | Phase 3 complete |
| CurseForge submission | 1-3 days | Export ready |

**Total estimated time:** 1-2 weeks (mostly waiting for approvals)

---

## Recommended Alternatives (If Needed)

| If This Mod Blocked | Consider This Alternative |
|---------------------|---------------------------|
| Polymer | May not need if no server-side polymer mods |
| Minescript | ComputerCraft or scripting datapack |
| AutoWhitelist | Manual whitelist management |
| Fabric Seasons | Serene Seasons (if on CF) |

---

## Notes

1. **Farmer's Delight Refabricated** vs **Farmer's Delight**: The original is on CurseForge, but you're using the Fabric port. Check if the original supports Fabric 1.21.1 or if Refabricated is on CF.

2. **Axiom**: This is a premium/paid mod. Verify its CurseForge distribution terms.

3. **WATERMeDIA family**: The approved list shows "watermine" by SrRapero720 - this may cover the WATER* mods.

4. **Let's Do series**: These are popular mods, likely on CurseForge but verify 1.21.1 Fabric versions.

---

*Generated for The Block Academy modpack CurseForge compatibility assessment*
