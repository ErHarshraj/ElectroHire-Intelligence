# ElectroHire Intelligence — Architecture

## 1. Purpose

ElectroHire Intelligence is designed as a modular job-intelligence platform rather than a single-site job scraper.

The architecture separates:

- job discovery
- company discovery
- data normalization
- domain intelligence
- candidate matching
- ranking
- notifications
- presentation

## 2. High-Level Architecture

```text
Permitted Sources
       ↓
Job Source Adapters
       ↓
RawJob
       ↓
Normalization / Validation
       ↓
Duplicate Detection
       ↓
PostgreSQL
       ↓
Matching / Ranking
       ↓
FastAPI / Dashboard
       ↓
Applications / Alerts
```

## 3. Repository Boundaries

### apps/api

Application-facing FastAPI service.

Responsibilities:

- REST endpoints
- request validation
- authentication
- service orchestration
- API responses

### apps/worker

Background processing.

Responsibilities:

- job ingestion
- normalization pipelines
- periodic verification
- matching jobs
- daily digest generation
- notification processing

### apps/web

Frontend application.

Responsibilities:

- dashboard
- job search
- job details
- company details
- startup discovery
- recommendations
- application tracking
- candidate profile

### packages/domain

Core business/domain models and rules.

This package should not depend directly on frontend or infrastructure implementations.

### packages/job_sources

Source abstraction and source-specific adapters.

Conceptually:

```text
JobSource
├── APIJobSource
├── CompanyCareerSource
├── RSSJobSource
├── StartupDirectorySource
└── ManualSource
```

### packages/company_discovery

Company and startup discovery logic.

### packages/matching

Candidate/job matching and scoring.

### packages/nlp

Text normalization, terminology handling, and later semantic processing.

### packages/notifications

Notification provider abstractions.

### packages/common

Shared infrastructure that does not belong to a specific domain subsystem.

## 4. Job Ingestion Pipeline

```text
Source
  ↓
RawJob
  ↓
Normalizer
  ↓
Validator
  ↓
Deduplicator
  ↓
Database
```

The application should not directly depend on a particular job website.
