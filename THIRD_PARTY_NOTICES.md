# Third-party components and review status

Original HarnessArena code/documentation is Apache-2.0; the repository's prior GPL-3.0 template is intentionally replaced at the owner's instruction. No third-party application implementation has been copied into HarnessArena. This file is a dependency-review register, not a claim that all future redistribution is licensed.

| Component | Relationship | Source / review |
| --- | --- | --- |
| LAYA | Official upstream source used as a remote Docker build context; source/checkpoint revisions pinned | [Apache-2.0 source](https://github.com/NandhaKishorM/laya/blob/main/LICENSE); preserve its license in runtime image; checkpoint/encoder redistribution review remains a release gate. |
| Gemma 4 | Hosted API integration planned; no weights redistributed | [Official model card](https://ai.google.dev/gemma/docs/core/model_card_4); model license and hosted API terms are distinct. |
| OpenCode / Aider | External harness subprocess adapters planned; no forks bundled | Inspect licenses at the exact supported commits before distributing images. |
| Qwen coding model | Hosted coding endpoint candidate; no weights included | Verify the exact checkpoint/provider identifier and corresponding model/API terms during the live probe. |
| PostgreSQL | Development infrastructure image | Preserve image notices and verify the deployed digest at release. |
| Python validation dependencies | Development/contract tooling, pinned in requirements.lock | Capture package license metadata in release inventory; no blanket license substitution. |

Before release, record each deployed package/image/model revision, license identifier, required notices and adapted code. Hosted endpoint eligibility, pricing and licensing claims must be supported by current provider sources. This milestone does not authorize publishing incomplete or unreviewed model weights.
