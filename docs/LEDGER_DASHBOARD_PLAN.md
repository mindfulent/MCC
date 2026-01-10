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

## Strategic Decision: Integrate with theblockacademy

After analyzing `theblockacademy`, the recommended approach is to **integrate the Ledger Dashboard into the existing app** rather than creating a standalone project.

### Why Integration Makes Sense

| Aspect | Standalone | Integrated (Recommended) |
|--------|------------|--------------------------|
| **Authentication** | Build from scratch (Discord OAuth) | Already have Microsoft OAuth + `is_admin` flag |
| **Data Sync** | New GitHub Actions workflow | Copy existing pattern from `stats-exporter.py` |
| **Backend** | New Express app | Add routes to existing Express API |
| **Frontend** | New React app | Add pages to existing React app (same stack) |
| **Deployment** | New DO App Platform app | Already deployed, just add routes |
| **Styling** | Recreate design system | Reuse Tailwind + shadcn/ui + theme |
| **Maintenance** | Two codebases | One codebase |

### What theblockacademy Already Has

**Data Sync Infrastructure:**
- `scripts/stats-exporter.py` - Syncs player stats every 15 minutes via Pterodactyl API
- `scripts/backup-sync.py` - Syncs backups every 6 hours to DO Spaces
- GitHub Actions workflows with all required secrets already configured

**Authentication System:**
- Microsoft OAuth (personal accounts) with Xbox/Minecraft verification
- Three permission levels: Authenticated → Allowlisted → Admin
- `is_admin` flag on users table
- Admin middleware: `backend/src/middleware/admin.ts`
- Cross-domain session handling (minecraftcollege.com ↔ theblock.academy)

**Admin Infrastructure:**
- Admin routes: `backend/src/routes/admin.ts`
- Admin page: `src/pages/Admin.tsx`
- Protected route component: `src/components/auth/ProtectedRoute.tsx`
- Auth context with `isAdmin` flag

**Tech Stack (matches our plan):**
- Express.js backend with PostgreSQL
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui
- TanStack React Query
- Deployed on DigitalOcean App Platform

---

## Revised Implementation Phases

### Phase 1: Read-Only Dashboard (Integrated)

**Goal:** Add Ledger visibility to theblockacademy's admin section.

#### 1.1 Data Sync Pipeline

Add a new script following the `stats-exporter.py` pattern.

**New File:** `theblockacademy/scripts/ledger-sync.py`
```python
#!/usr/bin/env python3
"""
Sync Ledger SQLite database from Minecraft server to DigitalOcean Spaces.
Runs every 6 hours via GitHub Actions.
"""

import os
import boto3
from botocore.config import Config
import paramiko
from datetime import datetime

def download_ledger_via_sftp():
    """Download ledger.sqlite from Bloom.host via SFTP."""
    transport = paramiko.Transport((
        os.environ['PTERODACTYL_SFTP_HOST'],
        int(os.environ.get('PTERODACTYL_SFTP_PORT', 2022))
    ))
    transport.connect(
        username=os.environ['PTERODACTYL_SFTP_USERNAME'],
        password=os.environ['PTERODACTYL_SFTP_PASSWORD']
    )
    sftp = paramiko.SFTPClient.from_transport(transport)

    local_path = '/tmp/ledger.sqlite'
    sftp.get('/world/ledger.sqlite', local_path)
    sftp.close()
    transport.close()

    return local_path

def upload_to_spaces(local_path):
    """Upload to DigitalOcean Spaces."""
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ['DO_SPACES_URL'],
        aws_access_key_id=os.environ['DO_SPACES_KEY'],
        aws_secret_access_key=os.environ['DO_SPACES_SECRET'],
        config=Config(signature_version='s3v4')
    )

    s3.upload_file(
        local_path,
        os.environ['DO_SPACES_BUCKET'],
        'ledger/ledger.sqlite',
        ExtraArgs={'ACL': 'private'}  # Not public!
    )

    # Also upload timestamp file
    s3.put_object(
        Bucket=os.environ['DO_SPACES_BUCKET'],
        Key='ledger/last-sync.txt',
        Body=datetime.utcnow().isoformat(),
        ACL='private'
    )

if __name__ == '__main__':
    print(f"[{datetime.now()}] Starting Ledger sync...")
    local_path = download_ledger_via_sftp()
    print(f"Downloaded ledger.sqlite ({os.path.getsize(local_path)} bytes)")
    upload_to_spaces(local_path)
    print("Uploaded to DigitalOcean Spaces")
```

**New Workflow:** `theblockacademy/.github/workflows/sync-ledger.yml`
```yaml
name: Sync Ledger Database
on:
  schedule:
    - cron: '30 */6 * * *'  # Every 6 hours, offset from backups
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install paramiko boto3

      - name: Sync Ledger database
        env:
          PTERODACTYL_SFTP_HOST: ${{ secrets.PTERODACTYL_SFTP_HOST }}
          PTERODACTYL_SFTP_PORT: ${{ secrets.PTERODACTYL_SFTP_PORT }}
          PTERODACTYL_SFTP_USERNAME: ${{ secrets.PTERODACTYL_SFTP_USERNAME }}
          PTERODACTYL_SFTP_PASSWORD: ${{ secrets.PTERODACTYL_SFTP_PASSWORD }}
          DO_SPACES_URL: ${{ secrets.DO_SPACES_URL }}
          DO_SPACES_BUCKET: ${{ secrets.DO_SPACES_BUCKET }}
          DO_SPACES_KEY: ${{ secrets.DO_SPACES_KEY }}
          DO_SPACES_SECRET: ${{ secrets.DO_SPACES_SECRET }}
        run: python scripts/ledger-sync.py
```

**Note:** May need to add SFTP-specific secrets if different from Pterodactyl API credentials.

#### 1.2 Backend API

Add new routes to theblockacademy's Express backend.

**New File:** `theblockacademy/backend/src/routes/ledger.ts`
```typescript
import { Router } from 'express';
import { requireAuth, requireAdmin } from '../middleware/auth';
import { getLedgerDatabase } from '../services/ledger-db';

const router = Router();

// All ledger routes require admin
router.use(requireAuth, requireAdmin);

// GET /ledger/actions - List actions with filters
router.get('/actions', async (req, res) => {
  const db = await getLedgerDatabase();
  const { player, action, object, world, after, before, page = 1, limit = 50 } = req.query;
  // Build query with filters...
  // Return paginated results
});

// GET /ledger/players - List all players with stats
router.get('/players', async (req, res) => {
  const db = await getLedgerDatabase();
  // Query players table with action counts
});

// GET /ledger/stats - Aggregate statistics
router.get('/stats', async (req, res) => {
  const db = await getLedgerDatabase();
  // Return counts by action type, time series data, etc.
});

// POST /ledger/sync - Trigger manual sync (rate-limited)
router.post('/sync', async (req, res) => {
  // Check last sync time, download fresh copy if allowed
});

export default router;
```

**New Service:** `theblockacademy/backend/src/services/ledger-db.ts`
```typescript
import Database from 'better-sqlite3';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';

let db: Database.Database | null = null;
let lastDownload: Date | null = null;

export async function getLedgerDatabase(): Promise<Database.Database> {
  // Download from Spaces if not cached or stale (> 1 hour)
  const now = new Date();
  if (!db || !lastDownload || (now.getTime() - lastDownload.getTime() > 3600000)) {
    await downloadFromSpaces();
    db = new Database('./data/ledger.sqlite', { readonly: true });
    lastDownload = now;
  }
  return db;
}

async function downloadFromSpaces() {
  const s3 = new S3Client({
    endpoint: process.env.DO_SPACES_URL,
    region: 'nyc3',
    credentials: {
      accessKeyId: process.env.DO_SPACES_KEY!,
      secretAccessKey: process.env.DO_SPACES_SECRET!,
    },
  });

  const response = await s3.send(new GetObjectCommand({
    Bucket: process.env.DO_SPACES_BUCKET!,
    Key: 'ledger/ledger.sqlite',
  }));

  await pipeline(
    response.Body as NodeJS.ReadableStream,
    createWriteStream('./data/ledger.sqlite')
  );
}
```

**Mount in backend/src/index.ts:**
```typescript
import ledgerRouter from './routes/ledger';
// ...
app.use('/ledger', ledgerRouter);
```

#### 1.3 Frontend UI

Add new pages to theblockacademy's React frontend.

**New Pages:**
```
src/pages/admin/
├── Ledger.tsx           # Main dashboard (activity feed + stats)
├── LedgerSearch.tsx     # Advanced search with filters
├── LedgerPlayer.tsx     # Player detail view
└── LedgerAnalytics.tsx  # Charts and visualizations
```

**Route Updates in App.tsx:**
```tsx
// Add to admin routes
<Route path="/:lang/admin/ledger" element={
  <ProtectedRoute requireAdmin>
    <Ledger />
  </ProtectedRoute>
} />
<Route path="/:lang/admin/ledger/search" element={
  <ProtectedRoute requireAdmin>
    <LedgerSearch />
  </ProtectedRoute>
} />
<Route path="/:lang/admin/ledger/player/:name" element={
  <ProtectedRoute requireAdmin>
    <LedgerPlayer />
  </ProtectedRoute>
} />
```

**Navigation Update:**
Add "Ledger" link to admin sidebar/navigation.

**Component Reuse:**
- Use existing `Card`, `Table`, `Button` from shadcn/ui
- Use existing color scheme (`ice`, `frost`, `night-sky`)
- Add Recharts for visualizations (already in dependencies or easy to add)

**UI Views:**

**Activity Feed (Main Dashboard)**
- Real-time-ish scrolling feed of recent actions
- Color-coded by action type (block-break: red, block-place: green, etc.)
- Click to expand details
- Quick filters at top
- "Last synced X minutes ago" indicator with refresh button

**Search**
- Advanced search form with all filter options:
  - Player (dropdown of known players)
  - Action type (block-break, block-place, item-insert, etc.)
  - Object (searchable block/item list)
  - World (overworld, nether, end)
  - Time range (after/before date pickers)
  - Coordinates (x, y, z with optional range)
- Results table with sorting
- Export to CSV
- Pagination

**Player Profiles**
- List of all tracked players
- Click into player detail:
  - Total actions by type (pie chart)
  - Activity timeline (line chart - actions over time)
  - Recent actions list
  - First/last seen dates
  - Most modified blocks

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

#### 1.4 Deployment

No new infrastructure needed! Just push changes to main branch.

**Updated Infrastructure Diagram:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────────┐
│  Bloom.host     │     │ GitHub Actions  │     │  DigitalOcean App Platform  │
│  /world/        │     │                 │     │  (theblockacademy)          │
│                 │     │ ┌─────────────┐ │     │                             │
│  ledger.sqlite ─┼────▶│ │ledger-sync  │ │     │  ┌────────────────────────┐ │
│                 │     │ │(every 6hrs) │─┼────▶│  │ DO Spaces              │ │
│  player stats  ─┼────▶│ │stats-export │ │     │  │ └─ ledger/ledger.sqlite│ │
│                 │     │ │(every 15min)│ │     │  │ └─ server-backups/     │ │
│  backups       ─┼────▶│ │backup-sync  │ │     │  └────────────────────────┘ │
│                 │     │ │(every 6hrs) │ │     │              ↓              │
└─────────────────┘     │ └─────────────┘ │     │  ┌────────────────────────┐ │
                        └─────────────────┘     │  │ API Service            │ │
                                                │  │ └─ /auth, /events      │ │
                                                │  │ └─ /admin, /upload     │ │
                                                │  │ └─ /ledger (NEW)       │ │
                                                │  └────────────────────────┘ │
                                                │              ↓              │
                                                │  ┌────────────────────────┐ │
                                                │  │ Frontend Static Site   │ │
                                                │  │ └─ /admin/ledger (NEW) │ │
                                                │  └────────────────────────┘ │
                                                └─────────────────────────────┘
```

---

### Phase 2: Live Connection

**Goal:** Fresher data with on-demand sync.

#### 2.1 On-Demand Refresh

Since the backend already downloads from DO Spaces, add a manual sync endpoint.

**Add to ledger.ts:**
```typescript
// POST /ledger/sync - Trigger fresh download from Spaces
router.post('/sync', async (req, res) => {
  const lastSync = await getLastSyncTime();
  const now = new Date();

  // Rate limit: 5 minutes between syncs
  if (lastSync && (now.getTime() - lastSync.getTime() < 300000)) {
    return res.status(429).json({
      error: 'Rate limited',
      nextSyncAvailable: new Date(lastSync.getTime() + 300000)
    });
  }

  await downloadFromSpaces();
  reopenDatabase();

  res.json({ success: true, syncedAt: now });
});
```

**UI Updates:**
- Add "Refresh" button to Ledger dashboard header
- Show "Last synced: X minutes ago" indicator
- Auto-refresh when dashboard is active (every 5 minutes)
- Disable refresh button during cooldown, show countdown

#### 2.2 Direct SFTP Sync (Optional)

For more immediate data, add endpoint that syncs directly from Bloom.host:

```typescript
// POST /ledger/sync/live - Sync directly from server (admin only, rate limited)
router.post('/sync/live', async (req, res) => {
  // This is slower but gets absolute latest data
  // Rate limit to 1 per 5 minutes
  await downloadViaSftp();  // Uses ssh2-sftp-client
  await uploadToSpaces();   // Cache for other instances
  reopenDatabase();
  res.json({ success: true });
});
```

**Dependencies to add:**
```bash
cd backend && npm install ssh2-sftp-client @types/ssh2-sftp-client
```

---

### Phase 3: Full Admin Panel

**Goal:** Perform admin actions (rollback, restore, purge) from the web.

#### 3.1 Authentication (Already Done!)

theblockacademy already has exactly what we need:

| Requirement | theblockacademy Solution |
|-------------|--------------------------|
| Admin-only access | `requireAdmin` middleware |
| User identification | Microsoft OAuth → email + optional MC username |
| Session management | Cookie-based sessions with 7-day expiry |
| Audit trail | Can log admin actions to PostgreSQL |

**No new auth work needed.** Just use existing `requireAdmin` on all ledger routes.

#### 3.2 Permission Levels

Extend the existing system for granular ledger permissions:

**Option A: Use Existing Admin Flag (Recommended for Phase 1-2)**
- `is_admin = true` → Full ledger access (view, rollback, purge)
- Everyone else → No access

**Option B: Add Ledger-Specific Permissions (Future)**
If we need moderator-level access, add to users table:
```sql
ALTER TABLE users ADD COLUMN ledger_access TEXT DEFAULT 'none';
-- Values: 'none', 'view', 'full'
```

**Recommendation:** Start with Option A. Add granular permissions only if needed.

#### 3.3 RCON Integration

Ledger commands must be run in-game or via server console. Use Pterodactyl API (already used by backup-sync.py).

**New Service:** `theblockacademy/backend/src/services/server-command.ts`
```typescript
const PTERODACTYL_URL = 'https://game.bloom.host';

export async function sendServerCommand(command: string): Promise<boolean> {
  const response = await fetch(
    `${PTERODACTYL_URL}/api/client/servers/${process.env.PTERODACTYL_SERVER_ID}/command`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.PTERODACTYL_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ command })
    }
  );
  return response.ok;
}

// Example usage:
// await sendServerCommand('ledger rollback source:GrieferName after:1h');
```

#### 3.4 Admin Actions

**Preview Rollback Flow:**
1. User selects filters (player, time range, area) in UI
2. Backend queries SQLite for matching actions
3. Display preview: "X blocks will be restored" with list
4. User confirms with "type ROLLBACK to confirm" pattern
5. Backend sends `/ledger rollback` command via Pterodactyl API
6. Log action to audit table

**Restore Flow:**
- Same as rollback, but for previously rolled-back actions
- Uses `rolledback:true` filter

**Purge Flow (Dangerous!):**
- Delete old records from database
- Requires confirmation: "type DELETE FOREVER to confirm"
- Limited to records older than X days
- Log action with full parameters

**API Endpoints:**
```typescript
// POST /ledger/actions/preview-rollback
// Body: { filters: {...} }
// Returns: { count: 123, actions: [...preview...] }

// POST /ledger/actions/rollback
// Body: { filters: {...}, confirmation: "ROLLBACK" }
// Returns: { success: true, command: "ledger rollback ...", affectedCount: 123 }

// POST /ledger/actions/restore
// Body: { filters: {...}, confirmation: "RESTORE" }

// POST /ledger/actions/purge
// Body: { olderThanDays: 30, confirmation: "DELETE FOREVER" }
```

#### 3.5 Audit Log

Track all admin actions in PostgreSQL (not SQLite - we want this in our main DB).

**Migration:** `backend/src/db/migrations/XXX_ledger_audit.sql`
```sql
CREATE TABLE ledger_audit_log (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  admin_user_id INTEGER REFERENCES users(id),
  admin_email TEXT NOT NULL,
  action_type TEXT NOT NULL,  -- 'rollback', 'restore', 'purge', 'sync'
  parameters JSONB,           -- Filters used
  affected_count INTEGER,
  command_sent TEXT,          -- Actual command sent to server
  status TEXT NOT NULL        -- 'success', 'failed', 'pending'
);

CREATE INDEX idx_ledger_audit_timestamp ON ledger_audit_log(timestamp);
CREATE INDEX idx_ledger_audit_admin ON ledger_audit_log(admin_user_id);
```

**Display in Admin UI:**
- Add "Audit Log" tab to Ledger dashboard
- Show recent admin actions with who/what/when
- Filterable by action type and admin

#### 3.6 Alerts & Notifications

**Discord Webhook Integration:**

Add to existing slashAI Discord bot or use webhooks directly.

**Alert Types:**
- Admin performed rollback (notify #admin-log)
- Suspicious activity detected (notify #alerts)
- Daily summary (notify #server-stats)

**Example Alert Rules:**
- Player breaks > 100 blocks in 5 minutes
- Diamond ore broken (track rare blocks)
- New player breaks blocks within 10 minutes of joining
- Large area cleared (> 50 blocks in small radius)

**Implementation:** Add background job or GitHub Action that:
1. Queries ledger.sqlite for suspicious patterns
2. Posts to Discord webhook if threshold exceeded

---

## Technical Considerations

### SQLite in Node.js

**Package:** `better-sqlite3` (synchronous, fast, widely used)

**Installation:**
```bash
cd backend && npm install better-sqlite3 @types/better-sqlite3
```

**Note:** `better-sqlite3` requires native compilation. DigitalOcean App Platform handles this, but may need build dependencies:
```yaml
# In .do/app.yaml, add to build_command if needed:
build_command: apt-get update && apt-get install -y python3 make g++ && npm install && npm run build
```

**Alternative:** If native compilation is problematic, use `sql.js` (pure JavaScript, WebAssembly-based SQLite).

### Database Caching Strategy

```typescript
// In ledger-db.ts
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour

let db: Database.Database | null = null;
let lastDownload: Date | null = null;
let dbPath = './data/ledger.sqlite';

export async function getLedgerDatabase(): Promise<Database.Database> {
  const now = new Date();
  const isStale = !lastDownload || (now.getTime() - lastDownload.getTime() > CACHE_TTL_MS);

  if (!db || isStale) {
    // Close existing connection
    if (db) {
      db.close();
      db = null;
    }

    // Download fresh copy
    await downloadFromSpaces();

    // Open new connection
    db = new Database(dbPath, { readonly: true });
    lastDownload = now;
  }

  return db;
}

export function getLastSyncTime(): Date | null {
  return lastDownload;
}

export async function forceRefresh(): Promise<void> {
  lastDownload = null; // Force next call to download
  await getLedgerDatabase();
}
```

### Security

- **SQLite file:** Never expose publicly. Keep in Spaces with `ACL: private`.
- **API sanitization:** All query parameters must be validated and escaped.
- **Rate limiting:** Sync endpoints limited to prevent abuse.
- **Audit logging:** All admin actions logged with user identity.
- **RCON commands:** Only send via backend, never expose credentials to frontend.

---

## File Structure (New Files in theblockacademy)

```
theblockacademy/
├── .github/workflows/
│   └── sync-ledger.yml          # NEW: GitHub Action for sync
├── scripts/
│   └── ledger-sync.py           # NEW: Sync script
├── backend/src/
│   ├── routes/
│   │   └── ledger.ts            # NEW: Ledger API routes
│   ├── services/
│   │   ├── ledger-db.ts         # NEW: SQLite connection manager
│   │   └── server-command.ts    # NEW: Pterodactyl command sender
│   └── db/migrations/
│       └── XXX_ledger_audit.sql # NEW: Audit log table
└── src/pages/admin/
    ├── Ledger.tsx               # NEW: Main dashboard
    ├── LedgerSearch.tsx         # NEW: Advanced search
    ├── LedgerPlayer.tsx         # NEW: Player detail
    └── LedgerAnalytics.tsx      # NEW: Charts
```

---

## Next Steps

1. **Set up sync pipeline:**
   - Create `scripts/ledger-sync.py`
   - Create `.github/workflows/sync-ledger.yml`
   - Add any missing secrets to GitHub repository
   - Test workflow manually

2. **Add backend routes:**
   - Install `better-sqlite3`
   - Create `ledger-db.ts` service
   - Create `ledger.ts` routes
   - Mount routes in `index.ts`

3. **Build frontend:**
   - Add Ledger link to admin navigation
   - Create main dashboard page
   - Add search functionality
   - Add player detail view

4. **Deploy:**
   - Push to main branch
   - Verify DigitalOcean build succeeds
   - Test in production

5. **Iterate:**
   - Add analytics charts
   - Add on-demand refresh
   - Add admin actions (Phase 3)

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

---

## Appendix: theblockacademy Architecture Reference

**Key files for integration:**

| Component | File | Purpose |
|-----------|------|---------|
| Auth middleware | `backend/src/middleware/admin.ts` | `requireAdmin` function |
| Existing admin routes | `backend/src/routes/admin.ts` | Pattern to follow |
| DO Spaces client | `backend/src/services/spaces.ts` | S3 client setup |
| Protected routes | `src/components/auth/ProtectedRoute.tsx` | Wrap admin pages |
| Auth context | `src/contexts/AuthContext.tsx` | `isAdmin` flag |
| API client | `src/lib/api.ts` | Add `ledgerApi` object |
| Backup sync | `scripts/backup-sync.py` | Pattern for sync script |
| Stats export | `scripts/stats-exporter.py` | Pattern for sync script |
