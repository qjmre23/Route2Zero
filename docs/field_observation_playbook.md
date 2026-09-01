# Field observation playbook

Route2Zero is intentionally conservative about current operations. The public dashboard does not turn an empty form into evidence, and a recent map edit is not treated as proof that a route is active. This playbook describes the smallest controlled observation that can move a corridor from screening to validation.

## What to collect

Use [`netlify-site/public/templates/field_observation_intake.csv`](../netlify-site/public/templates/field_observation_intake.csv) for one row per route observation. The companion [`field_observation.schema.json`](../netlify-site/public/templates/field_observation.schema.json) is the machine-readable contract.

Required fields identify the route, date, validator, source, active-status conclusion, validation status, geometry check, and evidence quality. Optional fields capture the observed endpoints, typical headway, service window, and a verified operator name. Use a source reference that another reviewer can open or locate, such as a dated field log, signed agency record, or consented operator record.

Do not record rider names, phone numbers, home addresses, vehicle plate numbers, or other personal data. The template is for route-level evidence, not a participant register.

## Validate before ingestion

From the repository root, run:

```text
python scripts/validate_field_observation.py --input path/to/field_observation_intake.csv
```

The command prints a JSON result and exits non-zero when a row is missing a required field, uses an unsupported status, contains an invalid date, or falls outside the documented numeric ranges. Duplicate route IDs are allowed when they represent separate dated observations and are reported as audit warnings.

## Evidence gates

1. **Receipt:** a named validator and dated source are present.
2. **Route identity:** the observed route ID and endpoints match the screening record.
3. **Operations:** active status is supported by an observation or an authoritative record; a map relation alone is not enough.
4. **Geometry:** the observed path is checked against the route and marked verified only when the reviewer can reproduce the check.
5. **Review:** a second reviewer records any conflict before the ledger is updated.

The static Netlify site is read-only. Approved observations are added to the controlled ledger by the project team, then the pipeline is rebuilt so the build manifest, checksums, evidence grades, and submission exports remain reproducible.
