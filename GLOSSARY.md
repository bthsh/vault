# GLOSSARY.md — Key Terms

**TEE (Trusted Execution Environment)** — A hardware-enforced, isolated
region of a processor where code and data are protected from the rest of
the system, including the host operating system, hypervisor, and any
user with root/admin access. Examples: Intel TDX, AMD SEV-SNP, ARM
TrustZone.

**Data-in-use** — Data that is actively being processed (in RAM/VRAM), as
opposed to data-in-transit (moving over a network, protected by TLS/
HTTPS) or data-at-rest (stored on disk, protected by disk encryption).
This project's core focus.

**Attestation (remote attestation)** — A cryptographic process where a
TEE proves to a remote party that it is running genuine, untampered code
inside a real hardware enclave, before that party sends any sensitive
data to it.

**Fernet** — A symmetric encryption scheme (part of Python's
`cryptography` library) combining AES-128-CBC encryption with HMAC-SHA256
authentication, designed to be simple and hard to misuse.

**Quantization** — A technique for shrinking a neural network's file size
and memory footprint by storing its weights with fewer bits of precision
(e.g. 4-bit instead of 16-bit), trading a small amount of accuracy for
significantly faster loading and inference.

**GGUF** — A file format used by llama.cpp to package a quantized LLM's
weights and metadata into a single portable file.

**llama.cpp** — An open-source C++ inference engine for running LLMs
efficiently on CPUs (and GPUs), widely used for local/offline model
deployment.

**Gramine** — A Library OS (LibOS) that allows unmodified applications
(like a Python + llama.cpp server) to run inside a hardware TEE without
being rewritten, by providing an OS-like interface inside the enclave.

**CVE-2023-4969 ("LeftoverLocals")** — A real vulnerability disclosed by
Trail of Bits in January 2024, allowing an attacker to recover leftover
data from GPU local memory shared between processes on Apple, Qualcomm,
AMD, and Imagination GPUs — proven to leak live LLM session data.

**`/proc/[pid]/mem`** — A Linux virtual filesystem interface that exposes
a running process's memory contents, readable by a user with sufficient
privilege (typically root). Used by this project's attack tool as a
standard, non-exploit-based way to demonstrate data-in-use exposure.

**Zero-trust** — A security model that assumes no implicit trust in any
part of the system (network, host OS, administrators) and requires
verification (e.g. via cryptographic attestation) at every step, rather
than trusting a perimeter or a privacy policy.

**Data-in-use protection gap** — This project's central thesis: network
encryption (TLS) and disk encryption solve two of the three states data
can be in, but the third — data actively being computed on — is left
exposed by most "local AI" setups today.
