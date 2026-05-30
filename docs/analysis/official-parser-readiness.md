# Official Parser Readiness

This note captures what is already prepared for official OGC 2026 parsing and what is still blocked on the missing competition schema.

## What Is Prepared

- the CLI now exposes `--input-format development|official`
- the loader keeps the current development schema path separate from the reserved official-format path
- selecting `--input-format official` fails with a clear message instead of pretending that support exists
- the rest of the solver stack already consumes normalized internal models, so parser replacement is localized to the input layer

## What Is Still Unknown

- official top-level field names
- block and yard attribute names
- whether orientation, zoning, lane, or resource data are mandatory in the official schema
- the exact contest objective definition and any hard retrieval-path rules

## Immediate Parser Tasks Once The Schema Arrives

1. map official field names into `Instance`, `Yard`, and `Block`
2. validate required fields and type conversions with explicit `InstanceFormatError` messages
3. add one official-format fixture and one invalid-format fixture
4. extend feasibility checks only after the official constraints are confirmed
5. revise the objective breakdown terms only after the official score definition is confirmed

## Non-Goals Until The Schema Arrives

- do not guess the official JSON shape
- do not invent placeholder fields that are not backed by the contest materials
- do not rename internal models just to speculate about the future parser