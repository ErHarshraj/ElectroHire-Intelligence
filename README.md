# ElectroHire Intelligence

ElectroHire Intelligence is a job-discovery and career-intelligence platform designed for electronics, embedded, hardware, PCB, robotics, IoT, and related engineering roles.

The goal is not to build a simple job scraper.

The system will discover permitted job opportunities, normalize job data, understand electronics-specific skills, evaluate fresher compatibility, match jobs against candidate skills and projects, rank opportunities, discover relevant startups, and provide application tracking.

## Current Status

Phase 0 — Environment Audit and Project Foundation

The project is being developed incrementally. Each major phase is tested and committed before proceeding to the next phase.

## Target Users

- Electronics Engineers
- Electronics & Communication Engineers
- ECE/E&TC graduates
- Embedded Hardware Engineers
- Hardware Design Engineers
- PCB Design Engineers
- Circuit Design Engineers
- Electronics R&D Engineers
- Embedded Systems Engineers
- IoT Hardware Engineers
- Robotics Hardware Engineers
- Power Electronics Engineers
- Semiconductor/Hardware Engineers
- Graduate Engineer Trainees
- Fresh graduates
- Candidates with 0–2 years of experience

## Important Principles

- Build incrementally.
- Prefer small, testable modules.
- Use deterministic logic before introducing AI/LLMs.
- Never fabricate jobs, companies, salaries, or hiring claims.
- Never bypass authentication, CAPTCHA, robots restrictions, paywalls, or access controls.
- Prefer official APIs, public feeds, permitted career pages, and structured public data.
- Keep source-specific logic behind source adapters.
- Never commit secrets.
- Use environment variables for credentials.
- Test every meaningful milestone.
- Keep candidate matching and job quality as separate concepts.
- Keep startup opportunity scoring separate from job matching.

## Planned Technology Stack

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Celery or equivalent background task system
- React/Next.js or another modern frontend
- Docker
- Docker Compose
- pytest
- Ruff
- mypy
- pre-commit

## Legal and Data-Source Policy

ElectroHire must not bypass technical or legal access controls.

Each job source will be implemented through an abstraction layer so that source-specific behavior remains isolated.

If a source cannot be legally or technically automated, it will be documented rather than bypassed.
