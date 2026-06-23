# STRIDE Threat Modeling Reference

STRIDE is a security threat modeling framework developed by Microsoft to help identify and classify potential security vulnerabilities during system design. It is structured around six threat categories, each directly mapped to a key security property that we aim to protect:

| Pillar | Threat Description | Security Property | Code/Architectural Example |
| :--- | :--- | :--- | :--- |
| **S**poofing | Impersonating a user, system, or service | **Authenticity** | An attacker masquerading as a registered client by supplying arbitrary or unverified credentials. |
| **T**ampering | Unauthorized modification of data or code | **Integrity** | Modifying parameters in a request to alter data or state (e.g. altering price values in an order payload). |
| **R**epudiation | Denying that an action was taken due to lack of proof | **Non-repudiation** | An attacker performing critical actions (like deleting records or redeeming codes) without leaving audit trails. |
| **I**nformation Disclosure | Exposing confidential data to unauthorized parties | **Confidentiality** | Leaking sensitive API tokens, PII (Personally Identifiable Information), or raw database exception stacks in client errors. |
| **D**enial of Service | Overwhelming resources to block legitimate access | **Availability** | Exhausting database/LLM resources via unbounded recursive loops, infinite execution timeouts, or lack of query limits. |
| **E**elevation of Privilege | Gaining unauthorized access to restricted features | **Authorization** | A guest user directly invoking admin APIs or executing commands bypassing role verification checks. |

## How It is Used

1.  **Decompose the System**: Map data flow diagrams (DFDs), boundary points, trust boundaries, data stores, and external interactors.
2.  **Apply STRIDE**: Analyze each boundary point or data flow against each of the six pillars.
3.  **Define Mitigations**: Choose standard, secure paved-road patterns (like Pydantic validations, strict role-based access, and secure logging) to neutralize the identified threats.
