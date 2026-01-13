# The Block Academy Modpack - Development History

**Timeline**: December 29, 2025 - January 9, 2026
**Total Commits**: 53
**Author**: mindfulent (jaedaemon@gmail.com)

This document chronicles the development journey of The Block Academy (formerly Minecraft College) modpack, tracking the evolution from technical challenges to a polished educational Minecraft experience.

---

## Table of Contents

1. [December 29, 2025 - BlueMap ReFramed Battle](#december-29-2025---bluemap-reframed-battle)
2. [December 31, 2025 - The Great Mod Expansion](#december-31-2025---the-great-mod-expansion)
3. [January 1, 2026 - Infrastructure & Server Management](#january-1-2026---infrastructure--server-management)
4. [January 3, 2026 - Polish & Refinement](#january-3-2026---polish--refinement)
5. [January 5, 2026 - The Rebrand](#january-5-2026---the-rebrand)
6. [January 9, 2026 - Planning the Future](#january-9-2026---planning-the-future)
7. [Key Themes](#key-themes)
8. [Lessons Learned](#lessons-learned)

---

## December 29, 2025 - BlueMap ReFramed Battle

**Duration**: 4 hours (11:10 AM - 2:01 PM PST)
**Commits**: 5
**Theme**: Technical problem-solving and mod compatibility

### Morning Session (11:10 AM - 12:15 PM)

The day began with a deep dive into making BlueMap render ReFramed blocks correctly. This would prove to be a challenging technical puzzle requiring multiple iterations.

**11:10 AM** - `8d9ea22` - First attempt
- Fixed model references in blockstates (reframed:block/* instead of reframed:bluemap/block/*)
- Moved models from bluemap/models/block/ to models/block/
- Theory: The bluemap/ subfolder is for blockstate overrides only

**11:34 AM** - `e2320b1` - The critical discovery
- Found the key: BlueMap's override system requires blockstates in `assets/<namespace>/bluemap/blockstates/`
- Renamed pack to zzz-reframed-compat for loading priority
- Added bluemap/blockstates/ folder with all 35 blockstate overrides
- This was the breakthrough moment - the bluemap/ subfolder tells BlueMap to use static models

**11:36 AM** - `ba8f3b9` - Quick documentation update
- Updated guide with critical bluemap/ folder information
- Added troubleshooting section

**12:15 PM** - `1e52f91` - Fixing orientation issues
- Previous attempts used simplified catch-all variants without rotation
- Extracted original ReFramed blockstates and preserved multipart format
- Kept rotation transforms (x, y) and uvlock settings
- All 35 block types now render with correct geometry and orientation

### Afternoon (2:01 PM)

**2:01 PM** - `444f048` - Documenting the journey
- Created comprehensive documentation of all three implementation attempts
- Detailed what worked, what didn't, and why
- Set up future investigation paths

**Key Learning**: Complex mod interactions require systematic debugging and documentation. The solution often lies in understanding the override mechanism deeply.

---

## December 31, 2025 - The Great Mod Expansion

**Duration**: 3 hours (8:19 AM - 11:14 AM PST)
**Commits**: 13
**Theme**: Rapid iteration, mod compatibility testing, crash handling

This day saw aggressive expansion of the modpack, with a pattern of adding features, discovering incompatibilities, and quickly iterating solutions.

### Early Morning (8:19 AM)

**8:19 AM** - `753d1f1` - v0.9.44
- Simple quality-of-life fix: Disabled ReplayMod auto-recording by default
- New players no longer have recording start automatically

### Morning Expansion (9:12 AM - 9:23 AM)

**9:12 AM** - `69eef45` - v0.9.45 - Massive 24-mod addition (117 total)
A bold expansion across multiple categories:
- **Content & Gameplay**: More Delight, Traveler's Backpack, Lootr, Carry On, Sit, Better Climbing, Actually Harvest, Universal Bone Meal
- **Building & Decoration**: Diagonal Walls, Falling Leaves
- **Audio & Immersion**: Sound Physics Remastered, Voice Chat Interaction, Subtle Effects
- **Camera & Animation**: First-person Model, Not Enough Animations, Camera Overhaul, Camera Utils
- **QoL & UI**: Mouse Wheelie, InvMove, Mod Menu
- **Server**: LuckPerms, Connectivity

**9:19 AM** - `16e7e8f` - v0.9.46 (119 total)
- Added AmbientSounds v6.3.1 and Brewin' And Chewin' v4.4.1
- Both Modrinth-only mods (CF versions incompatible)

**9:23 AM** - `53acd86` - Quick fix
- Switched AmbientSounds to CurseForge version for better compatibility
- Reduced CurseForge overrides to just 2 mods

### Mid-Morning Troubleshooting (9:40 AM - 10:05 AM)

**9:40 AM** - `d8da5d3` - v0.9.46 fix (121 total)
- Removed Mouse Wheelie (RecipeBookWidget mixin failure with 1.21.1)
- Added missing dependencies: YACL, playerAnimator, GeckoLib
- **Pattern emerges**: Compatibility issues require quick response

**9:46 AM** - `f21d953` - v0.9.47
- Added Solas Shader v3.1c (fantasy stylized with colored lighting)

**9:55 AM** - `e8f0cf0` - Documentation update
- Fixed instance paths in README
- Added Solas Shader to documentation

**10:05 AM** - `de515c9` - CREDITS.md update
- Updated for v0.9.47, 121 mods
- Documented Mouse Wheelie removal and new dependencies

### Late Morning Experiments (10:36 AM - 11:14 AM)

**10:36 AM** - `31450ca` - v0.9.48 (125 total)
- Added custom content mods: Fox Nap, Creative Block Replacer, Collective, Immersive Paintings
- Focus on user-generated content

**10:44 AM** - `fed506a` - v0.9.49 (124 total)
- Removed Fox Nap (DecoderException on set_creative_mode_slot packet)
- **First crash pattern identified**: Creative mode serialization issues

**10:54 AM** - `9be5e76` - v0.9.50 (126 total)
- Added VinURL v2.2.0 (play audio from URLs on note blocks)
- Added owo-lib dependency
- Added Photon shader v1.2a

**10:58 AM** - `daf56f2` - v0.9.51 (125 total)
- Removed Brewin' And Chewin' (Modrinth-only, was bundled)
- CurseForge export down to 1 override

**11:14 AM** - `bae5385` - v0.9.52 (123 total)
- Removed VinURL and owo-lib
- Same DecoderException crash as Fox Nap
- **Pattern confirmed**: Fabric 1.21 server issue with custom item NBT serialization
- Final count: 120 client mods, 3 server-only

**Key Learning**: Rapid iteration works, but requires systematic testing. Creative mode crashes became a recurring pattern that informed future mod selection.

---

## January 1, 2026 - Infrastructure & Server Management

**Duration**: 5 hours (2:53 PM - 7:39 PM PST)
**Commits**: 4
**Theme**: Building robust server infrastructure and world management tools

This day shifted focus from content to infrastructure, building the foundation for production server management.

### Afternoon Development (2:53 PM - 3:41 PM)

**2:53 PM** - `4e2a7a3` - World sync infrastructure
- Created download-world command for production world synchronization
- Downloads /world, /world_nether, /world_the_end
- Saves to LocalServer/world-production* directories
- Added Rich progress bars for user feedback
- Fixed RichProgressTracker bug (dict instead of list index)
- **Technical win**: Robust local backup system with visual feedback

**3:18 PM** - `f9d33af` - Local server mode switching
- Added menu options for Production/Test mode switching
- CLI commands: local-production, local-test
- Production mode syncs configs from MCC
- Test mode uses superflat/peaceful settings
- **Vision**: Seamless switching between test and production environments

**3:41 PM** - `fcdf7b9` - Architectural decision
- Removed local server commands from main server-config.py
- Moved to LocalServer/server-config.py
- **Separation of concerns**: Local testing infrastructure independent from production management

### Evening Fixes (5:08 PM - 5:39 PM)

**5:08 PM** - `f6cac24` - v0.9.53
- Fixed critical bug: Advanced Backups was using Spigot JAR instead of Fabric JAR
- Spigot version couldn't run on Fabric servers
- Caused silent backup failures
- Set side = "server" correctly
- **Impact**: This may have been causing other issues like Immersive Paintings crash

**5:39 PM** - `782d339` - v0.9.54 (122 total)
- Removed Universal Graves to fix Immersive Paintings creative mode crash
- Players' items now drop normally (vanilla behavior)
- 119 client mods, 3 server-only

**Key Learning**: Infrastructure problems can cascade into mysterious bugs elsewhere. The wrong JAR variant caused silent failures that took time to track down.

---

## January 3, 2026 - Polish & Refinement

**Duration**: 10 hours across the day (7:07 AM - 6:09 PM PST)
**Commits**: 20
**Theme**: Quality of life improvements, configuration optimization, user experience polish

This was the longest and most productive day, focusing on making the pack feel professional and polished.

### Morning - Backup System Enhancement (7:07 AM - 8:00 AM)

**7:07 AM** - `b69e7cc` - Enhanced world sync
- Added world-download/upload commands
- Two-phase upload to minimize downtime:
  - Phase 1 (offline): Critical data (region, entities, poi, data, level.dat)
  - Phase 2 (online): Non-critical data (DistantHorizons, bluemap)
- Improved update-pack to download mrpack from GitHub
- Created docs/BACKUP-STRATEGY.md
- **Vision**: Professional deployment workflow

**7:12 AM** - `a99dd0b` - Menu reorganization
- Renamed "Backup Management" to "Backup & World Sync"
- Prioritized World Sync as primary, Advanced Backups as secondary
- Better user mental model

**7:18 AM** - `0f14a05` - Status visibility
- Added world-status command showing backup age, size, status
- format_size() helper for human-readable sizes
- **UX improvement**: Users can see backup freshness at a glance

**7:34 AM** - `85931b6` - Documentation clarity
- Documented backup preservation in LocalServer production mode
- Explained world-production vs world-local distinction

**7:43 AM** - `e35e285` - Dimension fix
- Fixed reporting to detect DIM-1 (Nether) and DIM1 (The End) inside /world
- Removed confusing messages about world_nether/world_the_end
- **Technical accuracy**: Vanilla stores dimensions inside main world folder

**7:57 AM** - `d2a4dcc` - System documentation
- Documented Fresh World and Vanilla Debug modes
- Fixed dimension paths in documentation

**8:00 AM** - `51c1d80` - Menu improvement
- Replaced pointless "List server files" with "Update Pack"
- Better workflow integration

### Mid-Morning - Configuration Battle (9:44 AM - 11:41 AM)

**9:44 AM** - `6fbbab5` - v0.9.55
- Fixed Litematica/minimap keybind conflict
- Litematica main menu: M → L
- Advancements: L → Unmapped
- **Beginning of keybind saga**

**10:15 AM** - `bdbdf1f` - v0.9.56 - Comprehensive keybind resolution
A massive effort to resolve ALL conflicts:
- Create Waypoint (JourneyMap): B → K
- JourneyMap fullscreen pan: Arrow keys → Unmapped
- Disable Shaders (Iris): K → F12
- Third Person Camera 1/2: F6/F7 → Unmapped
- Camera Utils Zoom: Z → Unmapped
- Toggle Firstperson: F6 → Unmapped
- Cycle Tool: Z → Unmapped

Final clean assignments:
- Z: Just Zoom
- F6: Stable Cam
- F7: Disable Voice Chat
- F11: Toggle Fullscreen
- F12: Disable Shaders
- K: Create Waypoint
- B: Open Backpack

**10:33 AM** - `d5ed061` - v0.9.57 - Audio defaults
Changed sound defaults for new players:
- Weather: 100% → 50%
- Hostile mobs: 100% → 0%
- Friendly mobs: 100% → 0%
- Ambient: 100% → 25%
- **Philosophy**: Peaceful default experience

**11:02 AM** - `4b58e01` - v0.9.58 (121 total)
- Removed Just Zoom (conflicts with other utilities)
- Camera Utils Zoom: Unbound → Z
- Toggle Cinematic Camera: Unbound → F8
- Clean camera key layout: F5/F6/F8/Z

**11:31 AM** - `3239b47` - v0.9.59 (119 total)
- Removed Creative Block Replacer and Collective
- 116 client, 3 server-only

**11:41 AM** - `6ba2f62` - Automation improvement
- Added stale mod cleanup to update-pack command
- Automatically removes old mods from production
- get_expected_mods_from_mrpack() and clean_stale_mods_production()
- **DevOps maturity**: Automated cleanup prevents ghost mods

### Afternoon - Final Expansion (12:11 PM - 6:09 PM)

**12:11 PM** - `48f97b5` - v0.9.60 (124 total)
New additions:
- Accurate Block Placement Reborn - Place blocks in facing direction
- BetterF3 - Enhanced F3 debug screen
- Entity Culling - Performance (skip rendering off-screen entities)
- Genshin Instruments - Playable musical instruments
- Ledger - Server-side block/entity logging (ops only, grief tracking)

**5:19 PM** - `ac9f690` - v0.9.60 revision (126 total)
- Re-added VinURL and owo-lib (willing to test again)
- 123 client, 3 server-only

**5:34 PM** - `2d4a8e3` - Documentation update
- Updated BACKUP-STRATEGY.md for DH-aware world sync
- LocalServer commands as primary
- Cold storage concept for DistantHorizons files

**5:36 PM** - `06022cf` - CREDITS.md update
- Added 7 new mods to credits
- Removed Universal Graves
- Updated to 126 total

**6:09 PM** - `4faf249` - v0.9.61 - Critical server fix
- mrpack4server doesn't support server-overrides folder
- Changed Advanced Backups, AutoWhitelist, Better Sleep, Fabricord from side="server" to side="both"
- **Packaging bug**: Server-only mods weren't installing

**Key Learning**: Polish takes time. Keybind conflicts and audio defaults seem minor but dramatically impact user experience. Automation reduces future maintenance burden.

---

## January 5, 2026 - The Rebrand

**Duration**: 2.5 hours (7:24 AM - 8:58 AM PST)
**Commits**: 6
**Theme**: Identity change from Minecraft College to The Block Academy

A focused morning dedicated to comprehensive rebranding across the entire project.

### Morning Rebrand (7:24 AM - 8:58 AM)

**7:24 AM** - `d4b0083` - Complete rebrand
Systematic updates across all files:
- Core config: pack.toml, modpack-info.json, index.toml
- Assets: mcc_*.png → tba_*.png images
- Documentation: README, CHANGELOG, LICENSE, all docs/*.md
- Server config: server.properties MOTD, server-config.py header
- Renamed setup guide to docs/setup-guide.md
- **Thoroughness**: Every reference updated

**7:28 AM** - `39c4550` - v0.9.62 - Rebrand release
- Version bump to mark the rebrand milestone
- Updated README version and mod count
- Changelog entry

**8:15 AM** - `a1f4226` - Post-rebrand updates
- modpack-info.json updated to v0.9.62 with correct hash
- server-config.py: All remaining MCC → TBA references
- Refreshed hashes from packwiz export

**8:38 AM** - `4368413` - CurseForge compliance
- Switched AutoWhitelist from Modrinth to CurseForge
- CF modpack guidelines: mods on CF must be referenced, not bundled

**8:49 AM** - `481044c` - v0.9.63 - Compliance release
- AutoWhitelist now CurseForge source
- Mods must be in manifest.json, not bundled

**8:58 AM** - `ce5c53f` - Final hash update
- Updated modpack-info.json for v0.9.63

**Key Learning**: Rebranding is more than just name changes - it's about consistency across every user touchpoint. CurseForge compliance requirements matter for distribution.

---

## January 9, 2026 - Planning the Future

**Duration**: 2 hours (2:45 PM - 4:30 PM PST)
**Commits**: 3
**Theme**: Strategic planning for admin tooling and database optimization

After a multi-day break, work resumed with focus on future features and optimization.

### Afternoon Planning (2:45 PM - 4:30 PM)

**2:45 PM** - `9c2d7fb` - Ledger optimization
- Added config with source blacklist
- Blacklisted noisy environmental events: melt, gravity, trample
- These accounted for ~75% of logged actions
- **Performance**: Reduce database bloat

**2:54 PM** - `dda2ef6` - Ledger Dashboard plan
Initial planning document for web-based admin dashboard:
- Three-phase plan:
  - Phase 1: Read-only dashboard with periodic SQLite sync
  - Phase 2: Live connection with on-demand refresh
  - Phase 3: Full admin panel with RCON integration
- Includes architecture, API design, UI mockups
- Timeline estimates for phased approach

**4:30 PM** - `e43c44d` - Revised integration plan
Strategic pivot:
- Integrate into existing theblockacademy app instead of standalone
- Reuse Microsoft OAuth + admin system (no new auth)
- Copy data sync patterns from stats-exporter.py and backup-sync.py
- Add /ledger routes to Express backend
- Add /admin/ledger pages to frontend
- **Architecture**: Leverage existing infrastructure rather than rebuild

**Key Learning**: Planning before implementation saves time. Integrating with existing systems reduces complexity and leverages previous work.

---

## Key Themes

### 1. Iterative Problem-Solving
The BlueMap ReFramed saga (Dec 29) exemplifies the development approach: try, document, refine, succeed. Five commits over four hours to solve one technical challenge.

### 2. Rapid Experimentation
December 31 shows aggressive feature addition with quick rollback when issues arise. 13 commits in 3 hours, adding/removing 15+ mods based on compatibility testing.

### 3. Infrastructure Investment
January 1-3 shifts focus from content to tooling. World sync, backup strategies, deployment automation - building the foundation for reliable operations.

### 4. User Experience Focus
January 3's keybind resolution and audio defaults show attention to the new user experience. Making the pack "just work" out of the box.

### 5. Professional Polish
From documentation to automated cleanup to comprehensive rebranding, the project shows maturation from prototype to polished product.

### 6. Strategic Planning
January 9 demonstrates learning: plan integration with existing systems rather than building from scratch.

---

## Lessons Learned

### Technical Lessons

1. **Compatibility Testing is Critical**: The pattern of add→crash→remove (Fox Nap, VinURL, Mouse Wheelie) shows the importance of testing mods in creative mode with custom NBT data.

2. **Infrastructure Bugs Cascade**: The Advanced Backups Spigot JAR issue likely caused multiple mysterious problems before being identified.

3. **Override Mechanisms Matter**: BlueMap required specific folder structures (`bluemap/blockstates/`) - reading the documentation deeply saves time.

4. **Server vs Client Side Matters**: mrpack4server's limitations with server-overrides required changing mod side declarations.

### Development Practices

1. **Document Failures**: The BlueMap implementation attempts document shows the value of recording what doesn't work.

2. **Automation Reduces Future Pain**: Stale mod cleanup automation prevents production drift.

3. **Separation of Concerns**: Splitting LocalServer and production infrastructure made both clearer.

4. **Small, Focused Commits**: Most commits address one specific issue, making history readable and bisectable.

### Project Management

1. **Rebrand Comprehensively**: The systematic January 5 rebrand touched every reference point - thoroughness matters.

2. **Polish Takes Time**: January 3's 10-hour day polishing keybinds and audio seems excessive but creates a professional experience.

3. **Leverage Existing Systems**: The revised Ledger Dashboard plan shows maturity - integrate rather than rebuild.

4. **Version Bumps Tell Stories**: Each version number marks a chapter - v0.9.44 to v0.9.63 in two weeks shows rapid iteration.

---

## Statistics

- **Total Timeline**: 12 days (Dec 29, 2025 - Jan 9, 2026)
- **Active Development Days**: 6 days
- **Total Commits**: 53
- **Version Progression**: v0.9.44 → v0.9.63 (19 versions)
- **Peak Commit Day**: January 3 (20 commits)
- **Longest Session**: January 3 (10 hours)
- **Mod Count Evolution**: 117 → 126 → 119 (final: 116 client, 3 server)
- **Documentation Added**: 2 major docs (BACKUP-STRATEGY.md, implementation plans)
- **Mods Added Then Removed**: 7 (Fox Nap, Brewin' And Chewin', VinURL, owo-lib, Mouse Wheelie, Creative Block Replacer, Universal Graves, Collective)
- **Critical Bugs Fixed**: 3 (Advanced Backups JAR, server-side mod installation, dimension reporting)

---

## The Story Arc

**Act 1 - Technical Mastery (Dec 29)**: The journey begins with deep technical problem-solving, learning override systems and blockstate mechanics.

**Act 2 - Rapid Expansion (Dec 31)**: Aggressive feature addition, learning through failure, establishing the mod selection criteria.

**Act 3 - Infrastructure (Jan 1)**: Stepping back from content to build robust operational tooling.

**Act 4 - Polish (Jan 3)**: The longest day, dedicated to making everything feel professional and cohesive.

**Act 5 - Identity (Jan 5)**: Establishing the brand and compliance for public distribution.

**Act 6 - Vision (Jan 9)**: Planning the future with strategic integration approaches.

The Block Academy modpack emerged from iterative refinement, technical problem-solving, and user-focused polish. From 117 mods to 119, through extensive testing and optimization, to a professional educational Minecraft experience ready for The Block Academy community.
