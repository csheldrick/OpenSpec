import { describe, expect, it } from 'vitest';
import { CANONICAL_INVOCATION } from '../../src/core/command-generation/invocation.js';
import {
  getSkillReferenceTransformer,
  transformCommandInvocations,
  transformToSkillReferences,
} from '../../src/utils/command-references.js';
import { getApplyChangeSkillTemplate } from '../../src/core/templates/index.js';

describe('flat canonical workflow invocations', () => {
  it('uses /opsx- as the raw canonical form', () => {
    expect(CANONICAL_INVOCATION).toEqual({ style: 'flat', prefix: '/' });
    const apply = getApplyChangeSkillTemplate().instructions;
    expect(apply).toContain('/opsx-apply');
    expect(apply).not.toContain('/opsx:');
  });

  it('normalizes both canonical and legacy references for each target surface', () => {
    expect(transformToSkillReferences('Use /opsx-apply next')).toBe('Use /openspec-apply-change next');
    expect(transformToSkillReferences('Use /opsx:apply next')).toBe('Use /openspec-apply-change next');
    expect(getSkillReferenceTransformer('codex')('Use /opsx-apply next')).toBe('Use $openspec-apply-change next');
    expect(transformCommandInvocations('Use /opsx-apply next', { style: 'namespaced', prefix: '/' }))
      .toBe('Use /opsx:apply next');
    expect(transformCommandInvocations('Use /opsx:apply next', { style: 'flat', prefix: '/' }))
      .toBe('Use /opsx-apply next');
  });
});
