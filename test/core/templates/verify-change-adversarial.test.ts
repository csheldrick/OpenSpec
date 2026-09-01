import { describe, expect, it } from 'vitest';

import {
  getOpsxVerifyCommandTemplate,
  getVerifyChangeSkillTemplate,
} from '../../../src/core/templates/skill-templates.js';

describe('verify workflow adversarial review', () => {
  const variants: Array<[string, string]> = [
    ['skill', getVerifyChangeSkillTemplate().instructions],
    ['command', getOpsxVerifyCommandTemplate().content],
  ];

  it.each(variants)('%s actively tries to falsify implementation claims', (_variant, content) => {
    expect(content).toContain('actively try to **falsify**');
    expect(content).toContain('boundary values, negative/error paths, alternate states, and cross-component interactions');
    expect(content).toContain('A passing test does not prove a requirement');
    expect(content).toContain('Keyword/symbol presence does not prove a requirement');
  });

  it.each(variants)('%s separates demonstrated failures from verification gaps', (_variant, content) => {
    expect(content).toContain('Do not turn uncertainty into a defect');
    expect(content).toContain('**FAILED**: concrete evidence contradicts the artifact');
    expect(content).toContain('**WEAK EVIDENCE**: behavior may be correct');
    expect(content).toContain('**UNVERIFIED**: validation could not be performed');
    expect(content).toContain('Do not report speculative defects');
  });

  it.each(variants)('%s runs the adversarial pass before final coherence/reporting', (_variant, content) => {
    const correctness = content.indexOf('**Verify Correctness**');
    const adversarial = content.indexOf('**Run an adversarial pass**');
    const coherence = content.indexOf('**Verify Coherence**');
    const report = content.indexOf('**Generate Verification Report**');

    expect(correctness).toBeGreaterThanOrEqual(0);
    expect(adversarial).toBeGreaterThan(correctness);
    expect(coherence).toBeGreaterThan(adversarial);
    expect(report).toBeGreaterThan(coherence);
  });

  it.each(variants)('%s requires evidence-backed defect reports', (_variant, content) => {
    expect(content).toContain('Every reported defect MUST include: the artifact claim, the contradicting implementation/test evidence, and the concrete failure mechanism');
    expect(content).toContain('Summarize the falsification attempts performed and their outcomes');
    expect(content).toContain('state which negative/boundary paths were inspected');
  });
});
