# Dependency and runtime policy

Production and CI target Python 3.11; the current Windows validation environment uses Python 3.13.3. `requirements.lock` pins the resolved development/test dependency set; it is installed before editable project installation. CI checks Python 3.11 and 3.13. Production runtime verification is recorded separately from host unit tests.

LAYA is built from official source commit `68804629e8ccd9d616d48a40e87de9fabbeae069`, using its CPU-only Dockerfile and `laya-serve` entry point. The typed checkpoint revision is `1a793eb568e6718f15941d08f85432581df534e3`. The upstream Dockerfile still resolves transitive packages during build; capture the resolved package set, base image digest, final image digest and model artifact hashes in the live prototype report before claiming a reproducible validated deployment. The checked-in source/checkpoint pins alone are not runtime evidence.

`postgres:17.6` is a development tag, not benchmark provenance. Runtime benchmark/grader images must be pinned by digest. No GPU override, CUDA runtime, paid Docker security feature, local GPU or cloud worker is assumed.

The frontend workspace is reserved but not installed; choose and lock actual Next.js/Tailwind/accessibility dependencies when its first accepted workflow ticket is implemented. Do not claim a runnable web application from the workspace declaration.
