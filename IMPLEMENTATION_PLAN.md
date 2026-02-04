# Dashboard & Kanban Board - Implementation Plan

**Date:** 2026-02-04  
**Author:** Nexus  
**Status:** 🟡 Planning Phase

---

## Executive Summary

Build a unified Dashboard (dashboard.dyai.cloud) that provides:
1. **Project Overview** - All DYAI projects with status
2. **Kanban Board** - Task management for active projects
3. **Revenue Tracking** - Monetization status per project
4. **Quick Actions** - Common tasks and shortcuts

---

## Requirements

### From HEARTBEAT.md

```markdown
## Aktive Projekte

| Projekt | Status | URL |
|---------|--------|-----|
| QuissMe | LIVE | https://quissme.dyai.cloud |
| Agent Zero | 🔴 DOWN | https://a0.dyai.cloud |
| BaZodiac Engine | 🔄 P0 Started | Local repo |
| Dashboard | TODO | dashboard.dyai.cloud |
| Avatar | TODO | Lippensynchron |

## Backlog

1. Bazodiac (Monorepo)
2. Stoppclock (AdSense ready)
3. Babelsberger.info (SEO)
4. MapToPoster (POD)
5. FlashDoc (LIVE)
6. ...and 7 more projects
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Dashboard (dashboard.dyai.cloud)       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────────────────────┐  │
│  │   Header     │  │  Revenue Overview               │  │
│  │  - User     │  │  - Total MRR                    │  │
│  │  - Status   │  │  - AdSense RPM                 │  │
│  └─────────────┘  │  - Project Status               │  │
│                   └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              Kanban Board                        │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │   │
│  │  │ TODO │ │ DOING│ │ REVIEW│ │ DONE │        │   │
│  │  ├──────┤ ├──────┤ ├──────┤ ├──────┤        │   │
│  │  │ Task │ │ Task │ │ Task │ │ Task │        │   │
│  │  │ ...  │ │ ...  │ │ ...  │ │ ...  │        │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘        │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────────────────────┐  │
│  │   Projects  │  │  Quick Actions                  │  │
│  │  - QuissMe  │  │  - Deploy QuissMe               │  │
│  │  - Bazodiac │  │  - Run Tests                    │  │
│  │  - Stoppcl. │  │  - Check Analytics              │  │
│  └─────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Frontend | React + Vite | Fast, modern |
| Backend | None (static) | Simple, fast |
| Data | JSON files | No DB needed |
| Hosting | Vercel/Netlify | Free, easy |
| Auth | None | Internal tool |

---

## Implementation Steps

### Phase 1: MVP (Week 1)

#### 1.1 Project Structure
```
dashboard/
├── index.html          # Entry point
├── package.json
├── vite.config.ts
├── src/
│   ├── main.tsx        # App entry
│   ├── App.tsx         # Main layout
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── RevenueCard.tsx
│   │   ├── KanbanBoard.tsx
│   │   ├── ProjectCard.tsx
│   │   └── QuickActions.tsx
│   ├── data/
│   │   ├── projects.json    # Project definitions
│   │   └── tasks.json       # Kanban tasks
│   ├── hooks/
│   │   └── useProjects.ts
│   └── styles/
│       └── main.css
└── public/
    └── manifest.webmanifest
```

#### 1.2 Data Models

**projects.json:**
```json
{
  "projects": [
    {
      "id": "quissme",
      "name": "QuissMe",
      "status": "live",
      "url": "https://quissme.dyai.cloud",
      "revenue": {
        "model": "freemium",
        "status": "planning",
        "notes": "App Store + WebApp"
      },
      "lastDeployed": "2026-02-03",
      "repo": "DYAI2025/QuissMe"
    },
    {
      "id": "stoppclock",
      "name": "Stoppclock",
      "status": "live",
      "url": "https://www.stoppclock.com",
      "revenue": {
        "model": "adsense",
        "status": "partial",
        "notes": "1/5 slots configured"
      },
      "lastDeployed": "2026-02-04",
      "repo": "DYAI2025/Stoppclock-page"
    },
    {
      "id": "bazodiac",
      "name": "BaZodiac Engine",
      "status": "development",
      "url": null,
      "revenue": {
        "model": "api",
        "status": "planning",
        "notes": "QuissMe + Bazodiac integration"
      },
      "repo": "DYAI2025/Bazodiac.com",
      "phase": "P0"
    }
  ]
}
```

**tasks.json:**
```json
{
  "tasks": [
    {
      "id": "t1",
      "title": "Configure 4 missing AdSense slots",
      "project": "stoppclock",
      "status": "todo",
      "priority": "high",
      "assignee": "Ben",
      "dueDate": "2026-02-07"
    },
    {
      "id": "t2", 
      "title": "Set up GA4 for Stoppclock",
      "project": "stoppclock",
      "status": "doing",
      "priority": "high",
      "assignee": "Nexus",
      "dueDate": "2026-02-05"
    },
    {
      "id": "t3",
      "title": "Implement Harmonic Fusion tests",
      "project": "bazodiac",
      "status": "todo", 
      "priority": "medium",
      "assignee": "Nexus",
      "dueDate": "2026-02-08"
    }
  ]
}
```

#### 1.3 Key Components

**KanbanBoard.tsx:**
```typescript
interface Task {
  id: string;
  title: string;
  project: string;
  status: 'todo' | 'doing' | 'review' | 'done';
  priority: 'high' | 'medium' | 'low';
  assignee: string;
  dueDate?: string;
}

function KanbanBoard({ tasks }: { tasks: Task[] }) {
  const columns = ['todo', 'doing', 'review', 'done'];
  
  return (
    <div class="kanban-board">
      {columns.map(status => (
        <div class="kanban-column">
          <h3>{status.toUpperCase()}</h3>
          <TaskList tasks={tasks.filter(t => t.status === status)} />
        </div>
      ))}
    </div>
  );
}
```

**RevenueCard.tsx:**
```typescript
function RevenueCard({ project }: { project: Project }) {
  const statusColors = {
    live: 'green',
    development: 'yellow', 
    planning: 'gray',
    deprecated: 'red'
  };
  
  return (
    <div class="revenue-card">
      <h4>{project.name}</h4>
      <div class="status-badge" style={{ background: statusColors[project.status] }}>
        {project.status}
      </div>
      <div class="revenue-model">{project.revenue.model}</div>
      <div class="revenue-status">{project.revenue.status}</div>
    </div>
  );
}
```

---

### Phase 2: Enhancements (Week 2)

#### 2.1 GitHub Integration
- Fetch repo status via GitHub API
- Show last commit, branches, open PRs
- Deploy buttons (trigger GitHub Actions)

#### 2.2 Analytics Integration
- Fetch GA4 data (if API available)
- Show page views, sessions, bounce rate

#### 2.3 AdSense Integration  
- Fetch AdSense earnings (limited API)
- Show RPM, CTR, estimated revenue

#### 2.4 Drag & Drop
- Make Kanban cards draggable
- Use `@dnd-kit/core` or `react-beautiful-dnd`

---

### Phase 3: Advanced (Week 3+)

#### 3.1 Multi-User Support
- Add authentication (NextAuth)
- Personal dashboards

#### 3.2 Real-time Updates
- WebSocket for live status
- Auto-refresh project data

#### 3.3 Custom Views
- Filter by project, status, priority
- Saved views

---

## Deployment

### Vercel (Recommended)

```bash
cd dashboard
npm install
npm run build
vercel deploy --prod
```

### Netlify

```bash
npm run build
netlify deploy --prod --dir=dist
```

---

## Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/DYAI2025/dashboard.dyai.cloud.git
cd dashboard.dyai.cloud

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview build
npm run preview
```

---

## Success Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Dashboard Live | ✅ | Week 1 |
| All Projects Listed | 12/12 | Week 1 |
| Kanban Working | ✅ | Week 1 |
| GitHub Integration | ✅ | Week 2 |
| Revenue Tracking | 3/3 | Week 2 |
| Usage (Weekly Active) | 10+ | Week 4 |

---

## Files to Create

| File | Purpose |
|------|---------|
| `package.json` | Dependencies |
| `vite.config.ts` | Vite configuration |
| `tsconfig.json` | TypeScript config |
| `index.html` | Entry HTML |
| `src/main.tsx` | React entry |
| `src/App.tsx` | Main app |
| `src/data/projects.json` | Project data |
| `src/data/tasks.json` | Task data |
| `src/components/*` | React components |
| `src/styles/main.css` | Styles |
| `public/manifest.webmanifest` | PWA manifest |

---

## Next Steps

1. **Create project directory** in `/home/moltbot/dashboard.dyai.cloud/`
2. **Initialize React app** with Vite
3. **Implement MVP components**
4. **Add project data** from HEARTBEAT.md
5. **Deploy to Vercel**
6. **Configure domain** dashboard.dyai.cloud

---

**Status:** Planning Complete  
**Next Action:** Start implementation  
**ETA:** MVP in 1 week
