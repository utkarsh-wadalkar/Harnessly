# Spec 05: Curated benchmark pack and uncertainty

The global MVP pack has exactly ten initial curated tasks spanning bug fixes, feature implementation, test work and refactoring, primarily TypeScript and Python. Each family and both languages must appear; task metadata records distribution so scope is inspectable. Every task includes pinned repository snapshot/base SHA, setup, visible feedback tests, separate protected acceptance tests, family/tags/difficulty, grader version and a maintainer-verified reference fix.

Run at least three independent trials for every supported harness/task pair on the fixed coding model: with two harnesses and ten tasks, at least 60 standard attempts before infrastructure retries. Pin conditions and supported sampling parameters; disclose unsupported seeds, tools or provider caching effects. Retries do not inflate the number of independent successful trials.

Report raw solved/attempt counts, exclusions, infrastructure outcomes, observed coverage, elapsed-time dispersion and success uncertainty with method and sample size. Avoid unsupported precision or statistical-significance claims. Aggregate only comparable controlled global evidence. Personal task selection stays private and separate. Optional factorial runs must identify harness/model factors independently.

Given a task reference fix fails protected grading, when pack validation runs, then that task cannot publish. Given missing usage, when results aggregate, then token/cost coverage remains unknown. Given infrastructure retry, when trial counts aggregate, then its attempt history stays attached to the original trial. Given a personal run, when global aggregates refresh, then it is excluded.

Required validation: all ten reference fixes and intentionally failing patches; hidden grader non-exposure; manifest/comparability checks; raw count and uncertainty calculation fixtures; real three-trial execution evidence before claiming completed comparison.

