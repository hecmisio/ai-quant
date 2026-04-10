## 1. Data Access Setup

- [x] 1.1 Add the AkShare dependency to the project development environment if it is not already available
- [x] 1.2 Create a reusable A-share stock list module under `src/data/`

## 2. Stock List Implementation

- [x] 2.1 Implement AkShare-based fetching of the A-share stock list
- [x] 2.2 Normalize the fetched result into stable fields including stock code, stock name, and market or exchange information
- [x] 2.3 Implement default filtering that excludes ST and *ST stocks

## 3. Script And Verification

- [x] 3.1 Add a script entrypoint under `scripts/` to run the stock list fetch and filtering flow
- [x] 3.2 Add tests for normalized output structure and ST filtering behavior
- [x] 3.3 Run the relevant tests or script checks and confirm the filtered stock list flow works end to end
