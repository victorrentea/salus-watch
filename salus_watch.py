"""Power-outage alarm for a Salus iT500 thermostat.

The thermostat's internet gateway sits on mains power behind the home router,
so "gateway offline" in the Salus cloud means "no power (or no internet) at home".

Every run reads the gateway's `online` flag from the Arrayent API (the backend
the iT500 phone app uses; salus-it500.com is gone since 2026-10-22) and pings
healthchecks.io:
  online=1      -> success ping       (check stays green, or goes back up)
  online=0      -> /fail ping         (alarm right away)
  error/no data -> /log, exit 1       (no success ping; if it lasts, the grace
                                       period runs out and that alarms too)

Env: SALUS_USER, SALUS_PASS_MD5 (or SALUS_PASS), SALUS_DEVID, HC_URL (optional;
without it the script only prints).
"""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://sal-emea-p01-api.arrayent.com"
APP_AUTHORIZATION = "687886-679716122"  # Salus tenant id, same value the phone app sends
TIMEOUT = 30


def password_md5() -> str:
    if os.environ.get("SALUS_PASS_MD5"):
        return os.environ["SALUS_PASS_MD5"]
    return hashlib.md5(os.environ["SALUS_PASS"].encode()).hexdigest()


def login() -> dict:
    body = json.dumps({"username": os.environ["SALUS_USER"], "password": password_md5()}).encode()
    req = urllib.request.Request(
        API + "/acc/applications/SalusService/sessions", data=body, method="POST",
        headers={"Authorization": APP_AUTHORIZATION, "Accept": "application/json",
                 "Content-Type": "application/json"})
    token = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
    return {"secToken": token["securityToken"], "userId": token["userId"]}


def attributes(session: dict, dev_id: str) -> dict:
    query = urllib.parse.urlencode({**session, "devId": dev_id, "deviceTypeId": 1})
    xml = urllib.request.urlopen(
        API + "/zdk/services/zamapi/getDeviceAttributesWithValues?" + query, timeout=TIMEOUT).read()
    attrs = {}
    for el in ET.fromstring(xml).iter():
        if el.tag.rpartition("}")[2] == "attrList" and el.findtext("name"):
            attrs[el.findtext("name")] = (el.findtext("value") or "").strip()
    return attrs


def describe(attrs: dict) -> str:
    def temp(key):
        try:
            return f"{int(attrs[key]) / 100:.1f}°C"
        except (KeyError, ValueError):
            return "?"
    boiler = "ON" if attrs.get("A87") == "1" else "off"
    return f"room {temp('A84')}, setpoint {temp('A85')}, boiler {boiler}"


def ping(suffix: str, text: str) -> None:
    hc = os.environ.get("HC_URL")
    print(f"[{suffix or 'ok'}] {text}")
    if hc:
        urllib.request.urlopen(hc.rstrip("/") + suffix, data=text.encode(), timeout=TIMEOUT)


def main() -> int:
    try:
        attrs = attributes(login(), os.environ["SALUS_DEVID"])
        if "online" not in attrs:
            raise RuntimeError(f"no 'online' attribute in reply ({len(attrs)} attributes)")
    except Exception as e:  # noqa: BLE001 - any failure means "cannot tell"
        ping("/log", f"Cannot read thermostat state: {e!r}")
        return 1

    if attrs["online"] == "1":
        ping("", f"Thermostat ONLINE - {describe(attrs)}")
    else:
        ping("/fail", f"Thermostat OFFLINE (power or internet down at home). "
                      f"Last known: {describe(attrs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
