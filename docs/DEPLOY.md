# Put AFTERLIGHT online

Use a **Render Node web service**. The included `render.yaml` configures the whole app, including the server and its demo EVM. No runtime API keys, wallet setup, database, or paid disk are needed.

Demo video: [AFTERLIGHT on YouTube](https://youtu.be/JrWJmzfMmjQ).

Current live app: [afterlight-3ch7.onrender.com](https://afterlight-3ch7.onrender.com/). Its health endpoint and complete hosted walkthrough were verified on 25 October 2026. [Verification evidence](../artifacts/verification.json) records the tested origin and certificate lifecycle. The steps below reproduce the deployment for another instance.

## Deploy in three steps

1. In the `IEEE` folder, push the latest commit to the configured GitHub repository:

   ```sh
   git push origin main
   ```

   The configured remote is `git@github.com:Sanchay117/Afterlight.git`. Check that the repository is visible to judges before adding it to Devpost.

2. Open the [Render dashboard](https://dashboard.render.com/), choose **New → Blueprint**, connect GitHub, and select **Sanchay117/Afterlight**. Choose branch **main** and use the root `render.yaml`. Review the **Free** web service, then choose **Deploy Blueprint**.

3. When the service says **Live**, open its `https://…onrender.com` address. Select **Try to break it** and complete the walkthrough. Put that address in the Devpost **Try it out** field and use the YouTube link for the demo video.

Keep Render's **Root Directory** empty: this repository already contains the app at its root. Do not select Static Site.

If an older deployment failed with `EBADPLATFORM` for `fsevents`, deploy the latest commit. Ganache's nested macOS watcher is marked optional in the committed lockfile so Linux can skip it. Keep `npm ci`; no `--force` or platform override is needed. The GitHub Actions Linux check runs the same install, build and tests on every push.

## If you choose New → Web Service instead

| Setting | Value |
|---|---|
| Repository / branch | `Sanchay117/Afterlight` / `main` |
| Language | Node |
| Root Directory | Leave empty |
| Build Command | `npm ci --omit=dev --no-audit --no-fund && npm run build` |
| Start Command | `npm start` |
| Instance Type | Free |
| Health Check Path | `/healthz` |
| `NODE_VERSION` | `22` |
| `AFTERLIGHT_MODE` | `hosted-demo` |
| `AFTERLIGHT_MAX_SESSIONS` | `6` |
| `AFTERLIGHT_SESSION_TTL_MINUTES` | `20` |

Render supplies `PORT` and `RENDER_EXTERNAL_URL` automatically. The server uses that public URL to check requests and binds to `0.0.0.0` in hosted mode. If you add a custom domain, set `AFTERLIGHT_PUBLIC_ORIGIN` to that exact HTTPS origin (for example `https://demo.example.com`) and share that domain consistently.

## What judges get

Each browser receives an independent in-memory Ganache blockchain and evidence store. Two judges can both issue the same clean demonstration claim without changing one another's certificates. Within a visitor's chain, duplicate issuance remains blocked and retirement remains permanent for that chain's lifetime.

Sessions reset after 20 minutes without API activity, a service restart, or redeployment. The app labels this behavior visibly. The default limit is six simultaneous sessions; additional visitors see a retry message until a slot expires. Keep one running service instance because sessions live in that process. This is a hosted demonstration of a local EVM, not a public Ethereum network or shared production registry.

Render's [free-service documentation](https://render.com/docs/free) says idle services sleep after 15 minutes and can take about a minute to wake. Open the demo ahead of a scheduled presentation. A paid instance removes the free idle spin-down restriction; choose it only if you want that behavior.

Deepgram was used to make the video narration. The app itself does not call Deepgram, so do not add that key to Render. The video stays on YouTube; Render serves only the interactive app.

## Check after deployment

- Open `/healthz`; it should report `{"ok":true,"mode":"hosted-demo"}`.
- Confirm the page says **Your own solar sandbox**.
- Issue the clean claim, challenge the duplicate, run the tamper check, then retire the certificate.
- Open an incognito window: its registry should be empty, and its clean claim should issue independently.

You can also run the complete scripted walkthrough against your deployed address:

```sh
AFTERLIGHT_URL=https://YOUR-SERVICE.onrender.com npm run demo:verify
```

In hosted mode this uses its own temporary session. It checks screening, issuance, replay rejection, tampering, retirement and export, and writes verification evidence under `artifacts/`.

The repository's `npm test` checks these server behaviors locally, including session isolation, expiration, origin protection, and local persistence. A successful local check is not confirmation of a cloud deployment: confirm the actual Render URL before submitting it.

## Reproduce hosted mode on your computer

```sh
npm ci
npm run build
AFTERLIGHT_MODE=hosted-demo AFTERLIGHT_PUBLIC_ORIGIN=http://127.0.0.1:4173 npm start
```

Open exactly `http://127.0.0.1:4173`. Plain HTTP is allowed only for loopback testing. Without `AFTERLIGHT_MODE`, the app keeps its original loopback-only mode and persistent `.data` ledger.

References: [Render Blueprint specification](https://render.com/docs/blueprint-spec), [default environment variables](https://render.com/docs/environment-variables), [Node deployment](https://render.com/docs/deploy-node-express-app).
