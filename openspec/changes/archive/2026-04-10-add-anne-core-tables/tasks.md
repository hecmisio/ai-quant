## 1. Schema Definition

- [x] 1.1 Create a versioned Anne schema SQL file for the first batch of governance tables
- [x] 1.2 Add first-version relational tables for instruments, market bars, financial reports, macro series and macro observations
- [x] 1.3 Add first-version relational tables for documents, calendar events, and catalyst events

## 2. Constraints And Integrity

- [x] 2.1 Add shared governance columns across the core Anne tables
- [x] 2.2 Add primary keys, unique constraints, and foreign keys for the governance and fact tables
- [x] 2.3 Add baseline indexes for expected lookup paths without prematurely introducing full hypertable or vector optimizations

## 3. Verification

- [x] 3.1 Apply the Anne schema SQL to the local `anne` PostgreSQL database
- [x] 3.2 Verify that the new tables, constraints, and relationships are created successfully
- [x] 3.3 Insert or simulate minimal sample records to confirm provenance references and duplicate-prevention behavior
