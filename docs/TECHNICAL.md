# Technical design and review notes

## Screening

For daylight sample `r`, let `g = G(i)/1000`, `t = (T2m−25)/25`, `w = WS10m/10` and

`x = [1, g, g², g³, gt, g²t, gw, g²w]`.

Fit `β = argmin Σ(y−xβ)² + 0.001 Σ(j>0) βj²`, with `y=P/1000` in kW. The implementation solves the regularized normal equations with partial pivoting. This small eight-feature surrogate is intentionally inspectable. At prediction, clamp output to [0,100] kW and return zero when irradiance is zero.

On July–September daylight calibration records, sort `|y−ŷ|` and choose order statistic `ceil((n+1)×0.9)`, capped at `n`. The daylight interval is `[max(0,ŷ−q),min(100,ŷ+q)]`. At zero irradiance both bounds are zero. Chronological weather records need not satisfy conformal exchangeability: empirical test coverage is reported; a distribution-free guarantee for this time series is not claimed.

The policy covers PV generation at the inverter, excluding battery discharge. The separately registered export limit is 100 kW; this is an imposed demo registry limit, not an assertion that nominal DC nameplate power cannot be exceeded. The policy first rejects readings above 100 kWh or above 0.5 kWh with zero reference irradiance, then requires review for reconstructed irradiance or deviations beyond the model envelope plus 3 kWh. Any reject dominates review; any review blocks issuance. A clean model output does not verify an actual meter or prove an absence of fraud.

## Evidence

One metadata leaf contains schema, asset/day, dataset/model hashes and policy. Each of the next 24 leaves contains hour, exact source timestamp, claimed Wh and source weather. Leaves are SHA-256 of UTF-8 JSON; parents are SHA-256 of the concatenated lowercase hexadecimal child hashes; an odd last child is duplicated. The final root is `0x` prefixed. This encoding is implemented in one shared module and verified against metadata, ordering and reading mutations. Other implementations must reproduce field order and encoding exactly.

`createdAt`, display label and transaction metadata are outside the root. Relabelling a claim therefore does not change its root. The contract binds the root to asset/day/quantity separately. Offline verification establishes self-consistency; compare with contract storage to establish anchoring.

## EVM

The registered asset ID is `keccak256(UTF8("IZMIR-DEMO-100"))`. A slot is `keccak256(abi.encode(assetId, day/3600 + hour))`. UTC days must be midnight-aligned. Registration is verifier-only and cannot overwrite an existing asset. Issuance validates every interval's capacity, reserves every interval including zeros, and stores a single certificate. EVM rollback makes the whole operation atomic. Certificates are non-transferable in this prototype. Only the operator can retire; beneficiary strings are committed with keccak256 rather than stored as plaintext.

An issuer can choose another registered ID for the same physical installation; prevention requires registry governance. An authorized verifier can submit evidence that bypasses model review; the contract cannot execute the weather model. Those are explicit trust boundaries, not guarantees provided by hashes. The present server controls deterministic development signers and is suitable only for loopback demonstration.

## HTTP and storage

The server uses a same-origin per-session token for POST operations, rejects non-loopback Host headers and unexpected Origin headers, accepts bounded JSON payloads, validates reading values, and serializes mutations. Static file serving uses an explicit allowlist. Issuance re-runs the stored claim against the pinned dataset/model before sending a transaction. Reports are saved with atomic rename, while Ganache persists chain state separately. Contract events are queried at a concrete block tip to avoid stale `latest` caching immediately after issuance.

## Cost and scaling

The verified 24-slot certificate issuance uses approximately 708,066 local-EVM gas. A production system should evaluate an L2, compressed interval bitmaps, batched roots, and verifier attestations, rather than asserting low fees from a local test. Expanding weather models requires per-site validation, quality checks, monitoring and drift handling. Multi-party oracle governance, real signed meters and interoperability are required before accredited use.

## Validation

`npm test` checks deterministic retraining and source binding; adversarial profiles; malformed readings; metadata and reading tampering; verifier and owner permissions; invalid assets/days/roots/capacity; actual EVM issuance; changed-root replay; immutable registration; permanent retirement; and reopening persistent chain state. `npm run demo:verify` additionally exercises HTTP status paths, token rejection, stored evidence export and the full certificate lifecycle against a running server.
