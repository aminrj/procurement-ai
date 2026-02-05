# Change Summary

Date: February 5, 2026

## Runtime and API stability

- Fixed orchestrator injection mismatch so background analysis can run reliably.
- Normalized tender status transitions to values supported by migrations.
- Added safe upsert behavior for analysis and bid documents to avoid unique-constraint failures on re-analysis.
- Added processing time and error persistence in tender status updates.

## Authentication and tenancy

- Added dedicated organization API keys.
- API auth now checks `X-API-Key` against organization API key (with temporary slug fallback for compatibility).
- Added migration to persist API keys for existing organizations.
- Web routes no longer hardcode `organization_id=1`; they resolve by configured slug and fallback safely.

## Scraper reliability

- Standardized TED search contract around one API endpoint and POST payload.
- Added CPV-filter support in query building.
- Added explicit extraction helpers for title, description, buyer, CPV, and value.
- Updated scraper tests to match the implemented contract.

## Packaging and developer experience

- Fixed invalid `pyproject.toml` build backend.
- Removed broken console entry point from `setup.py`.
- Aligned Python version requirements to 3.11+.

## Documentation and scripts

- Rewrote root and scripts documentation to be concise and accurate.
- Updated API smoke scripts to use correct docs endpoints and API key behavior.
- Removed emoji output from scripts and primary docs.
