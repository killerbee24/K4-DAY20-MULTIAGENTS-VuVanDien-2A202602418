---
name: validate-output-schema
description: Use this after generating any structured output (JSON, CSV, or modified files) to verify it matches all specified format requirements.
---
1. List all output format requirements from the task rules (e.g., "money in integer cents", "service names use underscores", "timestamp format YYYY-MM-DDTHH:MM:SSZ").
2. For each requirement, write a simple verification script or manual check:
   - Money values: search for decimal points in numeric fields that should be integers.
   - Naming conventions: check capitalization, separators (hyphens vs underscores), and canonical spellings.
   - Timestamps: verify all dates match the required format with correct timezone.
   - Schema fields: confirm all required top-level keys exist and have correct data types.
3. Run the verification against your output files.
4. If any requirement fails, fix the root cause (not just the symptom) and re-verify.
5. Completion check: All output files pass every requirement without exceptions.
