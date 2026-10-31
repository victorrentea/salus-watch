# salus-watch

Power-outage alarm for a home heated through a **Salus iT500** thermostat.

The thermostat's internet gateway is on mains power behind the home router. When the
Salus cloud reports it **offline**, the house has lost power (or internet), and the
heating can't be controlled remotely.

Every 10 minutes a GitHub Action reads the gateway's `online` flag from the Arrayent API
(the backend of the iT500 phone app; the old salus-it500.com portal shut down on
2026-10-22) and pings a [healthchecks.io](https://healthchecks.io) check:

| state | ping | effect |
|---|---|---|
| online | success | check green (or back up → "recovered" notification) |
| offline | `/fail` | alarm right away |
| cannot read | `/log` | no success ping; alarm when the grace period runs out |

So the alarm also fires if this watcher itself breaks.

## Secrets

`SALUS_USER`, `SALUS_PASS_MD5` (md5 of the app password), `SALUS_DEVID`, `HC_URL`.

## Local run

```sh
SALUS_USER=... SALUS_PASS=... SALUS_DEVID=... python3 salus_watch.py
```

API mapping taken from [ladamczyk-it/salus-it500#1](https://github.com/ladamczyk-it/salus-it500/pull/1).
