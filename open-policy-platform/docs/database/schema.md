# Database Schema Overview (Operational)

Key tables referenced by API:
- `core_politician`
  - Suggested indexes: `(name)`, `(party_name)`, `(district)`
- `bills_bill`
  - Suggested indexes: `(classification)`, `(created_at)`, `(title)`
- `hansards_statement`
  - Suggested indexes: `(speaker_name)`, `(date)`, `(hansard_id)`
- `bills_membervote`
- `core_organization`
- `core_membership`

Notes:
- Use `EXPLAIN ANALYZE` to validate hot paths
- Consider partial indexes if data skewed