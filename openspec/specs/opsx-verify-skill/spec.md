# opsx-verify-skill Specification

## Purpose
Define `/opsx:verify` behavior for assessing implementation completeness, correctness, and coherence against change artifacts.

## Requirements
### Requirement: Verify Skill Invocation
The system SHALL provide an `/opsx:verify` skill that validates implementation against change artifacts.

#### Scenario: Verify with change name provided
- **WHEN** agent executes `/opsx:verify <change-name>`
- **THEN** the agent verifies implementation for that specific change
- **AND** produces a verification report

#### Scenario: Verify without change name
- **WHEN** agent executes `/opsx:verify` without a change name
- **THEN** the agent infers the change from conversation context, or auto-selects it when only one active change exists
- **AND** when ambiguous, prompts user to select from available changes, showing only changes that have implementation tasks
- **AND** announces which change was selected and how to override

#### Scenario: Change has no tasks
- **WHEN** selected change has no tasks.md or tasks are empty
- **THEN** the agent reports "No tasks to verify"
- **AND** suggests running `/opsx:continue` to create tasks

### Requirement: Completeness Verification
The agent SHALL verify that all required work has been completed.

#### Scenario: Task completion check
- **WHEN** verifying completeness
- **THEN** the agent reads tasks.md
- **AND** counts tasks marked `- [x]` (complete) vs `- [ ]` (incomplete)
- **AND** reports completion status with specific incomplete tasks listed

#### Scenario: Spec coverage check
- **WHEN** verifying completeness
- **AND** delta specs exist in `openspec/changes/<name>/specs/`
- **THEN** the agent extracts all requirements from delta specs
- **AND** searches codebase for implementation of each requirement
- **AND** traces beyond keyword matches into the actual execution path where practical
- **AND** reports which requirements have implementation evidence vs which are missing

#### Scenario: All tasks complete
- **WHEN** all tasks are marked complete
- **THEN** report "Tasks: N/N complete"
- **AND** mark completeness dimension as passed

#### Scenario: Incomplete tasks found
- **WHEN** some tasks are incomplete
- **THEN** report "Tasks: X/N complete"
- **AND** list each incomplete task
- **AND** mark as CRITICAL issue
- **AND** suggest: "Complete remaining tasks or mark as done if already implemented"

### Requirement: Correctness Verification
The agent SHALL verify that implementation matches the specifications.

#### Scenario: Requirement implementation mapping
- **WHEN** verifying correctness
- **THEN** for each requirement in delta specs:
  - Search codebase for implementation
  - Identify relevant files and line numbers
  - Trace how the implementation is reached where practical
  - Assess whether implementation satisfies the requirement

#### Scenario: Scenario coverage check
- **WHEN** verifying correctness
- **THEN** for each scenario in delta specs:
  - Check if the scenario's conditions are handled in code
  - Check if tests exist that exercise the scenario
  - Inspect whether those tests assert the specified outcome
  - Report coverage status

#### Scenario: Implementation matches spec
- **WHEN** implementation appears to satisfy a requirement
- **THEN** report which files/lines implement it
- **AND** mark requirement as covered

#### Scenario: Implementation diverges from spec
- **WHEN** implementation exists but concrete evidence shows it doesn't match spec intent
- **THEN** report the divergence as WARNING
- **AND** explain what differs
- **AND** suggest: either update implementation or update spec to match reality

#### Scenario: Missing implementation
- **WHEN** no implementation found for a requirement
- **THEN** report as CRITICAL issue
- **AND** suggest: "Implement requirement X" with guidance on what's needed

### Requirement: Adversarial Verification
The agent SHALL actively try to falsify important implementation claims after the initial implementation mapping rather than only searching for confirming evidence.

#### Scenario: Challenge each important contract
- **WHEN** the agent has mapped requirements and scenarios to implementation evidence
- **THEN** it turns each important artifact statement into a testable claim
- **AND** checks plausible counterexamples including boundary values, negative or error paths, alternate states, and cross-component interactions
- **AND** traces at least one relevant end-to-end execution path when the repository makes that practical

#### Scenario: Presence is not proof
- **WHEN** a matching symbol, keyword, test file, or passing test suite is found
- **THEN** the agent treats it as supporting evidence rather than proof by itself
- **AND** verifies that the implementation is reachable on the required path
- **AND** verifies that relevant tests assert the behavior required by the artifact

#### Scenario: Focused executable validation
- **WHEN** a focused test or command can practically challenge an important claim
- **THEN** the agent runs the smallest relevant validation
- **AND** records what claim the validation attempted to falsify and the observed outcome

#### Scenario: Concrete contradiction found
- **WHEN** source, tests, or executable behavior concretely contradict an artifact claim
- **THEN** the agent reports the defect with the artifact claim, contradicting evidence, and failure mechanism
- **AND** assigns CRITICAL or WARNING severity based on impact

#### Scenario: Evidence is insufficient
- **WHEN** the agent cannot establish a claim from the available source, tests, or executable evidence
- **AND** no concrete contradiction has been demonstrated
- **THEN** it reports a verification gap rather than claiming the implementation is wrong
- **AND** identifies what evidence or validation would resolve the gap

#### Scenario: Validation cannot be executed
- **WHEN** required tooling or environment is unavailable
- **THEN** the agent continues static verification where possible
- **AND** marks affected runtime claims UNVERIFIED
- **AND** does not invent a defect from the inability to run the check

#### Scenario: Targeted falsification finds no contradiction
- **WHEN** implementation evidence matches the artifact
- **AND** a reasonable targeted falsification attempt finds no counterexample
- **THEN** the agent marks the claim SUPPORTED
- **AND** does not describe the result as mathematically proven

### Requirement: Coherence Verification
The agent SHALL verify that implementation is sensible and follows design decisions.

#### Scenario: Design.md adherence check
- **WHEN** verifying coherence
- **AND** design.md exists for the change
- **THEN** extract key decisions from design.md
- **AND** verify implementation follows those decisions
- **AND** report any demonstrated deviations

#### Scenario: No design.md
- **WHEN** verifying coherence
- **AND** no design.md exists
- **THEN** skip design adherence check
- **AND** note "No design.md to verify against"

#### Scenario: Design decision followed
- **WHEN** implementation follows a design decision
- **THEN** report as confirmed
- **AND** cite evidence from code

#### Scenario: Design decision violated
- **WHEN** implementation contradicts a design decision
- **THEN** report as WARNING
- **AND** explain the contradiction
- **AND** suggest: either update implementation or update design.md

#### Scenario: Code pattern consistency
- **WHEN** verifying coherence
- **THEN** check if new code follows existing project patterns
- **AND** flag any significant deviations as suggestions

### Requirement: Verification Report Format
The agent SHALL produce a structured, prioritized report.

#### Scenario: Report summary
- **WHEN** verification completes
- **THEN** display summary scorecard:
  ```text
  ## Verification Report: <change-name>

  ### Summary
  | Dimension    | Status   |
  |--------------|----------|
  | Completeness | X/Y      |
  | Correctness  | X/Y      |
  | Coherence    | Followed |
  ```

#### Scenario: Issue prioritization
- **WHEN** issues are found
- **THEN** group and display in priority order:
  1. CRITICAL - Must fix before archive (missing implementation, incomplete tasks, demonstrated contract violations)
  2. WARNING - Should fix (demonstrated divergence, missing scenario coverage, material evidence gaps)
  3. SUGGESTION - Nice to fix (pattern inconsistencies, low-risk evidence gaps, minor improvements)

#### Scenario: Adversarial evidence summary
- **WHEN** verification completes
- **THEN** summarize the falsification attempts performed and their outcomes
- **AND** identify any UNVERIFIED claims and why they could not be checked
- **AND** when no defects are found, state which negative or boundary paths were inspected

#### Scenario: Actionable recommendations
- **WHEN** reporting an issue
- **THEN** include specific, actionable fix recommendation
- **AND** reference relevant files and line numbers where applicable
- **AND** avoid vague suggestions like "consider reviewing"

#### Scenario: All checks pass
- **WHEN** no issues found across all dimensions
- **THEN** display:
  ```text
  All checks passed. Ready for archive.
  ```

#### Scenario: Critical issues found
- **WHEN** CRITICAL issues exist
- **THEN** display:
  ```text
  X critical issue(s) found. Fix before archiving.
  ```
- **AND** do NOT suggest running archive

#### Scenario: Only warnings/suggestions
- **WHEN** no CRITICAL issues but warnings exist
- **THEN** display:
  ```text
  No critical issues. Y warning(s) to consider.
  Ready for archive (with noted improvements).
  ```

### Requirement: Flexible Artifact Handling
The agent SHALL gracefully handle changes with varying artifact completeness.

#### Scenario: Minimal change (tasks only)
- **WHEN** change has only tasks.md
- **THEN** verify task completion only
- **AND** skip spec and design checks
- **AND** note which checks were skipped

#### Scenario: Change with specs but no design
- **WHEN** change has tasks.md and delta specs but no design.md
- **THEN** verify completeness and correctness
- **AND** skip design adherence
- **AND** still check code coherence against project patterns

#### Scenario: Full change (all artifacts)
- **WHEN** change has proposal, design, specs, and tasks
- **THEN** perform all verification checks
- **AND** run the adversarial pass across requirements, scenarios, and design decisions
- **AND** cross-reference artifacts for consistency
