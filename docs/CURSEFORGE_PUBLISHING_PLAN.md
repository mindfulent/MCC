# TBA CurseForge Publishing Plan

**Goal:** Publish TBA modpack to CurseForge for broader distribution
**Current Version:** 0.9.36 (87 mods)

---

## Executive Summary

TBA is currently distributed via GitHub releases for Modrinth/Prism Launcher users. Publishing to CurseForge will:
- Reach the larger CurseForge user base
- Enable one-click installs via CurseForge App
- Potentially generate CurseForge Rewards points

**Compatibility Assessment:** ~75% of mods are ready. Main work is verification and 3-5 approval requests.

---

## Phase 1: Automated Detection

**Goal:** Identify which mods have CurseForge equivalents

### Steps

```bash
cd /c/Users/slash/Projects/TBA

# Run CurseForge detection
./packwiz.exe curseforge detect

# Review changes
git diff mods/
```

### Expected Outcome

Packwiz will add `[update.curseforge]` sections to mods that exist on both platforms. This gives us a concrete count of:
- Mods with CF metadata (ready)
- Mods without CF metadata (need manual action)

### Verification

```bash
# Count mods with CF metadata
grep -l "update.curseforge" mods/*.pw.toml | wc -l

# Count mods without CF metadata
grep -L "update.curseforge" mods/*.pw.toml | wc -l
```

---

## Phase 2: Manual Audit

**Goal:** Categorize remaining mods and identify blockers

### 2.1 Run Compatibility Analyzer

```bash
python docs/files/check_cf_compatibility.py .
```

### 2.2 Manual CurseForge Search

For each mod without CF metadata, search CurseForge manually:
1. Go to https://www.curseforge.com/minecraft/mc-mods
2. Search for mod name
3. Filter: Game Version = 1.21.1, Mod Loader = Fabric
4. If found: Note the project ID and file ID

### 2.3 Categorize Results

Create a tracking spreadsheet or update this document:

| Mod | Status | Action | Notes |
|-----|--------|--------|-------|
| Example Mod | On CF | Add metadata | Project ID: 12345 |
| Example Mod 2 | Approved List | Bundle in overrides | LGPL license |
| Example Mod 3 | Not Found | Submit approval | MIT license |
| Example Mod 4 | Not Found | Omit from CF version | Niche feature |

### 2.4 Check Approved Non-CF List

Reference the official CurseForge approved mods spreadsheet:
https://docs.google.com/spreadsheets/d/176Wv-PZUo0hFxy6oC6N8tWdquBLPRtSuLbNK-r0_byM

Mods on this list can be bundled directly in the `overrides/mods/` folder.

---

## Phase 3: Handle Blockers

**Goal:** Resolve mods not on CF or approved list

### 3.1 Decision Framework

For each blocker, decide:

```
Is the mod essential for the pack's identity?
├─ YES → Is the license permissive (MIT, GPL, Apache, LGPL)?
│        ├─ YES → Submit approval request
│        └─ NO → Find alternative or contact author
└─ NO → Omit from CurseForge version
```

### 3.2 Known Blockers & Recommendations

| Mod | License | Recommendation |
|-----|---------|----------------|
| **Polymer** | MIT | Check if required by other mods. If not, omit. |
| **Minescript** | MIT | Omit - power-user feature, not core experience |
| **AutoWhitelist** | MIT | Omit - server-side only, not needed in client pack |
| **Gamemode Unrestrictor** | Check | Submit approval if MIT, else omit |
| **WindChime Unofficial** | Check | Risky - "unofficial" may have IP issues. Find original or omit. |
| **Camerapture** | Check | Likely on CF, verify |
| **Joy of Painting** | Check | Likely on CF, verify |

### 3.3 Submit Approval Requests

For mods requiring approval:

1. Verify the mod's license is permissive
2. Go to: https://forms.monday.com/forms/a46faa60c3d9cf097763311811db5bbd
3. Submit with:
   - Mod name and Modrinth link
   - License type
   - Brief justification

### 3.4 Track Approvals

| Mod | Submitted | Status | Approved Date |
|-----|-----------|--------|---------------|
| | | | |

---

## Phase 4: Dual-Export Strategy

**Goal:** Set up parallel Modrinth and CurseForge exports

### 4.1 Create CF-Specific Ignore File

Create `.packwizignore-curseforge` for mods to exclude from CF build:

```
# Mods excluded from CurseForge version
mods/minescript.pw.toml
mods/autowhitelist.pw.toml
mods/polymer.pw.toml
# Add other CF-incompatible mods
```

### 4.2 Export Scripts

Add to `server-config.py` or create `export.py`:

```python
# Modrinth export (full pack)
./packwiz.exe modrinth export

# CurseForge export (CF-compatible subset)
# Option 1: Use packwiz side system
# Option 2: Temporarily remove incompatible mods, export, restore
```

### 4.3 Alternative: Use Mod Side System

In each CF-incompatible mod's `.pw.toml`:

```toml
side = "server"  # Won't be included in client packs
```

Or create a custom metadata field and filter during export.

---

## Phase 5: CurseForge Submission

**Goal:** Submit modpack to CurseForge

### 5.1 Prerequisites

- [ ] CurseForge account created
- [ ] Author profile completed
- [ ] Agreed to CurseForge distribution terms

### 5.2 Create Project

1. Go to https://www.curseforge.com/project/create
2. Select: Modpacks → Minecraft
3. Fill in:
   - **Name:** TBA (TheBlock.Academy)
   - **Summary:** Curated Fabric 1.21.1 modpack for building, performance, and multiplayer
   - **Description:** (Use README.md content, adapted for CF formatting)
   - **Categories:** Building, Multiplayer, Performance
   - **License:** Custom (link to your LICENSE)

### 5.3 Export and Upload

```bash
# Export CurseForge format
./packwiz.exe curseforge export -o TBA-0.9.36-curseforge.zip

# Verify structure
unzip -l TBA-0.9.36-curseforge.zip
# Should contain:
# - manifest.json (mod references)
# - modlist.html (optional)
# - overrides/ (configs, approved non-CF mods)
```

### 5.4 Upload File

1. Go to your project → Files → Upload File
2. Select the .zip file
3. Set:
   - **Release Type:** Release
   - **Game Version:** 1.21.1
   - **Mod Loader:** Fabric
   - **Java Version:** Java 21
4. Add changelog
5. Submit for review

### 5.5 Review Process

CurseForge reviews modpacks for:
- Correct manifest.json format
- All referenced mods exist on CF
- No unauthorized mods in overrides
- No malware/suspicious files

---

## Phase 6: Ongoing Maintenance

### 6.1 Dual Release Workflow

When updating the modpack:

```bash
# 1. Make changes as usual
./packwiz.exe mr install <mod> -y

# 2. Bump version
# Edit pack.toml

# 3. Export both formats
./packwiz.exe modrinth export
./packwiz.exe curseforge export -o TBA-X.Y.Z-curseforge.zip

# 4. Commit and push
git add -A && git commit -m "vX.Y.Z - description" && git push

# 5. Create GitHub release (for Modrinth users)
gh release create vX.Y.Z TBA-X.Y.Z.mrpack --title "vX.Y.Z"

# 6. Update server
python server-config.py update-pack X.Y.Z
python server-config.py restart

# 7. Upload to CurseForge
# Manual upload via CF website
```

### 6.2 New Mod Checklist

When adding new mods, always check:

- [ ] Is it on CurseForge for 1.21.1 Fabric?
- [ ] If not, is it on the approved list?
- [ ] If neither, is it essential? (May need approval request or omit from CF)

### 6.3 Version Sync

Keep versions aligned:
- GitHub Release: `v0.9.37`
- CurseForge File: `0.9.37`
- pack.toml: `version = "0.9.37"`

---

## Appendix A: Key Resources

| Resource | URL |
|----------|-----|
| CurseForge Approved Mods | https://docs.google.com/spreadsheets/d/176Wv-PZUo0hFxy6oC6N8tWdquBLPRtSuLbNK-r0_byM |
| Non-CF Mod Approval Form | https://forms.monday.com/forms/a46faa60c3d9cf097763311811db5bbd |
| Packwiz CurseForge Docs | https://packwiz.infra.link/tutorials/creating/curseforge/ |
| CurseForge Modpack Guide | https://support.curseforge.com/en/support/solutions/articles/9000197913 |

---

## Appendix B: Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mod approval denied | Low | Contact mod author for permission letter |
| CF review rejection | Medium | Follow manifest.json spec exactly |
| Mod removed from CF | Low | Monitor mod status, have alternatives ready |
| Version mismatch | Medium | Use packwiz detect after each CF update |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-27 | Pursue CurseForge publishing | Reach broader audience |
| | | |

---

## Next Steps

1. [ ] Run `packwiz curseforge detect`
2. [ ] Run compatibility analyzer script
3. [ ] Create blocker tracking table
4. [ ] Submit approval requests for essential mods
5. [ ] Set up dual-export workflow
6. [ ] Create CurseForge project page
7. [ ] Upload first CF version
8. [ ] Document in README that CF version exists
