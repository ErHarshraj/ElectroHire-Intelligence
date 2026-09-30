# ElectroHire Intelligence

> An electronics-focused career intelligence platform for discovering, evaluating, ranking, and managing technical job opportunities.

**ElectroHire Intelligence** is a career-intelligence system designed specifically for engineers and candidates targeting **hardware, electronics, embedded systems, PCB, robotics, IoT, power electronics, semiconductor, and related technical roles**.

It is designed to go beyond a conventional job scraper.

Instead of simply collecting job listings, ElectroHire Intelligence builds a pipeline that:

```text
Job Sources
    ↓
Source Adapters
    ↓
Raw Job Data
    ↓
Normalization & Validation
    ↓
Cross-Source Deduplication
    ↓
Persistent Job Storage
    ↓
Candidate Profile Matching
    ↓
Relevance / Role / Technical / Domain / Experience Scoring
    ↓
Job Intelligence
    ↓
Application Tracking
    ↓
Approval & Controlled Application Execution
    ↓
Worker Run History
    ↓
Dashboard
```

---

## Table of Contents

* [Overview](#overview)
* [Why ElectroHire Intelligence](#why-electrohire-intelligence)
* [Core Capabilities](#core-capabilities)
* [Target Roles](#target-roles)
* [Architecture](#architecture)
* [Job Discovery](#job-discovery)
* [Normalization and Deduplication](#normalization-and-deduplication)
* [Candidate Profile](#candidate-profile)
* [Candidate-Job Matching](#candidate-job-matching)
* [Job Ranking](#job-ranking)
* [Application Tracking](#application-tracking)
* [Application Execution and Safety](#application-execution-and-safety)
* [Worker System](#worker-system)
* [Dashboard](#dashboard)
* [Persistence](#persistence)
* [API](#api)
* [Project Structure](#project-structure)
* [Supported Job Sources](#supported-job-sources)
* [Technology Stack](#technology-stack)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the System](#running-the-system)
* [Testing](#testing)
* [Development Workflow](#development-workflow)
* [Application Workflow](#application-workflow)
* [Safety Model](#safety-model)
* [Current Status](#current-status)
* [Roadmap](#roadmap)
* [Design Principles](#design-principles)
* [Security](#security)
* [Contributing](#contributing)
* [License](#license)

---

# Overview

Traditional job scrapers generally answer one question:

> "What jobs are available?"

ElectroHire Intelligence is designed to answer a broader set of questions:

* Which jobs are relevant to my engineering profile?
* Which listings are duplicates across multiple sources?
* Which roles match my target engineering domains?
* Which jobs are suitable for an early-career candidate?
* Which opportunities deserve attention first?
* Which applications have already been submitted?
* Which applications are waiting for approval?
* Which applications failed or were paused?
* Which worker runs succeeded or partially failed?
* Which source caused a worker failure?
* What opportunities were discovered during each worker cycle?

The system therefore treats job searching as a **data-processing and decision-support problem**, rather than simply scraping websites.

---

# Why ElectroHire Intelligence

Electronics and embedded engineering opportunities are often fragmented across:

* company career pages
* applicant tracking systems
* startup job boards
* remote job boards
* specialized engineering listings
* general employment platforms

The same position can also appear on several sources.

A useful system therefore needs to handle:

1. **Source integration**
2. **Data normalization**
3. **Validation**
4. **Deduplication**
5. **Technical skill understanding**
6. **Candidate-profile matching**
7. **Ranking**
8. **Application state management**
9. **Safe application execution**
10. **Operational monitoring**

ElectroHire Intelligence is structured around these requirements.

---

# Core Capabilities

## Job Discovery

The system supports multiple job sources through source adapters.

Each source is isolated behind a common interface so that source-specific API or parsing logic does not leak into the rest of the application.

---

## Canonical Job Model

Jobs from different sources are converted into a common representation.

This allows the matching, ranking, persistence, and application systems to work with a consistent job model regardless of where the job originated.

---

## Normalization

Source-specific differences are normalized before jobs enter the main processing pipeline.

Examples include:

* titles
* companies
* locations
* descriptions
* application URLs
* source identifiers
* employment information
* timestamps
* metadata

---

## Cross-Source Deduplication

The same job may be published through several sources.

ElectroHire Intelligence performs canonicalization and duplicate detection so that the system does not treat every copy of the same opportunity as a separate job.

This is important for both ranking and application tracking.

---

# Target Roles

The candidate profile is currently oriented toward technical roles including:

### Hardware

* Hardware Design Engineer
* Hardware Engineer
* Embedded Hardware Engineer

### PCB

* PCB Design Engineer

### Electronics

* Electronics Engineer

### Embedded Systems

* Embedded Systems Engineer

### Robotics

* Robotics Hardware Engineer
* Robotics Engineer
* Robotic Engineer

### IoT

* IoT Hardware Engineer

### Drone / UAV Hardware

* Drone Hardware Engineer

The candidate profile architecture is extensible, so additional target roles can be added without redesigning the matching system.

---

# Architecture

The main architecture is:

```text
                    ┌─────────────────────┐
                    │    Job Sources      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Source Adapters   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      RawJob         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Normalize / Validate│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Duplicate Detection │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Persistent Storage  │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
          ┌──────────────────┐   ┌──────────────────┐
          │ Candidate Match  │   │ Application      │
          │ & Ranking        │   │ Tracking         │
          └────────┬─────────┘   └────────┬─────────┘
                   │                      │
                   └──────────┬───────────┘
                              ▼
                    ┌─────────────────────┐
                    │ FastAPI / Dashboard │
                    └─────────────────────┘
```

---

# Job Discovery

The worker executes configured source queries and processes each source independently.

A source failure does not necessarily terminate the entire worker cycle.

For example:

```text
Source A → successful
Source B → successful
Source C → timeout
Source D → successful
Source E → successful
```

The worker records the failure while continuing with the remaining sources.

This allows one unreliable external source to degrade a cycle without destroying the entire discovery process.

Worker reports record:

* success/failure
* source errors
* queries
* newly discovered jobs
* evaluated jobs
* ignored jobs
* application statistics
* completion time

---

# Normalization and Deduplication

ElectroHire Intelligence uses a canonical job representation so that different source formats can be processed consistently.

The processing pipeline is approximately:

```text
Source Response
      ↓
Parse
      ↓
Raw Job
      ↓
Normalize
      ↓
Validate
      ↓
Canonical Identity
      ↓
Duplicate Detection
      ↓
Persist / Update
```

This is especially important when the same company publishes the same opportunity through several job boards.

---

# Candidate Profile

Candidate information is represented using a persistent canonical candidate profile.

The profile includes:

* identity
* contact information
* resume information
* education
* skills
* projects
* application answers
* target roles
* role families
* skill families
* domain families
* experience keywords

The matching engine consumes this canonical profile instead of relying on scattered configuration values.

---

# Candidate-Job Matching

The matching system evaluates jobs against the candidate profile.

The profile contains structured technical concepts such as:

### Role Families

* hardware
* embedded
* PCB
* electronics
* firmware
* robotics
* electrical
* RTL / ASIC
* verification

### Skill Families

* Embedded C
* PCB
* circuit design
* EDA
* microcontrollers
* embedded systems
* electronics
* hardware
* electrical
* RTL
* verification
* robotics

### Domain Families

* embedded
* robotics
* IoT
* drone
* electronics
* semiconductor
* power electronics
* PCB
* hardware

### Experience Keywords

The current profile includes early-career signals such as:

* entry level
* junior
* fresher
* graduate
* 0-1
* 0-2
* 1-2

This provides a structured representation of the candidate rather than treating the resume as an opaque document.

---

# Job Ranking

The ranking engine produces a relevance score based on multiple dimensions.

Current scoring structure:

| Component         |   Weight |
| ----------------- | -------: |
| Overall relevance |      40% |
| Role match        | up to 25 |
| Technical match   | up to 20 |
| Domain match      | up to 10 |
| Experience match  |  up to 5 |
| Maximum           |      100 |

Jobs can also receive a priority classification:

```text
80+  → HIGH
60+  → MEDIUM
40+  → LOW
```

Jobs identified as irrelevant are capped so that unrelated listings cannot dominate the result set simply because they contain isolated matching keywords.

The ranking system is intended to provide **decision support**, not replace human judgment.

---

# Application Tracking

ElectroHire Intelligence maintains application state separately from job discovery.

This allows the system to distinguish between:

* discovered jobs
* evaluated jobs
* approved applications
* submitted applications
* failed applications
* paused applications
* rejected applications
* previously submitted applications

The application tracker is designed to prevent accidental duplicate submissions.

---

# Application Execution and Safety

Application automation is deliberately separated from job discovery and ranking.

The application system supports different execution modes.

The intended workflow is:

```text
DRY RUN
   ↓
APPROVAL REQUIRED
   ↓
ONE CONTROLLED REAL SUBMISSION
   ↓
VALIDATION
   ↓
CONTROLLED AUTOMATION
```

The system should not begin with unrestricted automatic submission.

The approval workflow allows a human to review an application before execution.

Approved applications are revalidated before execution so that the system does not blindly execute stale approval state.

Unknown or unsafe browser/application conditions can cause an application to be paused rather than automatically submitted.

---

# Application Safety

The browser application layer contains safety-oriented components for:

* field inspection
* field classification
* field mapping
* field filling
* form validation
* application preview
* submission safety
* recovery
* execution policy

Sensitive authentication fields are treated specially.

For example, password and authentication controls are identified by the safety layer rather than being treated as ordinary application fields.

The goal is to prevent the automation layer from making assumptions about fields that require human intervention.

---

# Worker System

The worker is responsible for executing repeatable processing cycles.

A typical cycle is:

```text
Load configuration
       ↓
Load persistent candidate profile
       ↓
Initialize job sources
       ↓
Query sources
       ↓
Normalize jobs
       ↓
Detect duplicates
       ↓
Persist jobs
       ↓
Evaluate candidate relevance
       ↓
Generate ranking
       ↓
Process application state
       ↓
Generate worker report
       ↓
Persist worker run
```

Worker run history is persisted and can be queried later.

---

# Worker Resilience

External job sources are inherently unreliable.

The worker therefore handles source-level failures independently.

For example, if a source experiences:

```text
SSL handshake timeout
HTTP failure
Parser failure
Unexpected source response
```

the worker records the source failure and continues processing other sources.

The overall worker report can therefore indicate:

```text
SUCCESS = FALSE

NEW JOBS = 43
EVALUATED = 18
IGNORED = 25

ERROR = Source 'himalayas' failed: ...
```

while still retaining the successfully processed jobs.

This is preferable to treating a single external failure as a complete worker-cycle failure.

---

# Dashboard

ElectroHire Intelligence includes a lightweight web dashboard.

Current routes include:

```text
/dashboard
/dashboard/jobs/{job_id}
/dashboard/applications
/dashboard/theme.css
```

The dashboard is intentionally compact and scan-oriented.

The main dashboard is designed for:

* job discovery
* score scanning
* priority scanning
* filtering
* source identification
* application review

The complete job description is kept on the job-detail page rather than making the main job list excessively large.

The interface uses a dark theme to reduce visual clutter during repeated job-search sessions.

---

# API

The backend is built with FastAPI.

The API exposes functionality for areas including:

* health
* jobs
* job intelligence
* candidate profile
* applications
* approvals
* worker runs

The API also provides OpenAPI documentation through FastAPI.

Current API identity:

```text
Title: ElectroHire Intelligence API
Version: 0.1.0
```

Health endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

# Persistence

The current local persistence layer uses SQLite through SQLAlchemy.

Default database:

```text
electrohire.db
```

The database contains persistent application and intelligence state rather than being treated as temporary scraper output.

Persisted areas include:

* jobs
* applications
* candidate profile
* worker runs
* related application state

The database is intentionally ignored by Git.

---

# Project Structure

A simplified project structure is:

```text
ElectroHire-Intelligence/
│
├── apps/
│   ├── api/
│   └── worker/
│
├── packages/
│   ├── application/
│   │   ├── adapters/
│   │   ├── browser/
│   │   ├── email/
│   │   ├── application_service.py
│   │   ├── approval.py
│   │   ├── approval_executor.py
│   │   ├── career_application_service.py
│   │   ├── execution_policy.py
│   │   └── recovery.py
│   │
│   ├── common/
│   │   └── config.py
│   │
│   ├── domain/
│   │   └── candidate_profile.py
│   │
│   ├── matching/
│   │   ├── profile.py
│   │   └── ranking.py
│   │
│   ├── persistence/
│   │   ├── database.py
│   │   ├── candidate_profile_repository.py
│   │   └── worker_run_repository.py
│   │
│   └── job_sources/
│       ├── adzuna/
│       ├── ashby/
│       ├── arbeitnow/
│       ├── ayla_gov/
│       ├── four_day_week/
│       ├── greenhouse/
│       ├── hopin/
│       ├── himalayas/
│       ├── jobicy/
│       ├── lever/
│       ├── remoteok/
│       ├── rippling/
│       ├── smartrecruiters/
│       ├── startup_jobs/
│       ├── workable/
│       └── workday/
│
├── templates/
│   └── dashboard/
│
├── tests/
│
├── .env.example
├── .gitignore
├── README.md
└── electrohire.db
```

The actual repository may contain additional files and implementation details beyond this simplified view.

---

# Supported Job Sources

The project currently contains adapters for multiple permitted job sources, including:

* Adzuna
* Greenhouse
* Lever
* Ashby
* SmartRecruiters
* Himalayas
* Remote OK
* Jobicy
* Arbeitnow
* Workday
* Workable
* Hopin
* 4dayweek.io
* AylaGov
* Startup Jobs
* Rippling

Source availability can vary over time because external APIs and websites change.

Sources are configured independently so individual sources can be enabled, disabled, or updated without redesigning the rest of the platform.

---

# Technology Stack

## Backend

* Python 3.10+
* FastAPI
* Uvicorn
* Pydantic
* Pydantic Settings
* SQLAlchemy

## Testing

* pytest
* pytest-cov

## Code Quality

* Ruff
* mypy
* Python compile checks

## Persistence

* SQLite
* SQLAlchemy

## Application Automation

The application layer is structured around:

* dry-run execution
* approval workflows
* browser automation
* field inspection
* form validation
* submission safety
* recovery handling
* execution policies

---

# Installation

Clone the repository:

```bash
git clone https://github.com/ErHarshraj/ElectroHire-Intelligence.git
cd ElectroHire-Intelligence
```

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the project dependencies according to the repository configuration.

Verify the environment:

```bash
python --version
```

Then run the test suite:

```bash
pytest -q
```

---

# Configuration

Create a local environment file from the example:

```bash
cp .env.example .env
```

The `.env` file is intentionally excluded from Git.

Important configuration areas include:

* database configuration
* candidate identity
* candidate contact information
* resume path
* LinkedIn URL
* GitHub URL
* portfolio URL
* job source configuration
* LLM configuration
* SMTP configuration
* application execution mode
* scheduler / worker configuration

Never commit real credentials to the repository.

---

# Candidate Profile Setup

ElectroHire Intelligence uses a persistent canonical candidate profile for matching.

The profile should contain accurate information about:

* candidate name
* email
* phone
* resume
* education
* skills
* projects
* target roles
* technical domains
* experience level
* application answers

The candidate profile is persisted separately from source configuration so that job matching remains consistent across worker runs.

---

# Running the API

The FastAPI application can be started using the project's API entry point.

A typical development command is:

```bash
uvicorn apps.api.main:app --reload
```

The exact entry point should be confirmed against the current repository configuration before deployment.

Once running, FastAPI provides interactive API documentation through its OpenAPI interface.

---

# Running the Worker

The worker executes job discovery and intelligence processing.

The worker:

1. loads configuration
2. initializes persistence
3. loads the canonical candidate profile
4. builds the configured job sources
5. processes each source
6. normalizes and deduplicates jobs
7. evaluates matching
8. processes application state
9. stores the worker report

The worker can be run using the project's worker entry point.

---

# Testing

The project uses pytest.

Run the complete test suite:

```bash
pytest -q
```

Run Ruff:

```bash
ruff check .
```

Run Python compilation checks:

```bash
python -m compileall -q apps packages tests
```

Check Git whitespace errors:

```bash
git diff --check
```

A successful development checkpoint should pass all four.

---

# Development Workflow

The project follows an incremental development workflow:

```text
Inspect
  ↓
Design
  ↓
Implement
  ↓
Focused Tests
  ↓
Full Test Suite
  ↓
Lint
  ↓
Compile Check
  ↓
Diff Review
  ↓
Commit
```

Changes should be kept focused.

Large architectural changes should be introduced only after the current behavior has been validated.

---

# Application Workflow

ElectroHire Intelligence is designed to progress through increasingly automated stages.

## Stage 1 — Dry Run

The system discovers and evaluates opportunities without performing real submissions.

Purpose:

* validate job discovery
* validate candidate matching
* validate ranking
* validate application detection
* inspect generated application decisions

---

## Stage 2 — Approval Required

A human reviews the application before execution.

```text
Job
 ↓
Application Decision
 ↓
Human Review
 ↓
Approve
 ↓
Revalidate
 ↓
Execute
```

This is the intended operating mode for the first real applications.

---

## Stage 3 — Controlled Real Submission

The first real submission should be treated as a controlled integration test.

The system should be observed for:

* application URL behavior
* field detection
* field mapping
* application answers
* resume upload
* unexpected fields
* authentication requirements
* confirmation behavior
* duplicate-submission prevention
* failure recovery

---

## Stage 4 — Controlled Automation

After successful controlled submissions, automation can be expanded gradually.

The goal is not unrestricted automation.

The goal is predictable automation with:

* approval controls
* execution policies
* safety checks
* recovery handling
* application state tracking
* duplicate prevention
* worker history

---

# Safety Model

Application automation can interact with external websites and forms that change without warning.

ElectroHire Intelligence therefore treats application execution differently from job discovery.

Important safety principles include:

### Human Approval

Real applications should require explicit approval during the controlled rollout.

### Revalidation

An approved application is revalidated before execution.

### Unknown Fields

Unknown or ambiguous application fields can cause the workflow to pause instead of guessing.

### Authentication

Password and authentication fields are treated as sensitive.

### Duplicate Prevention

Existing submitted applications are not blindly submitted again.

### Failure Preservation

Failed or paused executions remain represented in application state so that recovery can be handled explicitly.

### Dry Run

The system supports a dry-run mode so that application logic can be tested without sending real submissions.

---

# Current Status

The project has completed the following major milestones:

* Repository architecture established
* Multiple job-source adapters implemented
* Canonical job normalization
* Cross-source deduplication
* Persistent candidate profile
* Candidate-aware matching
* Job relevance ranking
* Application tracking
* Approval-based application execution architecture
* Browser application safety components
* Application recovery architecture
* Worker run history
* Worker source-failure resilience
* FastAPI intelligence APIs
* Lightweight dashboard
* End-to-end validation
* GitHub repository publication

Current repository validation includes:

```text
Full test suite: 715 passed
Ruff: passed
Compile check: passed
git diff --check: passed
Working tree: clean
```

The latest repository commit is:

```text
b53c07f fix: continue worker cycle when source fails
```

---

# Roadmap

Future development can focus on the following areas.

## Real Application Rollout

* approval-required execution
* controlled real submission
* application result verification
* recovery from failed submissions
* platform-specific handling

## Application Intelligence

* improved application-field classification
* stronger answer mapping
* company-specific application handling
* better duplicate prevention

## Job Intelligence

* improved technical skill extraction
* stronger electronics-domain classification
* better experience-level detection
* improved candidate-job explanations

## Worker Automation

* scheduled worker execution
* recurring job discovery
* source health monitoring
* configurable source policies
* worker alerts

## Dashboard

* richer filtering
* application lifecycle visualization
* source health
* worker history visualization
* candidate-match explanations
* application review workflow

## Data Infrastructure

* production PostgreSQL deployment
* Redis-backed worker coordination
* scalable background processing
* stronger observability

---

# Design Principles

ElectroHire Intelligence is built around several principles.

## 1. Intelligence Over Scraping

The purpose is not to collect as many jobs as possible.

The purpose is to identify useful opportunities.

## 2. Canonical Data

Different sources should be converted into consistent domain models.

## 3. Separation of Concerns

Source adapters, domain models, matching, persistence, APIs, dashboard code, and application automation should remain independently testable.

## 4. Human-Controlled Automation

Automation should assist the candidate rather than silently making irreversible decisions.

## 5. Resilience

One external source should not bring down the entire discovery cycle.

## 6. Persistent State

Important decisions and execution history should survive process restarts.

## 7. Test Before Automation

New application behavior should be tested in dry-run mode before being enabled for real submissions.

## 8. Security by Default

Credentials, environment files, databases, sessions, and other sensitive runtime artifacts must remain outside source control.

---

# Security

Never commit:

```text
.env
credentials
API keys
access tokens
passwords
SMTP credentials
browser sessions
cookies
local databases
private application data
```

The repository uses `.gitignore` to exclude sensitive runtime files.

The committed `.env.example` contains placeholders rather than production credentials.

Before pushing changes, inspect tracked files and search for accidental credentials.

Example:

```bash
git ls-files
git grep -nEi 'api[_-]?key|secret|password|access[_-]?token|bearer|smtp.*pass|authorization:' -- ':!tests/fixtures/*' || true
```

---

# Contributing

For development:

1. Create a focused change.
2. Add or update tests.
3. Run the focused tests.
4. Run the complete test suite.
5. Run Ruff.
6. Run compile checks.
7. Review the Git diff.
8. Check for credentials.
9. Commit the change with a descriptive message.

Example:

```bash
pytest -q
ruff check .
python -m compileall -q apps packages tests
git diff --check
```

---

# License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for the full license text.

Copyright (c) 2026 Harshraj

---

# Project

**ElectroHire Intelligence**

GitHub:

https://github.com/ErHarshraj/ElectroHire-Intelligence

Built as a focused career-intelligence platform for electronics, embedded, hardware, PCB, robotics, IoT, and related engineering opportunities.
