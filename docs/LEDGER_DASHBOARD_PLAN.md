# Ledger Dashboard - Implementation Plan

A web-based admin dashboard for viewing and managing Ledger block logging data from the TBA Minecraft server.

## Overview

Ledger is a server-side Fabric mod that logs player actions (block placement/breaking, item transfers, entity kills, etc.) to a SQLite database. Currently, the only interface is in-game commands (`/ledger search`, `/ledger inspect`, etc.).

This project creates a web dashboard to provide:
- Better search and filtering capabilities
- Visual analytics (charts, heatmaps, timelines)
- Player activity auditing
- Eventually, remote admin actions (rollback/restore)

## Current State

**Database Location:** `/world/ledger.sqlite` on Bloom.host production server

**Schema:**
```
actions (main table)
├── id              INTEGER [PK]
├── time            TEXT (ISO timestamp)
├── action_id       → ActionIdentifiers (block-place, block-break, etc.)
├── player_id       → players (nullable - NULL for environmental)
├── source          → sources (player, lava, gravity, etc.)
├── world_id        → worlds (overworld, nether, end)
├── object_id       → ObjectIdentifiers (minecraft:stone, etc.)
├── old_object_id   → ObjectIdentifiers (previous state)
├── x, y, z         INT (coordinates)
├── block_state     TEXT (NBT-like state data)
├── old_block_state TEXT
├── extra_data      TEXT
└── rolled_back     BOOLEAN

Lookup Tables:
├── ActionIdentifiers (9 action types)
├── players (UUID, name, first/last join)
├── worlds (3 dimensions)
├── sources (21 environmental causes)
└── ObjectIdentifiers (15,000+ blocks/items/entities)
```

**Current Stats (as of Jan 2026):**
- ~31,000 logged actions
- ~6.4 MB database size
- 7 players tracked
- 5 days of data

---

## Implementation Phases

### Phase 1: Read-Only Dashboard

**Goal:** Provide visibility into server activity without modifying anything.

#### 1.1 Data Sync Pipeline

Sync the SQLite database from production to a location accessible by the web app.

**Option A: GitHub Actions (Recommended)**
```yaml
# .github/workflows/ledger-sync.yml
name: Sync Ledger Database
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:        # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download ledger.sqlite via SFTP
        uses: wangyucode/sftp-upload-action@v2.0.2
        with:
          host: ${{ secrets.SFTP_HOST }}
          port: ${{ secrets.SFTP_PORT }}
          username: ${{ secrets.SFTP_USERNAME }}
          password: ${{ secrets.SFTP_PASSWORD }}
          localDir: ./data/
          remoteDir: /world/
          download: true
          include: 'ledger.sqlite'

      - name: Upload to DigitalOcean Spaces
        uses: BetaHuhn/do-spaces-action@v2
        with:
          access_key: ${{ secrets.DO_SPACES_ACCESS_KEY }}
          secret_key: ${{ secrets.DO_SPACES_SECRET_KEY }}
          space_name: ${{ secrets.DO_SPACES_BUCKET }}
          space_region: nyc3
          source: data/ledger.sqlite
          out_dir: ledger/
```

**Storage Options:**
| Option | Pros | Cons |
|--------|------|------|
| DigitalOcean Spaces | Already used for backups, CDN | Extra cost |
| GitHub Release artifact | Free, versioned | 100MB limit |
| Direct to backend server | Simplest | Larger app footprint |

#### 1.2 Backend API

Express.js API to query the synced SQLite database.

**Endpoints:**
```
GET /api/ledger/actions
  ?player=<name>           Filter by player
  ?action=<type>           Filter by action type (block-break, etc.)
  ?object=<id>             Filter by block/item
  ?world=<dimension>       Filter by dimension
  ?after=<timestamp>       After date
  ?before=<timestamp>      Before date
  ?x=<n>&y=<n>&z=<n>       Exact coordinates
  ?range=<n>               Radius around coordinates
  ?page=<n>&limit=<n>      Pagination
  ?sort=<field>&order=asc|desc

GET /api/ledger/actions/:id
  Full details for a single action

GET /api/ledger/players
  List all players with action counts

GET /api/ledger/players/:name
  Player details with recent activity

GET /api/ledger/stats
  Aggregate statistics (actions/day, top players, etc.)

GET /api/ledger/stats/timeline
  Actions over time for charting

GET /api/ledger/objects
  Most common objects interacted with
```

**Tech Stack:**
- Express.js (matches minecraftcollege backend)
- better-sqlite3 (fast synchronous SQLite for Node.js)
- Node.js 18+

#### 1.3 Frontend UI

React dashboard with the following views:

**Activity Feed**
- Real-time-ish scrolling feed of recent actions
- Color-coded by action type
- Click to expand details
- Filter bar at top

**Search**
- Advanced search form with all filter options
- Results table with sorting
- Export to CSV
- Pagination

**Player Profiles**
- List of all players
- Click into player detail:
  - Total actions by type (pie chart)
  - Activity timeline (line chart)
  - Recent actions list
  - First/last seen dates

**Analytics Dashboard**
- Actions per day (bar chart)
- Actions by type (pie chart)
- Most active players (leaderboard)
- Most modified blocks (top 10)
- Heatmap of activity by hour/day (optional)

**Map View (Stretch Goal)**
- 2D top-down view showing action locations
- Color-coded dots by action type
- Filter by time range
- Click dot for details

**Tech Stack:**
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui (matches minecraftcollege)
- Recharts or Chart.js for visualizations
- TanStack Query for data fetching
- React Router for navigation

#### 1.4 Deployment

**Option A: Extend minecraftcollege**
- Add `/ledger` routes to existing app
- Share authentication (if added later)
- Single deployment

**Option B: Standalone App (Recommended for Phase 1)**
- Separate repo: `mindfulent/ledger-dashboard`
- Deploy to DigitalOcean App Platform
- Can move fast without affecting main site

**Infrastructure:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Bloom.host     │     │ GitHub Actions  │     │ DO App Platform │
│  /world/        │────▶│ (every 6 hours) │────▶│ ledger-dashboard│
│  ledger.sqlite  │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     │ ┌─────────────┐ │
                                                │ │ Frontend    │ │
                                                │ │ React SPA   │ │
                                                │ └─────────────┘ │
                                                │ ┌─────────────┐ │
                                                │ │ Backend     │ │
                                                │ │ Express API │ │
                                                │ │ + SQLite    │ │
                                                │ └─────────────┘ │
                                                └─────────────────┘
```

---

### Phase 2: Live Connection

**Goal:** Query production database in real-time instead of periodic sync.

#### 2.1 On-Demand Refresh

Add a "Refresh" button that triggers an immediate sync:

```
POST /api/ledger/sync
  - Downloads fresh ledger.sqlite via SFTP
  - Replaces local copy
  - Returns new stats
```

**Implementation:**
```javascript
// Backend: SFTP download on-demand
const Client = require('ssh2-sftp-client');

async function syncLedgerDatabase() {
  const sftp = new Client();
  await sftp.connect({
    host: process.env.SFTP_HOST,
    port: process.env.SFTP_PORT,
    username: process.env.SFTP_USERNAME,
    password: process.env.SFTP_PASSWORD
  });

  await sftp.fastGet('/world/ledger.sqlite', './data/ledger.sqlite');
  await sftp.end();

  // Reopen database connection
  reopenDatabase();
}
```

**Rate Limiting:**
- Max 1 sync per 5 minutes
- Show "last synced" timestamp in UI
- Auto-sync on first load if data > 1 hour old

#### 2.2 WebSocket Updates (Optional)

For true real-time updates, we'd need a component on the server. Since Ledger doesn't expose an API, options are:

1. **Poll-based pseudo-realtime**: Sync every 60 seconds when dashboard is open
2. **File watcher on server**: Not practical without server-side code
3. **Ledger extension**: Write a Fabric mod that pushes events (complex)

**Recommendation:** Stick with on-demand refresh + auto-refresh every 5 minutes when dashboard is active.

#### 2.3 Direct Database Queries

If SFTP download becomes a bottleneck (large database), consider:

**Option A: SQLite on Spaces with SQL.js**
- Store SQLite on DO Spaces
- Load into browser with SQL.js (WebAssembly SQLite)
- Query client-side
- Pro: No backend needed for queries
- Con: Downloads entire DB to browser

**Option B: Read Replica**
- Set up PostgreSQL on DigitalOcean
- Sync Ledger SQLite → PostgreSQL periodically
- Query PostgreSQL from backend
- Pro: Scales better, supports concurrent queries
- Con: More infrastructure

---

### Phase 3: Full Admin Panel

**Goal:** Perform admin actions (rollback, restore, purge) from the web.

#### 3.1 Authentication

Add admin authentication before enabling write operations.

**Options:**
| Method | Pros | Cons |
|--------|------|------|
| Discord OAuth | Players already on Discord | Need to map to MC accounts |
| Simple password | Easy to implement | Shared credential |
| GitHub OAuth | Admins have GitHub | Extra step |

**Recommendation:** Discord OAuth with role-based access:
- `@Admin` role → Full access (rollback, purge)
- `@Moderator` role → View + search only
- Public → No access (or limited read-only)

#### 3.2 RCON Integration

Ledger commands must be run in-game or via server console. Use RCON to send commands.

**Note:** Bloom.host Pterodactyl panel exposes console commands via API, which we already use in `server-config.py`.

```javascript
// Send command via Pterodactyl API
async function sendServerCommand(command) {
  const response = await fetch(
    `${PTERODACTYL_URL}/api/client/servers/${SERVER_ID}/command`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ command })
    }
  );
  return response.ok;
}

// Example: Rollback player actions
await sendServerCommand('ledger rollback source:GrieferName after:1h');
```

#### 3.3 Admin Actions

**Preview Rollback**
1. User selects filters (player, time range, area)
2. Backend queries database for matching actions
3. Display preview: "X blocks will be restored"
4. User confirms
5. Backend sends `/ledger rollback` command via RCON

**Restore**
- Same flow as rollback, but for previously rolled-back actions

**Purge**
- Delete old records from database
- Requires highest permission level
- Confirmation with "type to confirm" pattern

#### 3.4 Audit Log

Track all admin actions:
```sql
CREATE TABLE admin_actions (
  id INTEGER PRIMARY KEY,
  timestamp TEXT,
  admin_discord_id TEXT,
  admin_name TEXT,
  action_type TEXT,  -- 'rollback', 'restore', 'purge'
  parameters TEXT,   -- JSON of filters used
  affected_count INTEGER,
  status TEXT        -- 'success', 'failed'
);
```

#### 3.5 Alerts & Notifications

**Discord Webhook Integration:**
- Alert on suspicious activity patterns
- Notify when rollback is performed
- Daily/weekly summary reports

**Example Alert Rules:**
- Player breaks > 100 blocks in 5 minutes
- Diamond ore broken (track rare blocks)
- Actions near protected areas
- New player breaks blocks within 10 minutes of joining

---

## Technical Decisions

### Repository Structure

**Option A: Monorepo in TBA**
```
TBA/
├── dashboard/
│   ├── frontend/
│   └── backend/
├── config/
├── mods/
└── ...
```

**Option B: Separate Repository (Recommended)**
```
ledger-dashboard/
├── frontend/          # React app
├── backend/           # Express API
├── scripts/           # Sync scripts
├── .github/workflows/ # GitHub Actions
└── ...
```

Separate repo keeps concerns isolated and allows independent deployment.

### Database Considerations

**SQLite Limitations:**
- Single-writer (not an issue for read-only)
- File-based (needs sync mechanism)
- No built-in replication

**When to Migrate to PostgreSQL:**
- Database exceeds 100MB
- Need concurrent write access
- Want real-time sync via logical replication

### Security

- Never expose raw database file publicly
- API should sanitize all query parameters
- Admin actions require authentication
- Rate limit all endpoints
- Log all access for audit

---

## Timeline Estimate

| Phase | Scope | Effort |
|-------|-------|--------|
| Phase 1.1 | Data sync pipeline | 2-3 hours |
| Phase 1.2 | Backend API | 4-6 hours |
| Phase 1.3 | Frontend UI (basic) | 8-12 hours |
| Phase 1.4 | Deployment | 2-3 hours |
| **Phase 1 Total** | **Read-only dashboard** | **~20 hours** |
| Phase 2.1 | On-demand refresh | 2-3 hours |
| Phase 2.2 | Auto-refresh | 1-2 hours |
| **Phase 2 Total** | **Live connection** | **~5 hours** |
| Phase 3.1 | Authentication | 4-6 hours |
| Phase 3.2 | RCON integration | 3-4 hours |
| Phase 3.3 | Admin actions UI | 6-8 hours |
| Phase 3.4 | Audit logging | 2-3 hours |
| Phase 3.5 | Alerts | 4-6 hours |
| **Phase 3 Total** | **Full admin panel** | **~25 hours** |

**Grand Total: ~50 hours**

---

## Next Steps

1. **Create repository**: `mindfulent/ledger-dashboard`
2. **Set up project structure**: Vite + React frontend, Express backend
3. **Implement sync pipeline**: GitHub Action to download SQLite
4. **Build basic API**: `/actions`, `/players`, `/stats` endpoints
5. **Create UI**: Activity feed and search page
6. **Deploy**: DigitalOcean App Platform
7. **Iterate**: Add features based on usage

---

## Appendix: Ledger Commands Reference

For Phase 3 RCON integration:

```
/ledger search <params>     Search actions
/ledger inspect             Toggle inspect mode
/ledger rollback <params>   Undo actions
/ledger restore <params>    Redo rolled-back actions
/ledger preview rollback    Preview rollback
/ledger preview restore     Preview restore
/ledger preview apply       Apply preview
/ledger preview cancel      Cancel preview
/ledger purge <params>      Delete records

Parameters:
  source:<player>           Player name
  action:<type>             block-break, block-place, etc.
  object:<id>               minecraft:stone, etc.
  world:<dimension>         minecraft:overworld, etc.
  range:<n>                 Radius from current position
  range:@global             All locations
  before:<time>             Before duration (1d, 2h, etc.)
  after:<time>              After duration
  rolledback:true|false     Filter by rollback status
```
