# Devpost submission copy

## Project name
AFTERLIGHT — Solar claims with an alibi

## Elevator pitch
AI screens solar generation against weather. Ethereum stops the same asset-hour from being claimed twice. Portable evidence lets anyone inspect the story behind each certificate.

## Track
Renewable Energy & Energy Trading — renewable certificate tracking.

## Inspiration
A blockchain can preserve a bad claim forever. An AI dashboard can flag an anomaly and still let the same electrons be sold twice. We wanted to close the gap between those two systems: before clean energy gets a certificate, it should have an alibi.

Our starting question was deliberately simple: what if a solar installation claimed production after sunset? Then we made the attacks subtler: production below installed capacity but above the weather envelope; a shifted clock that preserves the daily total; and a second certificate with different evidence for the same physical intervals.

## What it does
AFTERLIGHT is a verification desk for solar cooperatives, certificate issuers and clean-energy buyers. Submit 24 hourly readings for the demonstration installation. A learned weather-to-power model and explicit screening rules classify the claim as pass, review or reject. Inspect the hourly chart, see the reason for every flag, and download the complete evidence.

Only a passing claim can be issued through the authorized verifier. A real Solidity contract on a persistent local Ethereum chain records the asset, day, quantity and evidence Merkle root. It reserves all 24 registered asset-hours atomically. A second issuance for those intervals reverts even if the evidence root changes. The certificate owner can retire it permanently for a beneficiary.

The evidence lab invites the reviewer to attack the system: challenge duplicate issuance directly against the contract, or change one reading and watch the Merkle check fail.

## How we built it
The repository includes a real European Commission JRC PVGIS reference download: 8,760 hourly records for İzmir in 2023. We trained a ridge-regression surrogate using irradiance, nonlinear irradiance terms, and weather interactions. January–June fits the model, July–September calibrates a nominal 90% interval, and October–December remains held out. On the held-out daylight samples the mean error is 0.306 kW and empirical coverage is 94.1%.

The reference power is PVGIS modeled output, not measured telemetry; these are surrogate-model metrics rather than real-world fraud accuracy. Demonstration claims are clearly labelled reference-derived scenarios. A passing result supports an independent verifier and does not prove meter authenticity.

The rest is a compact Node.js application: an original responsive interface, SHA-256 Merkle evidence, ethers, a compiled Solidity contract, and Ganache with persistent storage. No API key or externally hosted blockchain is needed to reproduce the demo after installation.

## What makes it different
We made adversarial verification the main product experience. The judge does not need to trust a green success badge: they can try the attacks.

Three distinct responsibilities are visible: AI assesses consistency, the evidence root exposes edits, and the contract enforces interval uniqueness and retirement. The subtle peak attack demonstrates why installed-capacity rules alone are insufficient. The shifted-clock attack demonstrates why daily totals alone are insufficient. The changed-root replay demonstrates why hashing a certificate alone is insufficient.

## Climate impact and usefulness
Credible clean-energy claims help organizations procure renewables with greater confidence. Our demonstrated impact is narrow and measurable: 72 invented night kWh are flagged, a subtler daytime inflation requires review, and duplicate issuance is prevented within the registry. We do not translate those figures into avoided CO₂ or claim accredited renewable certificates.

The adoption path is a verification layer for existing registries and community solar operators, rather than a new speculative token. Readings can be imported, evidence can be exported, and an issuer can integrate the screening before issuance. Production adoption requires independent asset identity, signed revenue-grade meters, multiple oracle signers, real-installation validation, registry interoperability, and contract auditing.

## Challenges and lessons
An immutable record is not automatically a true record. We separated integrity, plausibility and authenticity, and chose review rather than automatic correction when evidence is uncertain. We also tested interval replay under a changed root, permissions, source/model fingerprints, one-way retirement, and persistence after a chain restart.

## Accomplishments
The working prototype includes four adversarial case files, arbitrary readings import for the demo asset/day, portable evidence, real EVM issuance and retirement, a guided walkthrough and 16 passing tests. The full HTTP workflow was also exercised, with reproducible transaction and evidence artifacts included.

## Built with
JavaScript, Node.js, Solidity, ethers, Ganache, solc, ridge regression, conformal calibration, SHA-256 Merkle trees, European Commission JRC PVGIS, HTML, CSS, SVG, Bricolage Grotesque, Deepgram Aura-2 Thalia. AI-assisted development; narration synthesized with Deepgram TTS; original motion graphics and a synthesized ambient-electronic score with speech-driven ducking.

## Before submitting

- Publish the repository and insert its public URL in Devpost.
- Upload `artifacts/afterlight-demo.mp4` to an accepted video host and insert that URL.
- Provide the video and repository as the reproducible proof of concept; the app currently runs locally.
- Confirm participant/team eligibility in Devpost. Its overview and rules page describe eligibility differently.
- Submit before **25 October 2026, 19:30 IST** (17:00 UTC+03:00).

No account registration, public repository publication, video upload, or Devpost submission has been performed by this local build.
