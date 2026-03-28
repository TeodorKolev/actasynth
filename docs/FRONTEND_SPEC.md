# Frontend Application Specification
## AgentOps Studio - Value Proposition Generator

**Document Version:** 1.0
**Last Updated:** 2026-01-12
**Target Stack:** Next.js 14+, TypeScript, shadcn/ui, TailwindCSS

---

## 1. Executive Summary

This document specifies the requirements for building a frontend application that interfaces with the AgentOps Studio backend API. The application enables users to submit customer notes and automatically generate compelling value propositions using AI-powered workflows across multiple LLM providers (OpenAI, Anthropic, Google).

### Key Features
- 🔐 User authentication and session management
- 📝 Customer feedback input interface
- 🤖 Multi-provider AI workflow execution
- 📊 Real-time workflow progress tracking
- 📈 Cost and performance analytics
- 🎯 Value proposition editing and export
- 📜 Workflow history and caching insights

---

## 2. Backend API Overview

### Base URL
```
Production: https://api.agentops.studio (TBD)
Development: http://localhost:8000
```

### API Endpoints

#### Health & Configuration
```typescript
GET /api/v1/health
Response: { status: "healthy", service: "agentops-studio" }

GET /api/v1/config/check
Response: {
  openai_key_configured: boolean
  anthropic_key_configured: boolean
  google_key_configured: boolean
  environment: string
  langsmith_enabled: boolean
}
```

#### Primary Workflow Execution
```typescript
POST /api/v1/workflow/execute
Query Params:
  - provider?: "openai" | "anthropic" | "google" (default: "google")
  - model?: string (default: "gemini-2.5-flash-lite")
  - temperature?: number (0.0-2.0, default: 0.7)

Request Body: RawInput
Response: WorkflowResult (see Data Models section)
```

#### Parallel Provider Comparison
```typescript
POST /api/v1/workflow/execute-parallel
Query Params:
  - providers?: ("openai" | "anthropic" | "google")[] (default: ["openai", "anthropic"])

Request Body: RawInput
Response: { [provider: string]: WorkflowResult }
```

#### Metrics (for admin dashboard)
```typescript
GET /api/v1/metrics
Response: Prometheus text format metrics
```

---

## 3. Data Models (TypeScript)

### Input Models

```typescript
interface RawInput {
  content: string;           // Min 10 characters, required
  source?: string;           // Default: "manual"
  customer_id?: string;      // Optional customer identifier
  metadata?: Record<string, string>; // Optional additional context
}
```

### Output Models

```typescript
type Provider = "openai" | "anthropic" | "google";
type Language = "en" | "es" | "fr" | "de" | "other";
type PIIType = "email" | "phone" | "ssn" | "credit_card" | "name" | "address";
type Persona = "executive" | "technical" | "business_user" | "procurement";

interface WorkflowResult {
  run_id: string;                    // UUID
  value_proposition: ValueProposition;
  normalized_input: NormalizedInput;
  extracted_data: ExtractedData;
  self_check: SelfCheckResult;
  total_latency_ms: number;
  total_cost_usd: number;
  provider_used: string;
  model_used: string;
  success: boolean;
  error: string | null;
}

interface ValueProposition {
  headline: string;                  // Max 200 chars
  problem: string;
  solution: string;
  differentiation: string;
  quantified_value: string | null;
  call_to_action: string;
  persona: Persona;
  key_talking_points: string[];      // 3-5 items
  generated_at: string;              // ISO datetime
}

interface NormalizedInput {
  content: string;
  language: Language;
  detected_pii: PIIDetection[];
  has_pii: boolean;
  cleaned_content: string;
  word_count: number;
  processed_at: string;              // ISO datetime
}

interface PIIDetection {
  pii_type: PIIType;
  value: string;
  confidence: number;                // 0.0-1.0
  location: [number, number];        // [start, end] character positions
}

interface ExtractedData {
  problem_statement: string;
  current_solution: string | null;
  desired_outcome: string;
  pain_points: string[];             // Min 1 item
  value_drivers: string[];           // Min 1 item
  stakeholders: string[];
  timeline: string | null;
  budget_signals: string | null;
  confidence_score: number;          // 0.0-1.0
}

interface SelfCheckResult {
  verifications: ClaimVerification[];
  overall_accuracy: number;          // 0.0-1.0
  hallucination_risk: number;        // 0.0-1.0
  approved: boolean;
  rejection_reason: string | null;
}

interface ClaimVerification {
  claim: string;
  supported_by_input: boolean;
  evidence: string | null;
  confidence: number;                // 0.0-1.0
}
```

---

## 4. Application Architecture

### Tech Stack

**Framework:** Next.js 14+ (App Router)
- Server-side rendering for SEO
- API routes for authentication proxy
- Streaming support for real-time updates

**UI Components:** shadcn/ui
- Pre-built accessible components
- Customizable with Tailwind
- Dark mode support

**Styling:** TailwindCSS
- Utility-first CSS
- Responsive design
- Custom theme configuration

**State Management:**
- React Context for auth state
- TanStack Query (React Query) for API data
- Zustand for complex client state (optional)

**Authentication:**
- Supabase Authentication for session management
- JWT tokens
- Secure cookie storage

**Form Validation:** Zod + React Hook Form
- Type-safe validation
- Schema-based validation matching backend

**Data Fetching:** TanStack Query
- Automatic caching
- Optimistic updates
- Real-time invalidation

---

## 5. Page Structure & User Flows

### 5.1 Authentication Pages

#### `/login`
**Purpose:** User login page

**Layout:**
- Centered card layout
- Branding/logo at top
- Login form in center
- Minimal, clean design

**Components:**
- Email input
- Password input (with show/hide toggle)
- Login button
- Supabase authentication provider

**Behavior:**
- Form validation on blur and submit
- Loading state during authentication
- Error messages for invalid credentials (from Supabase)
- Redirect to `/dashboard` on success
- Supabase handles session management automatically
- Session stored in cookies (managed by Supabase)

**Supabase Integration:**
```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Login flow
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
})
```

**Notes:**
- No registration page (admin creates users in Supabase)
- No forgot password flow (handled by Supabase if needed later)
- No sign-up link
- Simple, single-purpose login interface

---

### 5.2 Main Application Pages

#### `/dashboard`
**Purpose:** Home page after login, overview of recent workflows

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Header (Logo, Navigation, User Menu)               │
├─────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│ │ Total Runs  │ │ Avg Cost    │ │ Success Rate│  │
│ │    342      │ │  $0.012     │ │   94.2%     │  │
│ └─────────────┘ └─────────────┘ └─────────────┘  │
│                                                     │
│ Recent Workflows                        [View All] │
│ ┌───────────────────────────────────────────────┐ │
│ │ Customer Feedback - OpenAI    $0.015   2m ago│ │
│ │ Sales Call Notes - Anthropic  $0.008   1h ago│ │
│ │ Product Review - Google       $0.003   3h ago│ │
│ └───────────────────────────────────────────────┘ │
│                                                     │
│ Quick Actions                                       │
│ [+ New Workflow]  [Compare Providers]  [Settings]  │
└─────────────────────────────────────────────────────┘
```

**Components:**
- Stats cards (total runs, average cost, success rate, total spend)
- Recent workflows table (sortable, filterable)
- Quick action buttons
- Cost trend chart (optional)

**Data Requirements:**
- Fetch recent workflow runs from backend (needs new endpoint)
- Calculate aggregated statistics
- Real-time updates via polling or websockets

---

#### `/workflow/new`
**Purpose:** Primary workflow creation interface

**Layout - Step 1: Input**
```
┌─────────────────────────────────────────────────────┐
│ Create New Value Proposition                        │
├─────────────────────────────────────────────────────┤
│ Step 1: Input Customer Feedback                     │
│                                                     │
│ Customer Notes *                                    │
│ ┌───────────────────────────────────────────────┐ │
│ │                                               │ │
│ │  [Large textarea - min 10 chars]              │ │
│ │  Placeholder: "Paste customer feedback,       │ │
│ │  call notes, emails, or product reviews..."   │ │
│ │                                               │ │
│ │                                               │ │
│ └───────────────────────────────────────────────┘ │
│                                     234 characters  │
│                                                     │
│ Source                                              │
│ [Dropdown: Manual, CRM, Email, Call, Survey, etc.] │
│                                                     │
│ Customer ID (optional)                              │
│ [Input field]                                       │
│                                                     │
│ Metadata (optional)                                 │
│ [Key-value pair inputs]                             │
│                                                     │
│ [Cancel]                        [Next: Configure →] │
└─────────────────────────────────────────────────────┘
```

**Layout - Step 2: Configuration**
```
┌─────────────────────────────────────────────────────┐
│ Create New Value Proposition                        │
├─────────────────────────────────────────────────────┤
│ Step 2: Configure AI Settings                       │
│                                                     │
│ LLM Provider *                                      │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ │ OpenAI   │ │ Anthropic│ │  Google  │           │
│ │  ✓       │ │          │ │          │           │
│ │ GPT-5    │ │ Claude   │ │ Gemini   │           │
│ │ ~$0.015  │ │ ~$0.008  │ │ ~$0.003  │           │
│ │ 3-5s     │ │ 4-7s     │ │ 2-4s     │           │
│ └──────────┘ └──────────┘ └──────────┘           │
│                                                     │
│ Model                                               │
│ [Dropdown: gpt-5-mini, gpt-4, gpt-3.5-turbo]       │
│                                                     │
│ Temperature                      [0.7]              │
│ ├────────●────────────┤                            │
│ 0.0              2.0                                │
│ More Focused     More Creative                      │
│                                                     │
│ ☑ Enable caching (reuse results for 1 hour)       │
│                                                     │
│ [← Back]                      [Generate Workflow →] │
└─────────────────────────────────────────────────────┘
```

**Layout - Step 3: Processing**
```
┌─────────────────────────────────────────────────────┐
│ Generating Value Proposition                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│         ⟳ Processing your workflow...               │
│                                                     │
│ ✓ Step 1: Ingest & Normalize          (0.8s)      │
│   └─ Language detected: English                     │
│   └─ PII detected: 2 email addresses                │
│                                                     │
│ ⟳ Step 2: Extract Insights            (running)    │
│   └─ Analyzing pain points and value drivers...    │
│                                                     │
│ ○ Step 3: Self-Check Quality                       │
│                                                     │
│ ○ Step 4: Generate Value Proposition               │
│                                                     │
│ Estimated time remaining: ~8 seconds                │
│                                                     │
│ [Cancel Workflow]                                   │
└─────────────────────────────────────────────────────┘
```

**Layout - Step 4: Results**
```
┌─────────────────────────────────────────────────────┐
│ Value Proposition Generated ✓                       │
├─────────────────────────────────────────────────────┤
│ Workflow Metrics                                    │
│ Provider: OpenAI (gpt-5-mini)  Cost: $0.015        │
│ Total Time: 4.2s  Accuracy: 92%  Risk: 8%          │
│                                                     │
│ [Tabs: Value Prop | Raw Data | Self-Check | Logs] │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 🎯 Headline                                  │   │
│ │ Transform Manual Data Entry into Automated  │   │
│ │ Intelligence                          [Edit] │   │
│ │                                              │   │
│ │ 📝 Problem                                   │   │
│ │ Your team wastes 15 hours per week on...    │   │
│ │                                       [Edit] │   │
│ │                                              │   │
│ │ 💡 Solution                                  │   │
│ │ Our AI-powered platform eliminates manual...│   │
│ │                                       [Edit] │   │
│ │                                              │   │
│ │ 🚀 Differentiation                           │   │
│ │ Unlike spreadsheet-based solutions...       │   │
│ │                                       [Edit] │   │
│ │                                              │   │
│ │ 💰 Quantified Value                          │   │
│ │ Save $45,000 annually in labor costs        │   │
│ │                                       [Edit] │   │
│ │                                              │   │
│ │ ✅ Call to Action                            │   │
│ │ Schedule a demo to see 10x productivity...  │   │
│ │                                       [Edit] │   │
│ │                                              │   │
│ │ 🗣️ Key Talking Points                        │   │
│ │ • 90% reduction in manual data entry         │   │
│ │ • Real-time insights from unstructured data  │   │
│ │ • Enterprise-grade security and compliance   │   │
│ │                                       [Edit] │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ [Copy to Clipboard] [Export PDF] [Export DOCX]     │
│ [Save Draft] [Create New Workflow]                 │
└─────────────────────────────────────────────────────┘
```

**Behavior:**
- Multi-step wizard with progress indicator
- Real-time validation on each step
- Preview of estimated cost before submission
- Poll backend every 1s during processing to show progress
- Display structured results with inline editing capability
- Export options for various formats

---

#### `/workflow/compare`
**Purpose:** Run workflow across multiple providers simultaneously

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Compare Providers                                   │
├─────────────────────────────────────────────────────┤
│ Input (same as /workflow/new Step 1)               │
│                                                     │
│ Select Providers to Compare:                        │
│ ☑ OpenAI    ☑ Anthropic    ☑ Google               │
│                                                     │
│ [Run Comparison]                                    │
│                                                     │
│ Results (after execution):                          │
│ ┌──────────┬──────────┬──────────┐                │
│ │ OpenAI   │Anthropic │ Google   │                │
│ ├──────────┼──────────┼──────────┤                │
│ │ 4.2s     │ 5.8s     │ 2.9s     │ ← Latency      │
│ │ $0.015   │ $0.008   │ $0.003   │ ← Cost         │
│ │ 94%      │ 91%      │ 89%      │ ← Accuracy     │
│ ├──────────┼──────────┼──────────┤                │
│ │ [Result] │ [Result] │ [Result] │ ← Expandable   │
│ └──────────┴──────────┴──────────┘                │
│                                                     │
│ Winner: Google (best cost-performance ratio)        │
│                                                     │
│ [Export Comparison Report]                          │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Side-by-side comparison of results
- Highlight differences in generated content
- Cost/performance tradeoff visualization
- Recommendation engine (best provider for use case)

---

#### `/history`
**Purpose:** View all past workflow runs

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Workflow History                                    │
├─────────────────────────────────────────────────────┤
│ Filters:                                            │
│ [Date Range] [Provider] [Status] [Source]  [Reset] │
│                                                     │
│ [Search: Filter by content or customer ID...]      │
│                                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ Date        │Provider  │Cost   │Status │Action│ │
│ ├────────────────────────────────────────────────┤ │
│ │ 2m ago      │OpenAI    │$0.015 │✓      │View  │ │
│ │ 1h ago      │Anthropic │$0.008 │✓      │View  │ │
│ │ 3h ago      │Google    │$0.003 │✗ Err  │Retry │ │
│ │ Yesterday   │OpenAI    │$0.012 │✓      │View  │ │
│ └────────────────────────────────────────────────┘ │
│                                                     │
│ Showing 1-20 of 342  [< Prev] [Next >]             │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Sortable and filterable table
- Pagination (20 items per page)
- Quick actions (view, retry, delete)
- Bulk operations (export, delete)
- Cache hit indicators

---

#### `/analytics`
**Purpose:** Cost and performance analytics dashboard

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Analytics Dashboard                                 │
├─────────────────────────────────────────────────────┤
│ Time Period: [Last 7 Days ▼]                       │
│                                                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│ │ Total Spend │ │ Avg Latency │ │ Cache Hit   │  │
│ │   $4.23     │ │    4.8s     │ │   Rate 32%  │  │
│ │   ↑ 12%     │ │    ↓ 8%     │ │   ↑ 5%      │  │
│ └─────────────┘ └─────────────┘ └─────────────┘  │
│                                                     │
│ Cost Breakdown by Provider                          │
│ ┌───────────────────────────────────────────────┐ │
│ │ [Bar chart showing spend per provider]        │ │
│ └───────────────────────────────────────────────┘ │
│                                                     │
│ Workflow Performance Over Time                      │
│ ┌───────────────────────────────────────────────┐ │
│ │ [Line chart: latency and cost trends]         │ │
│ └───────────────────────────────────────────────┘ │
│                                                     │
│ Quality Metrics                                     │
│ ┌─────────────┐ ┌─────────────┐                  │
│ │ Avg Accuracy│ │Hallucination│                  │
│ │    91.5%    │ │  Risk 12%   │                  │
│ └─────────────┘ └─────────────┘                  │
│                                                     │
│ [Export Report]                                     │
└─────────────────────────────────────────────────────┘
```

**Data Sources:**
- Backend `/api/v1/metrics` endpoint (Prometheus data)
- Aggregated workflow history data
- Real-time updates (optional)

**Charts:**
- Cost trend over time (line chart)
- Provider comparison (bar chart)
- Latency distribution (histogram)
- Cache hit rate (percentage)
- Quality scores (gauge charts)

---

#### `/settings`
**Purpose:** User preferences and API configuration

**Tabs:**

**1. Profile**
- Name, email, avatar upload
- Change password
- Delete account

**2. API Configuration**
- Default provider selection
- Default model per provider
- Default temperature
- Cache TTL preference

**3. Notifications**
- Email notifications for completed workflows
- Cost threshold alerts
- Error notifications

**4. Billing (future)**
- Current plan
- Usage limits
- Payment method
- Invoices

---

## 6. Component Library (shadcn/ui)

### Required Components

#### Forms
- `Input` - Text inputs with validation states
- `Textarea` - Multi-line text input
- `Select` - Dropdown selection
- `Radio Group` - Provider selection cards
- `Checkbox` - Terms acceptance, caching toggle
- `Slider` - Temperature control
- `Label` - Form labels with required indicators
- `Form` - Form context provider (React Hook Form integration)

#### Data Display
- `Table` - Workflow history, comparison results
- `Card` - Stats cards, provider cards, result sections
- `Badge` - Status indicators (success, error, pending)
- `Separator` - Section dividers
- `Tabs` - Result views (value prop, raw data, logs)
- `Accordion` - Expandable result sections
- `Progress` - Workflow step progress bar

#### Feedback
- `Alert` - Success/error messages
- `Toast` - Non-blocking notifications
- `Skeleton` - Loading states
- `Spinner` - Inline loading indicators
- `Dialog` - Confirmation modals (delete, retry)
- `Alert Dialog` - Destructive action confirmations

#### Navigation
- `Navigation Menu` - Main navigation
- `Breadcrumb` - Page hierarchy
- `Pagination` - History table pagination
- `Tabs` - Content sections

#### Buttons
- `Button` - Primary, secondary, destructive variants
- `Icon Button` - Edit, delete, copy actions
- `Button Group` - Provider selection toggle

#### Layout
- `Container` - Content width container
- `Grid` - Responsive grid layout
- `Flex` - Flexbox layouts

---

## 7. Authentication & Security

### Authentication Flow with Supabase

**Supabase Setup**
```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true
  }
})
```

**Login Component**
```typescript
// components/LoginForm.tsx
import { supabase } from '@/lib/supabase'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    router.push('/dashboard')
  }

  return (
    <form onSubmit={handleLogin}>
      {/* Form fields */}
    </form>
  )
}
```

**Auth Context Provider**
```typescript
// providers/AuthProvider.tsx
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { User } from '@supabase/supabase-js'

type AuthContextType = {
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signOut: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{ user, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

### Protected Routes
```typescript
// middleware.ts
import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  const {
    data: { session },
  } = await supabase.auth.getSession()

  // Protect routes
  if (!session && req.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  if (!session && req.nextUrl.pathname.startsWith('/workflow')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  if (!session && req.nextUrl.pathname.startsWith('/history')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  if (!session && req.nextUrl.pathname.startsWith('/analytics')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  if (!session && req.nextUrl.pathname.startsWith('/settings')) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  // Redirect to dashboard if already logged in and trying to access login
  if (session && req.nextUrl.pathname === '/login') {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

  return res
}

export const config = {
  matcher: ['/dashboard/:path*', '/workflow/:path*', '/history/:path*', '/analytics/:path*', '/settings/:path*', '/login']
}
```

### API Request Wrapper
```typescript
// lib/api.ts
import { supabase } from '@/lib/supabase'

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Get Supabase session token
  const { data: { session } } = await supabase.auth.getSession()

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.access_token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "API request failed");
  }

  return response.json();
}
```

---

## 8. State Management & Data Fetching

### TanStack Query Setup

```typescript
// lib/queries/workflow.ts
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api";
import type { RawInput, WorkflowResult } from "@/types/workflow";

export function useExecuteWorkflow() {
  return useMutation({
    mutationFn: async ({
      input,
      provider = "google",
      model,
      temperature = 0.7,
    }: {
      input: RawInput;
      provider?: string;
      model?: string;
      temperature?: number;
    }) => {
      return apiRequest<WorkflowResult>(
        `/api/v1/workflow/execute?provider=${provider}&model=${model || ""}&temperature=${temperature}`,
        {
          method: "POST",
          body: JSON.stringify(input),
        }
      );
    },
    onSuccess: (data) => {
      // Show success toast
      console.log("Workflow completed:", data.run_id);
    },
    onError: (error) => {
      // Show error toast
      console.error("Workflow failed:", error);
    },
  });
}

export function useWorkflowHistory(page = 1, limit = 20) {
  return useQuery({
    queryKey: ["workflow-history", page, limit],
    queryFn: () => apiRequest<WorkflowResult[]>(`/api/v1/workflows?page=${page}&limit=${limit}`),
    staleTime: 30000, // 30 seconds
  });
}

export function useCompareProviders() {
  return useMutation({
    mutationFn: async ({
      input,
      providers = ["openai", "anthropic"],
    }: {
      input: RawInput;
      providers?: string[];
    }) => {
      return apiRequest<Record<string, WorkflowResult>>(
        `/api/v1/workflow/execute-parallel?providers=${providers.join(",")}`,
        {
          method: "POST",
          body: JSON.stringify(input),
        }
      );
    },
  });
}
```

---

## 9. Key User Interactions

### 9.1 Login Flow
1. User navigates to `/login`
2. Sees clean, centered login form
3. Enters email and password
4. Clicks "Login" button
5. Supabase authenticates credentials
6. On success: Redirected to `/dashboard`
7. On error: Error message displayed (e.g., "Invalid credentials")
8. Session automatically persisted by Supabase

### 9.2 Create Workflow - Happy Path
1. User clicks "+ New Workflow" from dashboard
2. Navigates to `/workflow/new`
3. Enters customer feedback (min 10 chars validation)
4. Selects source from dropdown
5. (Optional) Adds customer ID and metadata
6. Clicks "Next: Configure"
7. Selects LLM provider (visual card selection)
8. Chooses model from dropdown
9. Adjusts temperature slider (sees real-time preview of effect)
10. Toggles caching (sees estimated cost with/without cache)
11. Clicks "Generate Workflow"
12. Processing screen shows:
    - Step 1: Ingest (animated checkmark when complete)
    - Step 2: Extract (shows extracted insights preview)
    - Step 3: Self-check (shows accuracy score)
    - Step 4: Rewrite (shows final generation)
13. Results screen displays complete value proposition
14. User can:
    - Edit inline (click edit icon on any section)
    - Copy to clipboard
    - Export as PDF/DOCX
    - Save as draft
    - Create new workflow

### 9.3 Create Workflow - Error Handling
**Scenario 1: Self-check rejection**
- Processing stops at Step 3
- Shows alert: "Quality check failed: Insufficient evidence for claims"
- Displays rejection reason from `self_check.rejection_reason`
- Options: "Edit Input" or "Retry with Different Provider"

**Scenario 2: Provider error**
- Processing shows error state at failed step
- Shows alert: "Provider error: Rate limit exceeded"
- Displays full error message from `error` field
- Options: "Retry" or "Try Different Provider"

**Scenario 3: Network error**
- Shows toast notification: "Connection lost"
- Auto-retry with exponential backoff (3 attempts)
- If all retries fail, show error dialog with "Contact Support" option

### 9.4 Compare Providers
1. User clicks "Compare Providers" from dashboard
2. Navigates to `/workflow/compare`
3. Enters customer feedback
4. Selects 2-3 providers to compare
5. Clicks "Run Comparison"
6. Shows parallel progress bars for each provider
7. Results display in side-by-side cards:
   - Latency comparison (bar chart)
   - Cost comparison (with percentage difference)
   - Accuracy scores (with color coding: green >90%, yellow 80-90%, red <80%)
   - Expandable full results
8. System recommends best provider based on:
   - Cost-performance ratio
   - User's historical preferences
   - Current workload
9. User can select winner and proceed with that result

### 9.5 View Workflow History
1. User clicks "History" in navigation
2. Table loads with recent 20 workflows
3. User can:
   - Sort by date, provider, cost, status (click column headers)
   - Filter by date range, provider, status (dropdown filters)
   - Search by content or customer ID (fuzzy search)
   - Click row to view full details (navigates to `/workflow/[run_id]`)
   - Retry failed workflows (icon button)
   - Delete workflows (confirmation dialog)
4. Cache hit indicator shown as badge (tooltip: "Result served from cache, $0.00 cost")

---

## 10. Responsive Design Guidelines

### Breakpoints (Tailwind defaults)
- `sm`: 640px (mobile landscape)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)
- `2xl`: 1536px (ultra-wide)

### Mobile Layout Adaptations

**Dashboard**
- Stack stat cards vertically
- Show 3 most recent workflows only (link to view all)
- Hide trend charts (link to analytics page)

**Workflow Creation**
- Single-column layout
- Provider cards stack vertically
- Temperature slider remains horizontal
- Processing screen shows simplified progress (current step only)

**Results**
- Tabs remain at top
- Each section expands to full width
- Edit buttons move to bottom of each section
- Export options in dropdown menu

**History**
- Table becomes card list
- Show essential info only (date, provider, status)
- Tap card to view details
- Filters in bottom sheet drawer

---

## 11. Accessibility Requirements

### WCAG 2.1 Level AA Compliance

**Keyboard Navigation**
- All interactive elements focusable via Tab
- Skip navigation link
- Focus indicators visible (2px outline)
- Modal trapping (Tab cycles within modal)

**Screen Reader Support**
- Semantic HTML (nav, main, article, aside)
- ARIA labels for icon buttons
- ARIA live regions for dynamic content (processing status)
- ARIA expanded/collapsed for accordions

**Color Contrast**
- Text: 4.5:1 minimum contrast ratio
- Interactive elements: 3:1 minimum
- Error states: red + icon (not color alone)
- Success states: green + checkmark

**Form Accessibility**
- Labels associated with inputs (htmlFor/id)
- Error messages announced to screen readers
- Required fields indicated visually and semantically
- Validation on blur and submit

---

## 12. Performance Optimization

### Code Splitting
- Route-based code splitting (automatic with Next.js App Router)
- Dynamic imports for heavy components (charts, exports)
- Lazy load modals and dialogs

### Image Optimization
- Use Next.js `<Image>` component
- WebP format with fallbacks
- Responsive images (srcSet)
- Lazy loading for below-fold images

### API Optimization
- TanStack Query caching (stale-while-revalidate)
- Debounced search inputs (300ms delay)
- Pagination for large lists
- Request cancellation on unmount

### Bundle Size
- Tree-shaking (automatic with Next.js)
- Remove unused lodash functions (import individually)
- Analyze bundle with `@next/bundle-analyzer`
- Target: < 200KB initial JS bundle

---

## 13. Testing Strategy

### Unit Tests (Vitest + React Testing Library)
- Component rendering
- Form validation logic
- Utility functions
- Custom hooks

**Example:**
```typescript
// __tests__/components/WorkflowForm.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WorkflowForm from "@/components/WorkflowForm";

test("validates minimum content length", async () => {
  render(<WorkflowForm />);
  const textarea = screen.getByLabelText("Customer Notes");
  await userEvent.type(textarea, "short");
  await userEvent.tab(); // Trigger blur validation

  expect(screen.getByText("Minimum 10 characters required")).toBeInTheDocument();
});
```

### Integration Tests (Playwright)
- Complete user flows (login, create workflow, view results)
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile viewport testing

**Example:**
```typescript
// e2e/workflow-creation.spec.ts
import { test, expect } from "@playwright/test";

test("creates workflow successfully", async ({ page }) => {
  await page.goto("/workflow/new");
  await page.fill('[name="content"]', "Customer wants to automate data entry");
  await page.selectOption('[name="source"]', "crm");
  await page.click("text=Next: Configure");

  await page.click('[data-provider="google"]');
  await page.click("text=Generate Workflow");

  await expect(page.locator("text=Step 1: Ingest")).toBeVisible();
  await expect(page.locator("text=Value Proposition Generated")).toBeVisible({ timeout: 30000 });
});
```

### API Mocking (MSW)
- Mock backend responses for development
- Consistent test data
- Error scenario testing

---

## 14. Deployment & DevOps

### Environment Variables
```bash
# .env.local (development)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key # For admin operations only
```

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.agentops.studio
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

**Supabase Setup:**
1. Create a Supabase project at https://supabase.com
2. Get your project URL and anon key from Settings → API
3. Create users in Supabase Auth dashboard (no public registration)
4. Configure JWT secret for backend token verification

### Build & Deploy (Vercel recommended)
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Start production server
npm start
```

### CI/CD Pipeline (GitHub Actions)
```yaml
name: CI/CD
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/action@v1
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

---

## 15. Future Enhancements

### Phase 2 Features
- Real-time collaboration (multiple users editing same workflow)
- Workflow templates library
- Custom prompt engineering interface
- A/B testing for value propositions
- Integration with CRMs (Salesforce, HubSpot)
- Browser extension for capturing feedback

### Phase 3 Features
- Mobile app (React Native)
- Slack/Teams bot integration
- Advanced analytics (cohort analysis, funnel visualization)
- Multi-language support (i18n)
- White-label version for enterprise customers
- API key management for third-party integrations

---

## 16. Design System & Branding

### Color Palette (Suggested)
```css
/* Primary */
--primary: 222.2 47.4% 11.2%; /* Dark blue-gray */
--primary-foreground: 210 40% 98%;

/* Secondary */
--secondary: 210 40% 96.1%;
--secondary-foreground: 222.2 47.4% 11.2%;

/* Accent (for success states) */
--accent: 142.1 76.2% 36.3%; /* Green */
--accent-foreground: 355.7 100% 97.3%;

/* Destructive (for errors) */
--destructive: 0 84.2% 60.2%; /* Red */
--destructive-foreground: 210 40% 98%;

/* Chart colors (for analytics) */
--chart-1: 12 76% 61%; /* OpenAI - Orange */
--chart-2: 173 58% 39%; /* Anthropic - Teal */
--chart-3: 197 37% 24%; /* Google - Blue */
```

### Typography
```css
/* Headings */
font-family: "Inter", sans-serif;
--font-heading: "Inter", sans-serif;

/* Body */
--font-body: "Inter", sans-serif;

/* Code/Monospace */
--font-mono: "JetBrains Mono", monospace;
```

### Spacing Scale (Tailwind defaults)
- `0.5`: 0.125rem (2px)
- `1`: 0.25rem (4px)
- `2`: 0.5rem (8px)
- `4`: 1rem (16px)
- `6`: 1.5rem (24px)
- `8`: 2rem (32px)

### Icons
- Use Lucide Icons (shadcn/ui default)
- 24px default size
- Consistent stroke width (2px)

---

## 17. Backend Requirements (New Endpoints Needed)

**Note:** The following endpoints are not currently implemented in the backend but are needed for the frontend:

### Authentication
**No authentication endpoints needed** - Supabase handles all authentication flows.

The backend should:
1. Accept Supabase JWT tokens in `Authorization: Bearer <token>` header
2. Verify tokens using Supabase JWT verification
3. Extract user ID from verified token for associating workflows with users

**Supabase Token Verification (Python/FastAPI)**
```python
# Example middleware for verifying Supabase tokens
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Workflow History Endpoints
```typescript
GET /api/v1/workflows?page=1&limit=20&provider=openai&status=success
Response: {
  items: WorkflowResult[],
  total: number,
  page: number,
  pages: number
}

GET /api/v1/workflow/{run_id}
Response: WorkflowResult

DELETE /api/v1/workflow/{run_id}
Response: { success: true }
```

### Analytics Endpoints
```typescript
GET /api/v1/analytics/summary?period=7d
Response: {
  total_runs: number,
  total_cost: number,
  avg_latency_ms: number,
  success_rate: number,
  cache_hit_rate: number,
  cost_by_provider: { [provider: string]: number },
  runs_by_day: { [date: string]: number }
}
```

### User Settings Endpoints
```typescript
GET /api/v1/user/settings
Response: {
  default_provider: string,
  default_model: string,
  default_temperature: number,
  cache_enabled: boolean
}

PUT /api/v1/user/settings
Request: { default_provider?, default_model?, ... }
Response: UserSettings
```

---

## 18. Implementation Checklist

### Phase 1: MVP (Weeks 1-3)
- [ ] Project setup (Next.js 14, TypeScript, shadcn/ui)
- [ ] Authentication (Supabase login, protected routes)
- [ ] Basic workflow creation page (input + configuration)
- [ ] API integration (execute workflow endpoint)
- [ ] Results display page (value proposition view)
- [ ] Basic styling and responsive layout

### Phase 2: Core Features (Weeks 4-6)
- [ ] Dashboard with recent workflows
- [ ] Workflow history page with filtering
- [ ] Provider comparison feature
- [ ] Inline editing of results
- [ ] Export functionality (PDF, DOCX, clipboard)
- [ ] Settings page (user preferences)

### Phase 3: Advanced Features (Weeks 7-8)
- [ ] Analytics dashboard with charts
- [ ] Real-time progress tracking (polling/websockets)
- [ ] Cache hit indicators
- [ ] Error handling and retry logic
- [ ] Toast notifications system
- [ ] Loading states and skeletons

### Phase 4: Polish & Testing (Weeks 9-10)
- [ ] Comprehensive error handling
- [ ] Accessibility audit and fixes
- [ ] Performance optimization
- [ ] Unit and integration tests
- [ ] End-to-end tests
- [ ] Documentation

### Phase 5: Deployment (Week 11)
- [ ] Environment configuration
- [ ] CI/CD pipeline setup
- [ ] Vercel deployment
- [ ] Monitoring and analytics setup
- [ ] User acceptance testing

---

## 19. Success Metrics

### User Experience Metrics
- **Time to first value**: < 60 seconds (from login to first result)
- **Workflow completion rate**: > 85%
- **Error rate**: < 5%
- **User satisfaction**: NPS > 50

### Performance Metrics
- **First Contentful Paint (FCP)**: < 1.8s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.5s
- **Cumulative Layout Shift (CLS)**: < 0.1

### Business Metrics
- **Daily Active Users (DAU)**: Track weekly
- **Workflows per user**: > 5/week
- **Feature adoption**: 70% of users use comparison feature
- **Retention**: 60% day-7 retention

---

## 20. Support & Maintenance

### Documentation
- User guide (in-app help center)
- API documentation (for backend integration)
- Component storybook (for developers)
- Deployment guide

### Monitoring
- Error tracking (Sentry)
- Analytics (Vercel Analytics or Google Analytics)
- Performance monitoring (Web Vitals)
- Uptime monitoring (Pingdom or UptimeRobot)

### Feedback Channels
- In-app feedback widget
- Support email (support@agentops.studio)
- Public roadmap (Canny or similar)
- Status page (for incident communication)

---

## Appendix A: API Response Examples

### Successful Workflow Execution
```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "value_proposition": {
    "headline": "Transform Manual Data Entry into Automated Intelligence",
    "problem": "Your team wastes 15 hours per week on repetitive data entry tasks, leading to errors and delayed insights.",
    "solution": "Our AI-powered platform eliminates manual data entry by automatically extracting and structuring information from any source.",
    "differentiation": "Unlike spreadsheet-based solutions, our system learns from your data patterns and continuously improves accuracy without human intervention.",
    "quantified_value": "Save $45,000 annually in labor costs while reducing errors by 95%",
    "call_to_action": "Schedule a demo to see how we can 10x your team's productivity in 30 days",
    "persona": "executive",
    "key_talking_points": [
      "90% reduction in manual data entry time",
      "Real-time insights from unstructured data",
      "Enterprise-grade security and compliance"
    ],
    "generated_at": "2026-01-12T14:23:45.123Z"
  },
  "normalized_input": {
    "content": "Customer feedback about data entry automation needs",
    "language": "en",
    "detected_pii": [
      {
        "pii_type": "email",
        "value": "john@example.com",
        "confidence": 0.95,
        "location": [45, 62]
      }
    ],
    "has_pii": true,
    "cleaned_content": "Customer feedback about data entry automation needs from [REDACTED]",
    "word_count": 42,
    "processed_at": "2026-01-12T14:23:42.123Z"
  },
  "extracted_data": {
    "problem_statement": "Manual data entry is time-consuming and error-prone",
    "current_solution": "Excel spreadsheets with manual data input",
    "desired_outcome": "Automated data extraction and structuring",
    "pain_points": [
      "15 hours per week wasted on data entry",
      "High error rates",
      "Delayed insights"
    ],
    "value_drivers": [
      "Time savings",
      "Error reduction",
      "Faster decision making"
    ],
    "stakeholders": ["Operations team", "Executive leadership"],
    "timeline": "Next quarter",
    "budget_signals": "$50,000 annual budget",
    "confidence_score": 0.92
  },
  "self_check": {
    "verifications": [
      {
        "claim": "15 hours per week wasted",
        "supported_by_input": true,
        "evidence": "Customer mentioned '15 hours per week' in original feedback",
        "confidence": 0.95
      }
    ],
    "overall_accuracy": 0.94,
    "hallucination_risk": 0.08,
    "approved": true,
    "rejection_reason": null
  },
  "total_latency_ms": 4231,
  "total_cost_usd": 0.0142,
  "provider_used": "openai",
  "model_used": "gpt-5-mini",
  "success": true,
  "error": null
}
```

---

## Appendix B: Error Response Examples

### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "content"],
      "msg": "ensure this value has at least 10 characters",
      "type": "value_error.any_str.min_length",
      "ctx": {"limit_value": 10}
    }
  ]
}
```

### Self-Check Rejection
```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "success": false,
  "error": "Self-check rejected workflow",
  "self_check": {
    "approved": false,
    "rejection_reason": "Overall accuracy too low (0.65 < 0.7 threshold)",
    "overall_accuracy": 0.65,
    "hallucination_risk": 0.42
  }
}
```

### Provider Error
```json
{
  "detail": "Provider error: OpenAI API rate limit exceeded. Please retry in 60 seconds."
}
```

---

## Document Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | Initial specification document created |

---

**End of Specification Document**

This document serves as the complete specification for building the AgentOps Studio frontend application. It should be treated as a living document and updated as requirements evolve or new features are added.
