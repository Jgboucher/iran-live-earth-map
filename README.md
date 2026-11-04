# Iran War Live Google Earth Map — starter kit

This kit creates a hosted KML feed for Google Earth Pro. GitHub Actions polls a public incident feed every five minutes, converts geolocated events to KML, and publishes the result with GitHub Pages.

## Important limitations

- **The map refresh interval is 5 minutes; the underlying source is not a 5-minute guaranteed feed.** IranWarLive documents that its public `feed.json` is refreshed about every two hours and contains a rolling 48-hour window. This pipeline checks it every five minutes, but new reports only appear when the source publishes them.
- The public feed is labelled as a machine-readable feed under **CC BY 4.0**. Attribution is included in the placemark descriptions.
- An event is labelled **Confirmed** only when the source's own confidence field explicitly contains `confirmed` or `verified`. Everything else is labelled **Reported** and retains the source confidence wording. This is not independent verification.
- Events without coordinates are omitted rather than guessed. Coordinates may be approximate.
- This is an OSINT situational-awareness aid, not an official warning system.
- **Google Earth Pro desktop supports KML NetworkLink interval refresh. Google Earth for iPhone/iPad does not reliably honor NetworkLink auto-refresh.** On iPhone, use the live source map in Safari, or reopen/reload the published `live.kml` for a fresh snapshot.

## Included files

- `index.kml` — Google Earth NetworkLink, configured for a 300-second refresh.
- `update_map.py` — downloads and converts the public feed into `live.kml`.
- `.github/workflows/update-map.yml` — scheduled GitHub Actions workflow (every 5 minutes).
- `requirements.txt` — Python dependency list.
- `live.kml` — placeholder until the first workflow run.
- `status.json` — last-run metadata.

## Setup

1. Create a new GitHub repository, e.g. `iran-live-earth-map`.
2. Upload the contents of this folder to the repository root (including the hidden `.github` folder).
3. In GitHub, open **Settings → Pages** and set **Build and deployment → Deploy from a branch**, branch `main`, folder `/ (root)`. Save.
4. Open **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**. Save.
5. Open **Actions → Update Iran live KML → Run workflow** once. Wait for it to finish. The scheduled job then runs every five minutes.
6. Your hosted files will be:
   - `https://YOUR-GITHUB-USERNAME.github.io/iran-live-earth-map/index.kml`
   - `https://YOUR-GITHUB-USERNAME.github.io/iran-live-earth-map/live.kml`

## Google Earth Pro (computer)

1. Open Google Earth Pro.
2. Choose **File → Open** and open the hosted `index.kml` URL (or download `index.kml` and open it).
3. Keep the NetworkLink in **Temporary Places** or save it to **My Places**.
4. The live layer fetches `live.kml` every 300 seconds while Google Earth Pro is running and connected.

## iPhone / iPad

Google Earth mobile may display imported KML/KMZ snapshots, but do not rely on it to honor the desktop NetworkLink refresh timer. For a continuously updating phone view, open the source map in Safari:
- https://battlemap.online/conflicts/iran/en

For a fresh KML snapshot on iPhone, open the hosted `live.kml` URL in Safari and share/open it with Google Earth. Reopen it to fetch a newer snapshot.

## Sources and cadence

- IranWarLive public machine feed: https://iranwarlive.com/feed.json
- IranWarLive methodology / access notes: https://iranwarlive.com/llms.txt
- battleMap Iran dashboard (separate tracker; its REST API requires an API plan/key): https://battlemap.online/conflicts/iran/en

This starter kit uses the public IranWarLive JSON feed only. It does not scrape private endpoints or bypass API authentication. Its public feed documents a 48-hour window and approximately two-hour update cadence. The five-minute job interval is a polling schedule, not a promise of five-minute intelligence freshness.

## Troubleshooting

- If the Pages URL returns 404, confirm Pages is enabled on `main` / root and wait for deployment.
- If Actions fails to push `live.kml`, check that workflow permissions are set to **Read and write**.
- GitHub Actions supports schedules as often as every five minutes, but jobs can be delayed or queued.
- Check `status.json` in the repository for the last successful source fetch and event count.
