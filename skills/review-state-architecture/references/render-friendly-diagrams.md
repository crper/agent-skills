# Render-Friendly Diagram Reference

Use this reference right before drawing the ASCII pre-map or Mermaid diagrams.

Goal: make the review readable in terminals, markdown renderers, and agent pipelines even when Mermaid does not render.

## Contents

- Output layering
- ASCII fallback rules
- Mermaid readability rules
- Terminal and agent compatibility rules
- Label and width rules

## Output Layering

Use a two-layer diagram strategy:

1. **ASCII pre-map first**
   Give the reader a compact text-only mental model before the Mermaid block.
2. **Mermaid second**
   Use Mermaid for the full structured diagram.

Never rely on Mermaid alone to communicate the main structure.

## ASCII Fallback Rules

Default to **ASCII Basic** for maximum compatibility:

- arrows: `->`
- grouping: `[Module]`, `(Flow)`, `{Boundary}`
- splits: `/`, `|`, `+`
- indentation with spaces only

Prefer ASCII Basic when:

- the output may be consumed by another agent
- terminal capabilities are unknown
- the diagram includes many English identifiers or code symbols
- alignment matters more than visual polish

Use **Unicode box drawing** only when all of these are true:

- the environment clearly supports UTF-8 well
- the diagram is small
- the extra visual polish helps human readers more than it risks alignment issues

If unsure, stay with ASCII Basic.

## ASCII Pre-Map Templates

Use one of these compact forms:

### Linear flow

```text
[UI] -> [Page State] -> [Domain Store] -> [Service] -> [API]
```

### Split ownership

```text
[UI]
  -> [Local UI State]
  -> [Form State]
  -> [Domain Store] -> [Service] -> [API]
  -> [Query Cache]  -> [API]
```

### Problem path

```text
[Page] -> [Store A] -> [Effect] -> [Store B]
   \------------------------------->/
```

Keep the ASCII pre-map to the smallest shape that explains the main point.

## Mermaid Readability Rules

Prefer `flowchart LR` unless a top-down structure is clearly easier to read.

Use `subgraph` for stable ownership boundaries:

- screen or page owner
- shared domain state
- server or cache state
- services and IO

Use labeled edges only when the label adds meaning:

- `reads`
- `writes`
- `calls`
- `effects`
- `fetch`
- `response`

If a diagram gets crowded:

- keep only the 1-2 most important paths
- collapse secondary modules into a named group
- shorten labels and explain the full meaning in nearby bullets or tables

## Terminal And Agent Compatibility Rules

- Keep diagrams narrow enough to survive common terminal widths.
- Favor one node per concept. Do not embed paragraphs inside nodes.
- Avoid decorative symbols, emojis, icons, or color-dependent meaning.
- Avoid relying on Mermaid styling directives for essential meaning.
- Keep Mermaid node ids simple and stable.
- Keep ASCII indentation deterministic so another agent can parse the flow.

## Label And Width Rules

Target width:

- ASCII pre-map: ideally within 80 columns, hard cap around 100
- Mermaid node labels: usually 2-5 words

If a real module or store name is long:

- keep the real name if it is essential evidence
- otherwise shorten it in the diagram and map it back in surrounding prose

Good:

```text
[CheckoutPage] -> [CartStore] -> [PricingService]
```

Too dense:

```text
[CheckoutPageStateAndDerivedPromotionsResolver] -> [CartPricingAndCouponMutationCoordinator]
```

## Human-Friendly Layout Rules

- Put the most important path on the first visible line.
- Use vertical stacking only when it clarifies ownership or branching.
- Keep sibling nodes visually aligned.
- Reserve diagonal or crossing ASCII only for the single cycle or duplication that matters.
- If the current problem is "duplicated truth", show the duplication explicitly in the pre-map.

## Distinct Roles Across The 3 Diagrams

Keep the three diagrams visually different:

- **图1**: current problem path, usually messier and narrower in scope
- **图2**: target ownership map, cleaner and grouped by boundary
- **图3**: target runtime flow, one representative end-to-end scenario

Do not redraw the same topology three times with renamed labels.
