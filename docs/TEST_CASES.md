# TEST_CASES.md

## Functional cases
- Valid plan: basic happy path where:
  - order totals == batch totals
  - batches fit machine min/max capacity
  - batches scheduled outside downtimes and holidays
  - no overlapping batches on same equipment
- Split orders: one order split into multiple batches.
- Combined orders: multiple orders combined into one batch.

## Negative & edge cases
- Quantity mismatch: batches total != orders total.
- Batch below min capacity.
- Batch above max capacity.
- Batch assigned to equipment that does not exist.
- Batch product not supported by equipment.
- Batch scheduled during equipment downtime.
- Batch scheduled during plant holiday.
- Two batches overlap on same equipment.
- Batch start_time == end_time (invalid).
- Batch start_time > end_time (invalid).
- Downtime with end before start (invalid metadata) -- validator should report malformed inputs.
- Orders with zero quantity and batches covering zero quantities.
- Floating point rounding issues (very small differences) - enforce strict equality but document tolerance option.
- Missing fields in JSON (e.g., missing equipment list) - validator should handle gracefully.

## Data validation checks (what to assert)
- Datetime parseable (ISO 8601 with 'Z' supported).
- All referenced equipment IDs exist.
- Totals per product_code equal between orders and batches.
- For equipment, min_capacity <= max_capacity.
- No overlapping active times for equipment.
- Downtimes and holidays correctly interpreted as closed intervals [start, end).