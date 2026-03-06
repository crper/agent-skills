# Chrome Web Store Submission

English | [简体中文](./README.zh.md)

Prepare copy-and-paste Chrome Web Store submission content for browser extensions, including policy fields, permission rationale, privacy/data-use answers, reviewer notes, and store listing copy.

## Scope

- Best for **submission text and compliance copy**
- Works well for **single-language** or **bilingual** output
- Keeps output in a **stable field order** for direct copy-paste

## Project Structure

- `SKILL.md` — skill instructions and workflow
- `references/field-templates.md` — reusable field wording and stable output order
- `evals/evals.json` — minimal prompts for future regression checks

## Best Use Cases

- Filling the Chrome Web Store listing form
- Writing single-purpose statements
- Explaining why permissions are required
- Answering remote-code questions
- Drafting data-use disclosures
- Producing short and detailed store descriptions

## Output Style

The skill can produce:

- Chinese only
- English only
- Chinese + English bilingual output

Default stable field order:

1. Single Purpose
2. Permission rationale for requested permissions only
3. Remote Code
4. Data Use
5. Store descriptions
6. Reviewer note

## Notes

- This skill inspects the current extension code before drafting answers
- It only writes rationale for permissions that are actually requested by the extension
- It is designed for **copy-and-paste submission content**, not for automated publishing
- It should always prefer precise, reviewer-friendly wording over marketing language
