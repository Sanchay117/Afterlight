# AFTERLIGHT demonstration

Narrated product demo: approximately 4 minutes 24 seconds, 1920×1080. The MP4 includes optional English subtitles; the SRT is also provided.

Actual captured UI states are presented with annotations and Deepgram Aura-2 Thalia narration. This is an edited demonstration of the working app, not a continuous screen recording.

Run the interactive version with `npm start`, open http://127.0.0.1:4173, and choose **Try to break it**.

## 00:00 — The sun has receipts.

A blockchain can preserve a bad climate claim forever. AFTERLIGHT asks a question before issuing a clean energy certificate: does the generation have an alibi? This working prototype combines weather-grounded machine learning, inspectable evidence, and a real Ethereum contract. Let's test it by trying to break it.

## 00:19 — Solar power. After sunset?

Here is the first case file. We inserted eighteen kilowatt-hours into each of four night intervals. The daily claim looks plausible at first glance. The hourly weather evidence tells a different story: there is no solar irradiance. All seventy-two invented kilowatt-hours are flagged, and certificate issuance is blocked. Every reading has an explanation in the evidence table.

## 00:44 — Below capacity. Above the evidence.

Now a subtler attack. We inflate six daytime readings by thirty-five percent. Every reading stays below the installation's registered capacity. A capacity-only check would miss this. The learned weather model identifies production above its uncertainty envelope, so the system requests review. It does not invent a corrected reading or issue a partial certificate.

## 01:08 — Same daily total. Wrong hours.

The third attack changes only the clock. The daily energy sum is exactly the same as the clean claim. But shifting the profile by four hours places some generation outside the solar window and misaligns the daytime evidence. Fifteen intervals are flagged. A daily total alone would have hidden this inconsistency.

## 01:26 — Learn. Calibrate. Hold out.

The model uses a real public European Commission reference download: eight thousand seven hundred sixty hourly records for Izmir. Ridge regression learns irradiance and weather interactions. Training, calibration, and test months are separate. Held-out daylight error is zero point three zero six kilowatts, with ninety-four point one percent empirical interval coverage. These are metrics against modeled PVGIS output, not real-meter fraud accuracy.

## 01:54 — Earn the receipt. Then anchor it.

Now return to the clean reference-derived claim. All twenty-four intervals pass. The model's estimate and submitted profile agree within the screening policy. The verifier can anchor the evidence. This is a real contract transaction on a persistent local Ethereum chain, with no wallet setup or paid external service needed for the demo.

## 02:16 — A certificate with a chain of evidence.

The certificate records the registered asset, UTC day, energy quantity, and evidence Merkle root. Its transaction hash and block are visible in the registry. At issuance, the Solidity contract atomically reserves every asset-hour, including zero-output intervals. The contract restricts issuance to its authorized verifier. Weather screening remains an explicit off-chain responsibility.

## 02:41 — New receipt. Same electrons.

Let's issue another claim for those same intervals. The challenge calls the contract directly, rather than relying on the interface's duplicate check. The Ethereum virtual machine rejects it with Duplicate Interval. A different evidence root cannot unlock an already consumed asset-hour. This prevents duplicate issuance within this registry's registered asset identity.

## 03:03 — One edited reading. A broken alibi.

Next, attack the evidence. The original packet matches its committed root. Add just one kilowatt-hour to a single reading, and verification fails. The packet binds all readings, the source data fingerprint, the model fingerprint, and the screening policy. It can be exported and checked offline. Integrity proves a packet has not changed; it does not prove its inputs are true.

## 03:30 — Retired once. Retired for good.

The certificate owner can permanently retire the certificate for a beneficiary. Retirement does not release the consumed generation intervals. The tests check that a second retirement fails and that both retirement and replay protection survive closing and reopening the chain. The working interface also accepts imported hourly readings for the fixed demonstration asset and day.

## 03:52 — A little less greenwash. A little more proof.

AFTERLIGHT is designed as a verification layer for solar cooperatives and certificate issuers. Our demonstrated impact is claims challenged and duplicate issuance prevented, not claimed carbon savings. The asset and meter readings are illustrative, the power reference is modeled, and the blockchain is local. Production needs authenticated meters, independent asset identity, multiple oracle signers, and real-site validation. The working prototype and sixteen tests are reproducible from the repository.
