# Claude Code guide · 数仓 Agent 知识库

Claude Code should use [`AGENTS.md`](AGENTS.md) as the canonical project guide for this directory.

Do not maintain a separate rule set here. In particular, follow the data-access rule in `AGENTS.md`: before evaluating `ai_hive`, `ai_ck`, freshness, or Data Agent readiness, first verify live MC and CK connectivity, run lightweight real-table probes, refresh freshness snapshots, then run the required regression.
