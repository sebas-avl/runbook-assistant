# Evaluation results

Run on 2026-11-17 against `POST /ask` with the three Kubernetes docs in `data/docs/`.
`MIN_SCORE = 0.25`, calibrated with only these 6 questions.

| # | Question | Expected source | Source returned | Top score | Result |
|---|----------|-----------------|-----------------|-----------|--------|
| 1 | What is a Pod? | pods.md | pods.md | 0.742 | pass |
| 2 | How do I expose an app outside the cluster? | services.md | services.md | 0.456 | pass |
| 3 | How do I update an application without downtime? | deployments.md | deployments.md | 0.329 | pass |
| 4 | What happens to my pods if one of them crashes? | pods.md | pods.md | 0.386 | pass |
| 5 | What types of Service exist? | services.md | services.md | 0.426 | pass |
| 6 | What is the best pizza recipe? | none | none ("I don't know") | 0.138 | pass |

## Notes

- Question 4: expected source corrected from `deployments.md` to `pods.md` after reading the retrieved chunk, which contains the answer.
- Question 2: the YAML in the answer is cut off, because chunks are split every 800 characters without respecting lines.
- Question 3: the source is right, but the answer talks about pausing a rollout instead of rolling updates.
- Retrieved chunks contain leftovers from the Kubernetes site generator (`{{< ... >}}` tags).
- Other documents (2026-11-17): with this repository's README as the only document, "Which Python version does the project need?" scored 0.169 and the requirements chunk was not in the top 3, so `/ask` answered "I don't know". "What do I need to run the project locally?" found it with 0.251. Character-based chunking mixes sections, so short, specific questions can miss details.
