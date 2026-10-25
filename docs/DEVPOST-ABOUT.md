## Inspiration

What if a solar installation claimed 72 kWh after sunset? A blockchain could preserve that claim forever without making it true. We built Afterlight around a simple question: does the sun back up the story?

Credible renewable-energy claims matter to community solar operators, certificate issuers and clean-energy buyers. We wanted to make verification something people can inspect and challenge, rather than another green badge they must trust.

## What it does

**Track: Renewable Energy & Energy Trading — renewable certificate tracking.**

Afterlight screens 24 hourly solar readings against weather and a learned power-generation envelope. It separates claims into **PASS, REVIEW or REJECT**, explains each flagged hour and exports the supporting evidence.

The demo invites judges to attack four cases: clean production, invented night generation, an inflated daytime peak and a shifted meter clock. The night attack exposes 72 invented kWh; the clock attack preserves the daily total but fails hourly checks.

Only passing claims can proceed through the verifier to a real Solidity contract running on Ganache. The contract reserves all 24 registered asset-hours, blocks a second issuance even when its evidence root changes, and lets the certificate owner retire it permanently. A portable Merkle receipt exposes edits to the evidence.

## How we built it

We used 8,760 public hourly records from the European Commission's PVGIS for İzmir, Türkiye. A ridge-regression model learns the relationship between weather and modeled solar output. January–June trains it, July–September calibrates its prediction interval, and October–December remains held out.

The app combines Node.js, JavaScript, Solidity, ethers, Ganache and SHA-256 Merkle evidence with an original violet, coral and lime interface. It runs on Render, where each visitor gets an independent temporary demo chain. The demo film uses Deepgram Aura-2 narration, original motion graphics and an original synthesized background score.

## Challenges we ran into

A correct daily total can hide incorrect hourly production. A valid evidence hash can describe a forged claim. A new hash can still represent energy that was already certified. We handled these separately with hourly screening, inspectable evidence and asset-hour uniqueness enforced by the contract.

We also had to make the deployed demo usable by multiple judges without their transactions interfering, and fix a macOS-only dependency that initially blocked the Linux deployment.

## Accomplishments that we're proud of

- A live app whose full screening, issuance, replay, tamper, retirement and export workflow has been verified.
- Nineteen passing tests covering the model, adversarial cases, contract permissions, persistence and isolated hosted sessions.
- Held-out daylight mean absolute error of 0.306 kW and observed interval coverage of 94.1% on PVGIS modeled output.
- A guided demo where judges can attempt the attacks themselves, with no wallet setup.

## What we learned

Integrity, plausibility and authenticity answer different questions. Our evidence root detects changes, our model assesses consistency, and an independent verifier must authenticate the real installation and meter.

PVGIS output is modeled, and our attack cases are controlled demonstrations. These metrics are not real-meter fraud accuracy; we do not claim accredited renewable certificates or avoided CO₂. Making those boundaries visible makes the prototype easier to evaluate honestly.

## What's next for Afterlight

Pilot with a community solar operator using signed meter readings and independently verified asset identities. Validate and calibrate models across sites and seasons, introduce multiple verifier signers, and evaluate a public testnet and registry interoperability.

The adoption path is an evidence and screening layer that existing certificate registries can integrate before issuance, with exported evidence available for independent review.
