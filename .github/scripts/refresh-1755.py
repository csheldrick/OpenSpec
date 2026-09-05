from pathlib import Path


def replace_exact(text: str, old: str, new: str, expected: int | None = None) -> str:
    count = text.count(old)
    if expected is not None and count != expected:
        raise RuntimeError(f"expected {expected} occurrences, found {count}: {old[:120]!r}")
    if count == 0:
        raise RuntimeError(f"pattern not found: {old[:120]!r}")
    return text.replace(old, new)

# Canonical invocation becomes flat slash form.
p = Path('src/core/command-generation/invocation.ts')
text = p.read_text()
text = replace_exact(
    text,
    "export const CANONICAL_INVOCATION: CommandInvocation = { style: 'namespaced', prefix: '/' };",
    "export const CANONICAL_INVOCATION: CommandInvocation = { style: 'flat', prefix: '/' };",
    1,
)
text = text.replace('canonical `/opsx:<id>`', 'canonical `/opsx-<id>`')
text = text.replace('canonical `/opsx:<id>` that', 'canonical `/opsx-<id>` that')
p.write_text(text)

# Command generation always normalizes references so legacy colon-form content
# cannot leak even when the target itself uses the flat canonical form.
p = Path('src/core/command-generation/generator.ts')
text = p.read_text()
text = text.replace("import { getInvocationForAdapter, needsInvocationRewrite } from './invocation.js';", "import { getInvocationForAdapter } from './invocation.js';")
text = text.replace('Command bodies are authored with `/opsx:<id>` references.', 'Command bodies are authored with `/opsx-<id>` references.')
old = """  const formatted = needsInvocationRewrite(invocation)\n    ? { ...content, body: transformCommandInvocations(content.body, invocation) }\n    : content;"""
new = """  const formatted = { ...content, body: transformCommandInvocations(content.body, invocation) };"""
text = replace_exact(text, old, new, 1)
p.write_text(text)

# Accept both legacy colon and canonical hyphen input everywhere references are rewritten.
p = Path('src/utils/command-references.ts')
text = p.read_text()
text = text.replace("import {\n  formatCommandInvocation,\n  needsInvocationRewrite,\n} from '../core/command-generation/invocation.js';", "import { formatCommandInvocation } from '../core/command-generation/invocation.js';")
text = text.replace(r'/\\/opsx:([a-z-]+)/g', r'/\\/opsx[:-]([a-z-]+)/g')
text = text.replace('canonical `/opsx:<command>`', 'canonical `/opsx-<command>`')
text = text.replace('canonical `/opsx:<id>`', 'canonical `/opsx-<id>`')
text = text.replace('canonical `/opsx:*`', 'canonical `/opsx-*`')
old = """  if (invocation !== undefined && needsInvocationRewrite(invocation)) {\n    return (text: string) => transformCommandInvocations(text, invocation);\n  }\n  return undefined;"""
new = """  if (invocation !== undefined) {\n    return (text: string) => transformCommandInvocations(text, invocation);\n  }\n  return undefined;"""
text = replace_exact(text, old, new, 1)
p.write_text(text)

# Raw workflow templates use the flat canonical form. Preserve all newer upstream
# behavior around those references, including the propose natural-language fallback.
for wf in Path('src/core/templates/workflows').glob('*.ts'):
    text = wf.read_text()
    if '/opsx:' in text:
        wf.write_text(text.replace('/opsx:', '/opsx-'))

# Update current upstream tests semantically instead of restoring stale test files.
p = Path('test/core/command-generation/invocation.test.ts')
text = p.read_text()
text = text.replace("body: 'Run /opsx:archive when done. See /opsx:continue for the next artifact.'", "body: 'Run /opsx-archive when done. See /opsx-continue for the next artifact.'")
text = text.replace("expect(needsInvocationRewrite({ style: 'namespaced', prefix: '/' })).toBe(false);\n      expect(needsInvocationRewrite({ style: 'flat', prefix: '/' })).toBe(true);", "expect(needsInvocationRewrite({ style: 'flat', prefix: '/' })).toBe(false);\n      expect(needsInvocationRewrite({ style: 'namespaced', prefix: '/' })).toBe(true);")
text = text.replace("it('leaves command references alone for namespaced tools'", "it('normalizes canonical flat references for namespaced tools'")
text = text.replace("expect(adapter.formatFile(sampleContent), toolId).toContain('/opsx:archive');", "expect(adapter.formatFile(sampleContent), toolId).toContain('/opsx-archive');")
p.write_text(text)

# Existing command-reference tests keep legacy-colon coverage; update the canonical
# no-op/transformer expectations and add coverage for hyphen canonical input.
p = Path('test/utils/command-references.test.ts')
text = p.read_text()
text = text.replace("it('is a no-op for the canonical namespaced slash form'", "it('normalizes canonical flat input for a namespaced slash target'")
text = text.replace("const input = 'Use /opsx:new then /opsx:apply';\n      expect(transformCommandInvocations(input, NAMESPACED_SLASH)).toBe(input);", "const input = 'Use /opsx-new then /opsx-apply';\n      expect(transformCommandInvocations(input, NAMESPACED_SLASH)).toBe('Use /opsx:new then /opsx:apply');")
text = text.replace("it('selects no transformer for namespaced tools when commands are generated', () => {\n    expect(getTransformerForTool('claude', 'both', 'adapter-backed', NAMESPACED_SLASH)).toBeUndefined();\n    expect(getTransformerForTool('claude', 'commands', 'adapter-backed', NAMESPACED_SLASH)).toBeUndefined();\n  });", "it('selects a normalizer for namespaced tools when commands are generated', () => {\n    for (const delivery of ['both', 'commands'] as const) {\n      const transformer = getTransformerForTool('claude', delivery, 'adapter-backed', NAMESPACED_SLASH);\n      expect(transformer?.('/opsx-apply')).toBe('/opsx:apply');\n      expect(transformer?.('/opsx:apply')).toBe('/opsx:apply');\n    }\n  });")
p.write_text(text)

# Template parity assertions refer to authored canonical command syntax.
p = Path('test/core/templates/skill-templates-parity.test.ts')
text = p.read_text().replace('/opsx:', '/opsx-')
p.write_text(text)

# Pin the core compatibility contract explicitly.
p = Path('test/utils/flat-canonical-invocations.test.ts')
p.write_text("""import { describe, expect, it } from 'vitest';\n\nimport { CANONICAL_INVOCATION } from '../../src/core/command-generation/invocation.js';\nimport { getOpsxApplyCommandTemplate } from '../../src/core/templates/skill-templates.js';\nimport {\n  getSkillReferenceTransformer,\n  transformCommandInvocations,\n} from '../../src/utils/command-references.js';\n\ndescribe('flat canonical workflow invocations', () => {\n  it('uses flat slash syntax as the raw canonical form', () => {\n    expect(CANONICAL_INVOCATION).toEqual({ style: 'flat', prefix: '/' });\n    const body = getOpsxApplyCommandTemplate().content;\n    expect(body).toContain('/opsx-');\n    expect(body).not.toContain('/opsx:');\n  });\n\n  it('maps both legacy and canonical command references to skills', () => {\n    const transform = getSkillReferenceTransformer('vibe');\n    expect(transform('/opsx:apply')).toBe('/openspec-apply-change');\n    expect(transform('/opsx-apply')).toBe('/openspec-apply-change');\n  });\n\n  it('maps flat canonical input to namespaced tools', () => {\n    expect(\n      transformCommandInvocations('/opsx-apply', { style: 'namespaced', prefix: '/' })\n    ).toBe('/opsx:apply');\n  });\n\n  it('normalizes legacy colon input for flat tools', () => {\n    expect(transformCommandInvocations('/opsx:apply', { style: 'flat', prefix: '/' })).toBe(\n      '/opsx-apply'\n    );\n  });\n});\n""")

print('Reapplied #1755 semantics onto current upstream main')
