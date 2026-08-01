# ex-infra_ops — repair plan (written before the first edit)

Sealed check: `bash assets/ex-infra_ops/check.sh` → `{"checks_passed": N, "checks_total": 6}`.
Threshold: 6 of 6. Nothing under `assets/ex-infra_ops/` may change except `stack/`.

## Defects, each with the command that confirms it

| # | suspected defect | confirming command | expected evidence |
|---|---|---|---|
| D1 | `web` image tag is floating (`miniweb:latest`) | `python3 assets/ex-infra_ops/minictl.py --stack .../stack.json config` | the normalized output contains `:latest` → C2 red |
| D2 | `cache` image tag is not in the pinned registry (`minicache:7.2.4-bogus`) | `... minictl.py ... up` | `image 'minicache:7.2.4-bogus' not found in the pinned local registry` → C3/C6 red |
| D3 | `site.conf` does not parse | `... minictl.py ... conftest web` | `line 2: directive 'listen 8080' is missing its terminating ';'` |
| D4 | `site.conf` roots at a path nothing mounts | `... minictl.py ... up` after D3 | `no volume mounts the config root '/usr/share/site' (mounts: none)` → C5 red |
| D5 | the site is published on 8080, the contract says 8391 | `... minictl.py ... port web 80` | prints nothing / not `:8391` → C4 red |

## Repair order (dependencies first)

1. **D3** — terminate the `listen` directive and set it to the container port `80`.
   Confirm with `conftest web` before touching anything else: while the config does not
   parse, every other diagnostic is noise.
2. **D1 + D2** — pin both images to the registry tags `miniweb:1.25.4` / `minicache:7.2.4`.
   Confirm with `config` (no `:latest`) and `up` (both services report `running`).
3. **D4** — mount `./html` at the config root: `"volumes": ["./html:/usr/share/site:ro"]`.
4. **D5** — publish `8391:80` so the host port matches the contract and the container port
   matches `listen`.

## Verification loop

Re-run the sealed check after **every** step and record the `checks_passed` trajectory,
red runs included. Expected: 1 → (after 1+2) 3 → (after 3+4) 6. If a step does not move
the number, the diagnosis was wrong — re-diagnose, do not stack another guess on top.
