from pathlib import Path


def replace_exact(text: str, old: str, new: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"expected {expected} occurrences, found {count}: {old[:80]!r}")
    return text.replace(old, new)


workflow = Path("src/core/templates/workflows/verify-change.ts")
text = workflow.read_text()

skill_input = r'''**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.'''
skill_input_new = r'''**Input**: Optionally specify a change name. Add \`--adversarial\` to opt into a deeper falsification pass (for example, \`/opsx:verify add-auth --adversarial\`). Parse \`--adversarial\` as workflow input before change selection: remove it from the positional input, never treat it as a change name, and never append it to any \`openspec\` CLI command. If the flag is absent, run the standard verification only. If the change name is omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.'''
text = replace_exact(text, skill_input, skill_input_new)

command_input = r'''**Input**: Optionally specify a change name after \`/opsx:verify\` (e.g., \`/opsx:verify add-auth\`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.'''
command_input_new = r'''**Input**: Optionally specify a change name after \`/opsx:verify\` (e.g., \`/opsx:verify add-auth\`). Add \`--adversarial\` anywhere after the command to opt into a deeper falsification pass (e.g., \`/opsx:verify add-auth --adversarial\`). Parse \`--adversarial\` as workflow input before change selection: remove it from the positional input, never treat it as a change name, and never append it to any \`openspec\` CLI command. If the flag is absent, run the standard verification only. If the change name is omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.'''
text = replace_exact(text, command_input, command_input_new)

text = replace_exact(
    text,
    "   If a name is provided, use it. Otherwise:",
    "   If a name remains after removing workflow flags, use it. Otherwise:",
    expected=2,
)

adversarial_block = r'''8. **Optional adversarial pass (\`--adversarial\` only)**

   If \`--adversarial\` was not provided, skip this entire step. Do not spend tokens on adversarial claim selection, counterexample search, or extra validation.

   When enabled, reuse the evidence already gathered above rather than repeating broad discovery.

   **Build a bounded claim set**:
   - Inventory behavioral claims from requirements, scenarios, completed task outcomes, and explicit design decisions
   - Prioritize claims touching changed implementation paths first, then high-risk boundaries/error paths and cross-component behavior, then other contract-important claims
   - Review at most 5 important claims in one invocation; if fewer than 5 important claims exist, review all of them
   - Record important claims beyond the budget as \`UNCHECKED\`; summarize lower-priority unchecked claims too, so the report never implies exhaustive coverage

   **Try to falsify each selected claim**:
   - Trace the actual execution path instead of treating symbol/keyword presence as proof
   - Inspect whether relevant tests assert the required outcome instead of treating a passing suite as proof
   - Try a plausible boundary, negative/error, alternate-state, or cross-component counterexample
   - When practical, run the smallest focused executable validation that could disprove the claim
   - Classify the result as \`FAILED\`, \`WEAK EVIDENCE\`, \`SUPPORTED\`, or \`UNVERIFIED\`
   - Every \`FAILED\` result must cite the artifact claim, contradicting implementation/test evidence, and concrete failure mechanism
   - Missing tooling or environment produces \`UNVERIFIED\`, not an invented defect

   **Determine adversarial readiness from claim outcomes, not issue severity**:
   - Any \`FAILED\` important claim -> **Not ready**
   - Any important \`WEAK EVIDENCE\` or \`UNVERIFIED\` claim -> **Partially verified — not ready**
   - Any important claim left \`UNCHECKED\` because of the budget -> **Partially verified — not ready**
   - **Ready** only when every important claim is \`SUPPORTED\`; lower-priority \`UNCHECKED\` remainder may exist but must be reported explicitly'''

text = replace_exact(
    text,
    "8. **Generate Verification Report**",
    adversarial_block + "\n\n9. **Generate Verification Report**",
    expected=2,
)

baseline_assessment = r'''   **Final Assessment**:
   - If CRITICAL issues: "X critical issue(s) found. Fix before archiving."
   - If only warnings: "No critical issues. Y warning(s) to consider. Ready for archive (with noted improvements)."
   - If all clear: "All checks passed. Ready for archive."'''
assessment_new = baseline_assessment + r'''

   **Adversarial Assessment** (\`--adversarial\` only):
   - Add a compact checked-claims table with each selected claim and its \`FAILED\`, \`WEAK EVIDENCE\`, \`SUPPORTED\`, or \`UNVERIFIED\` outcome
   - Add an \`UNCHECKED\` remainder section, distinguishing important claims skipped because of the budget from lower-priority claims not selected
   - End with the adversarial readiness from claim outcomes above. This readiness is independent of CRITICAL/WARNING/SUGGESTION issue counts
   - Do not use the baseline "All checks passed" terminal line as the adversarial readiness result'''
text = replace_exact(text, baseline_assessment, assessment_new, expected=2)

workflow.write_text(text)

spec = Path("openspec/specs/opsx-verify-skill/spec.md")
spec_text = spec.read_text()
spec_text = replace_exact(
    spec_text,
    "Define `/opsx:verify` behavior for assessing implementation completeness, correctness, and coherence against change artifacts.",
    "Define `/opsx:verify` behavior for assessing implementation completeness, correctness, and coherence against change artifacts, including an opt-in bounded adversarial mode.",
)

adversarial_spec = r'''### Requirement: Optional Adversarial Verification
The agent SHALL support `--adversarial` as an explicit opt-in mode of the existing verify workflow while preserving standard verification behavior when the mode is absent.

#### Scenario: Standard verification remains the default
- **WHEN** `/opsx:verify <change-name>` is invoked without `--adversarial`
- **THEN** the agent performs the existing completeness, correctness, and coherence checks
- **AND** does not perform adversarial claim selection, counterexample search, or extra validation
- **AND** uses the existing baseline report and archive-readiness assessment

#### Scenario: Adversarial flag is workflow input
- **WHEN** `/opsx:verify <change-name> --adversarial` is invoked
- **THEN** the agent removes `--adversarial` from positional input before selecting the change
- **AND** does not treat `--adversarial` as a change name
- **AND** does not forward `--adversarial` to any `openspec` CLI command

#### Scenario: Adversarial effort is bounded and prioritized
- **WHEN** adversarial mode is enabled
- **THEN** the agent reuses evidence gathered by standard verification
- **AND** prioritizes claims touching changed implementation paths, high-risk boundaries and error paths, cross-component behavior, and other contract-important behavior
- **AND** checks at most 5 important claims in one invocation
- **AND** reports important claims beyond the budget as `UNCHECKED`
- **AND** reports the lower-priority unchecked remainder explicitly rather than implying exhaustive coverage

#### Scenario: Selected claims are actively challenged
- **WHEN** an important claim is selected for adversarial verification
- **THEN** the agent traces the relevant execution path
- **AND** inspects whether tests assert the required outcome
- **AND** tries a plausible boundary, negative/error, alternate-state, or cross-component counterexample
- **AND** runs the smallest focused executable validation when practical
- **AND** classifies the claim as `FAILED`, `WEAK EVIDENCE`, `SUPPORTED`, or `UNVERIFIED`

#### Scenario: Failed important claim blocks readiness
- **WHEN** any important claim is `FAILED`
- **THEN** the adversarial final assessment is `Not ready`
- **AND** the result includes the artifact claim, contradicting evidence, and concrete failure mechanism

#### Scenario: Weak or unavailable evidence blocks readiness
- **WHEN** no important claim is `FAILED`
- **AND** any important claim is `WEAK EVIDENCE` or `UNVERIFIED`
- **THEN** the adversarial final assessment is `Partially verified — not ready`

#### Scenario: Important claim remains unchecked
- **WHEN** no important claim is `FAILED`, `WEAK EVIDENCE`, or `UNVERIFIED`
- **AND** an important claim is `UNCHECKED` because the adversarial budget was exhausted
- **THEN** the adversarial final assessment is `Partially verified — not ready`

#### Scenario: Important claims are supported
- **WHEN** every important claim is `SUPPORTED`
- **THEN** the adversarial final assessment is `Ready`
- **AND** any lower-priority `UNCHECKED` remainder is still reported explicitly
- **AND** the report does not claim exhaustive proof

'''
spec_text = replace_exact(
    spec_text,
    "### Requirement: Completeness Verification\n",
    adversarial_spec + "### Requirement: Completeness Verification\n",
)
spec.write_text(spec_text)

docs = Path("docs-lab/reference/skills.md")
docs_text = docs.read_text()
docs_text = replace_exact(
    docs_text,
    "| **Arguments** | A change proposal name, optional. When ambiguous it asks, listing change proposals that have a tasks artifact. |",
    "| **Arguments** | A change proposal name, optional. Add `--adversarial` to opt into a bounded falsification pass; this mode intentionally spends more model tokens/work than standard verification. When ambiguous it asks, listing change proposals that have a tasks artifact. `--adversarial` is workflow-only and is never forwarded to an `openspec` CLI command. |",
)
docs_text = replace_exact(
    docs_text,
    "| **Response** | A report: a scorecard for Completeness, Correctness, and Coherence, then CRITICAL, WARNING, and SUGGESTION issues with recommendations, and a final archive-readiness assessment. It changes nothing and does not archive. |",
    "| **Response** | Standard mode returns the existing scorecard for Completeness, Correctness, and Coherence, then CRITICAL, WARNING, and SUGGESTION issues with recommendations and the normal archive-readiness assessment. With `--adversarial`, it also reports the bounded set of checked claims, the explicit `UNCHECKED` remainder, and readiness derived from claim outcomes (`FAILED`, `WEAK EVIDENCE`, `SUPPORTED`, `UNVERIFIED`). It changes nothing and does not archive. |",
)
docs.write_text(docs_text)

changeset = Path(".changeset/adversarial-verify.md")
changeset.write_text('''---\n"@fission-ai/openspec": patch\n---\n\nAdd an opt-in `--adversarial` mode to `/opsx:verify` that bounds falsification effort, reports checked and unchecked claims, and derives readiness from claim outcomes without changing standard verification behavior.\n''')

test = Path("test/core/templates/verify-change-adversarial.test.ts")
test.write_text(r'''import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

import {
  getOpsxVerifyCommandTemplate,
  getVerifyChangeSkillTemplate,
} from '../../../src/core/templates/skill-templates.js';

const variants: Array<[string, string]> = [
  ['verify skill', getVerifyChangeSkillTemplate().instructions],
  ['verify command', getOpsxVerifyCommandTemplate().content],
];

describe('verify adversarial mode', () => {
  it('keeps standard verification as the default path', () => {
    for (const [variant, content] of variants) {
      expect(content, variant).toContain('If the flag is absent, run the standard verification only.');
      expect(content, variant).toContain(
        'If `--adversarial` was not provided, skip this entire step. Do not spend tokens on adversarial claim selection, counterexample search, or extra validation.'
      );

      const coherence = content.indexOf('7. **Verify Coherence**');
      const adversarial = content.indexOf('8. **Optional adversarial pass (`--adversarial` only)**');
      const report = content.indexOf('9. **Generate Verification Report**');
      expect(coherence, variant).toBeGreaterThanOrEqual(0);
      expect(adversarial, variant).toBeGreaterThan(coherence);
      expect(report, variant).toBeGreaterThan(adversarial);
    }
  });

  it('parses --adversarial as workflow input rather than a change or CLI flag', () => {
    for (const [variant, content] of variants) {
      expect(content, variant).toContain('remove it from the positional input');
      expect(content, variant).toContain('never treat it as a change name');
      expect(content, variant).toContain('never append it to any `openspec` CLI command');
      expect(content, variant).toContain('If a name remains after removing workflow flags, use it. Otherwise:');
    }
  });

  it('bounds and prioritizes the adversarial claim set', () => {
    for (const [variant, content] of variants) {
      expect(content, variant).toContain('Prioritize claims touching changed implementation paths first');
      expect(content, variant).toContain('Review at most 5 important claims in one invocation');
      expect(content, variant).toContain('Record important claims beyond the budget as `UNCHECKED`');
      expect(content, variant).toContain('the report never implies exhaustive coverage');
    }
  });

  it('drives adversarial readiness from claim outcomes', () => {
    for (const [variant, content] of variants) {
      expect(content, variant).toContain('Any `FAILED` important claim -> **Not ready**');
      expect(content, variant).toContain(
        'Any important `WEAK EVIDENCE` or `UNVERIFIED` claim -> **Partially verified — not ready**'
      );
      expect(content, variant).toContain(
        'Any important claim left `UNCHECKED` because of the budget -> **Partially verified — not ready**'
      );
      expect(content, variant).toContain('**Ready** only when every important claim is `SUPPORTED`');
      expect(content, variant).toContain('This readiness is independent of CRITICAL/WARNING/SUGGESTION issue counts');
      expect(content, variant).toContain(
        'Do not use the baseline "All checks passed" terminal line as the adversarial readiness result'
      );
    }
  });

  it('documents the opt-in syntax and cost tradeoff in the canonical skills reference', () => {
    const docs = readFileSync('docs-lab/reference/skills.md', 'utf8');
    const verifySection = docs.slice(docs.indexOf('## openspec-verify-change'));

    expect(verifySection).toContain('`--adversarial`');
    expect(verifySection).toContain('more model tokens/work than standard verification');
    expect(verifySection).toContain('workflow-only and is never forwarded to an `openspec` CLI command');
    expect(verifySection).toContain('the explicit `UNCHECKED` remainder');
    expect(verifySection).toContain('readiness derived from claim outcomes');
  });
});
''')

print("Applied #1752 opt-in adversarial verification refresh")
