# Nexora AI Frontend

Next.js 15 frontend for the Nexora AI proposal management platform.

## Tech Stack

- **Next.js 15** (App Router)
- **React 19**
- **TypeScript**
- **TailwindCSS**
- **shadcn/ui** (Radix + Tailwind)
- **TanStack Query** (data fetching)
- **React Hook Form** + **Zod** (forms)
- **Axios** (HTTP client)
- **Zustand** (auth state)
- **Framer Motion** (coming soon)

## Getting Started

### Prerequisites

- Node.js 22+
- Backend running at `http://localhost:8000`

### Install

```bash
npm install
```

### Environment

Copy `.env.local` to set the API URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Nexora AI
```

### Run (development)

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Build (production)

```bash
npm run build
npm start
```

## Docker

```bash
docker compose up --build
```

## Project Structure

```
src/
├── app/               # Next.js App Router pages
│   ├── (auth)/        # Login / Register
│   ├── (dashboard)/   # Dashboard, Jobs, Proposals, Analytics, Profile, Settings
│   └── layout.tsx     # Root layout with providers
├── components/
│   ├── ui/            # shadcn/ui primitives
│   ├── layout/        # Sidebar, Navbar, DashboardLayout
│   ├── auth/          # LoginForm, RegisterForm
│   ├── dashboard/     # StatsCards, RecentProposals, ActivityTimeline
│   ├── proposals/     # ProposalReview workspace
│   ├── jobs/          # JobCard, JobFilters
│   └── shared/        # Loading, Empty, Error states, ThemeToggle
├── hooks/             # useAuth, useProposals, useJobs
├── lib/               # api (axios), utils (cn), validators (zod)
├── services/          # auth, proposal, jobs, profile service layers
├── store/             # Zustand auth store
└── types/             # TypeScript interfaces
```

## Pages

| Route | Description |
|---|---|
| `/login` | Sign in |
| `/register` | Create account |
| `/dashboard` | Overview with stats, proposals, activity |
| `/jobs` | Browse opportunities with search & filters |
| `/opportunities` | Manage proposals |
| `/proposals/[id]` | Proposal Review workspace |
| `/analytics` | Performance metrics |
| `/profile` | Account info |
| `/settings` | Preferences & password |

## API Integration

- Axios client with auto-refresh interceptors
- TanStack Query for caching & stale management
- All endpoints use the `/api/v1` base URL
