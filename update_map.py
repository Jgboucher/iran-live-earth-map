#!/usr/bin/env python3
"""Fetch a public OSINT JSON feed and render a Google Earth KML snapshot."""
from __future__ import annotations
import html, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
import requests

FEED_URL = os.getenv("IRANWARLIVE_FEED_URL", "https://iranwarlive.com/feed.json")
OUT, STATUS = Path("live.kml"), Path("status.json")
BOUNDS = {"min_lat": 10.0, "max_lat": 42.5, "min_lon": 24.0, "max_lon": 65.5}

KML_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<name>Iran War — Live public-source incidents</name>
<description><![CDATA[Automated snapshot from IranWarLive public JSON feed.
Confirmed means the source confidence label explicitly says confirmed/verified.
All other entries are reported, not independently confirmed by this map.
This is not an official warning feed.]]></description>
<Style id="confirmed"><IconStyle><scale>1.15</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon></IconStyle></Style>
<Style id="reported"><IconStyle><scale>1.05</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/orange-circle.png</href></Icon></IconStyle></Style>
<Folder><name>CONFIRMED — source explicitly labels confirmed/verified</name><open>1</open>
"""
KML_MID = """</Folder><Folder><name>REPORTED — not independently confirmed by this map</name><open>1</open>
"""
KML_TAIL = "</Folder></Document></kml>\n"

def coords_for(item):
    meta = item.get("_osint_meta") or {}
    coords = meta.get("coordinates") or item.get("coordinates") or {}
    lat = coords.get("lat", item.get("lat", item.get("latitude")))
    lon = coords.get("lng", coords.get("lon", item.get("lon", item.get("longitude"))))
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not (BOUNDS["min_lat"] <= lat <= BOUNDS["max_lat"] and BOUNDS["min_lon"] <= lon <= BOUNDS["max_lon"]):
        return None
    return lat, lon

def esc(v):
    return html.escape(str(v if v is not None else "Not provided"), quote=True)

def render(item):
    point = coords_for(item)
    if point is None:
        return None, None
    lat, lon = point
    confidence = item.get("confidence") or item.get("sourceConfidence") or "Not specified"
    confirmed = bool(re.search(r"\b(confirmed|verified)\b", str(confidence), re.I))
    bucket = "confirmed" if confirmed else "reported"
    status = "CONFIRMED (source label)" if confirmed else "REPORTED (not independently confirmed)"
    kind = item.get("type") or item.get("attackType") or "Incident"
    location = item.get("location") or item.get("city") or item.get("country") or "Location not specified"
    title = item.get("title") or item.get("event_summary") or item.get("summary") or kind
    stamp = item.get("timestamp") or item.get("date") or "Time not provided"
    source = item.get("source_url") or item.get("primaryArticleUrl") or item.get("url") or ""
    event_id = item.get("event_id") or item.get("id") or ""
    summary = item.get("event_summary") or item.get("summary") or ""
    desc = (
        f"<b>Status:</b> {status}<br/><b>Type:</b> {esc(kind)}<br/>"
        f"<b>Location:</b> {esc(location)}<br/><b>Timestamp:</b> {esc(stamp)}<br/>"
        f"<b>Source confidence:</b> {esc(confidence)}<br/><b>Event ID:</b> {esc(event_id)}<br/>"
        f"<b>Summary:</b> {esc(summary)}<br/><b>Coordinates:</b> {lat:.5f}, {lon:.5f}<br/>"
        f'<b>Source:</b> <a href="{html.escape(source, quote=True)}">Open original report</a><br/>'
        "Coordinates and descriptions may be approximate; inspect the source."
    )
    when = str(stamp)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        when += "T00:00:00Z"
    pm = (f"<Placemark><name>{esc(status + ' — ' + str(title)[:160])}</name>"
          f"<styleUrl>#{bucket}</styleUrl><description><![CDATA[{desc}]]></description>"
          f"<TimeStamp><when>{esc(when)}</when></TimeStamp>"
          f"<Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point></Placemark>\n")
    return bucket, pm

def main():
    response = requests.get(FEED_URL, timeout=25, headers={"User-Agent": "IranLiveKML/1.0"})
    response.raise_for_status()
    payload = response.json()
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("Feed JSON did not contain an items array")
    confirmed, reported, seen, skipped = [], [], set(), 0
    for item in items:
        if not isinstance(item, dict):
            skipped += 1
            continue
        key = item.get("event_id") or item.get("id")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        bucket, placemark = render(item)
        if not placemark:
            skipped += 1
        elif bucket == "confirmed":
            confirmed.append(placemark)
        else:
            reported.append(placemark)
    now = datetime.now(timezone.utc).isoformat()
    kml = KML_HEAD + "".join(confirmed) + KML_MID + "".join(reported) + KML_TAIL
    OUT.write_text(kml, encoding="utf-8")
    status = {
        "status": "ok", "generated_utc": now, "source": FEED_URL,
        "source_title": payload.get("title", "Public OSINT feed") if isinstance(payload, dict) else "Public OSINT feed",
        "source_last_updated": payload.get("last_updated", "Not supplied") if isinstance(payload, dict) else "Not supplied",
        "feed_items": len(items), "mapped_confirmed_by_source_label": len(confirmed),
        "mapped_reported": len(reported), "skipped_missing_or_out_of_area_coordinates": skipped,
        "refresh_target_seconds": 300,
        "note": "Polling every five minutes does not make the source itself update every five minutes."
    }
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        raise
