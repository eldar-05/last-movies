import os, json, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

API_KEY = os.getenv("TMDB_API_KEY")
REGION = os.getenv("TMDB_REGION") or None
DAYS_BACK = int(os.getenv("DAYS_BACK", "30"))
MAX_ITEMS = 10
BASE = "https://api.themoviedb.org/3"

if not API_KEY:
    print("ERROR: TMDB_API_KEY is not set", file=sys.stderr)
    sys.exit(1)

def get(url, params=None, retries=3, timeout=20):
    p = {"api_key": API_KEY}
    if params: p.update(params)
    for i in range(retries):
        r = requests.get(url, params=p, timeout=timeout)
        if r.status_code == 429:
            time.sleep(1.5)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Failed GET {url}")

def get_genres():
    data = get(f"{BASE}/genre/movie/list", {"language": "ru-RU"})
    return {g["id"]: g["name"] for g in data.get("genres", [])}

def discover_movies():
    today = datetime.now(timezone.utc).date()
    since = today - timedelta(days=DAYS_BACK)
    params = {
        "sort_by": "primary_release_date.desc",
        "primary_release_date.gte": since.isoformat(),
        "primary_release_date.lte": today.isoformat(),
        "include_adult": "false",
        "page": 1,
    }
    if REGION:
        params["region"] = REGION
    data = get(f"{BASE}/discover/movie", params)
    return data.get("results", [])

def movie_details(movie_id):
    det = get(f"{BASE}/movie/{movie_id}", {"language": "ru-RU"})
    vids = get(f"{BASE}/movie/{movie_id}/videos", {"language": "en-US"})
    results = vids.get("results", []) or []
    if not results:
        vids = get(f"{BASE}/movie/{movie_id}/videos")
        results = vids.get("results", []) or []
    yt = None
    for v in results:
        if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
            yt = {"key": v.get("key"), "name": v.get("name"), "type": v.get("type")}
            break
    return det, yt

def poster_url(path, size="w500"):
    return f"https://image.tmdb.org/t/p/{size}{path}" if path else None

def main():
    out_dir = Path("docs/data")
    (out_dir / "movie").mkdir(parents=True, exist_ok=True)

    genres_map = get_genres()
    discovered = discover_movies()
    top = discovered[:MAX_ITEMS]

    list_items = []
    for m in top:
        mid = m.get("id")
        det, yt = movie_details(mid)

        per_movie = {
            "id": det.get("id"),
            "title": det.get("title") or det.get("original_title"),
            "tagline": det.get("tagline"),
            "overview": det.get("overview"),
            "release_date": det.get("release_date"),
            "runtime": det.get("runtime"),
            "vote_average": det.get("vote_average"),
            "vote_count": det.get("vote_count"),
            "genres": [g["name"] for g in det.get("genres", [])],
            "original_language": det.get("original_language"),
            "spoken_languages": [l.get("english_name") for l in det.get("spoken_languages", [])],
            "production_countries": [c.get("iso_3166_1") for c in det.get("production_countries", [])],
            "poster_url": poster_url(det.get("poster_path")),
            "backdrop_url": poster_url(det.get("backdrop_path"), "w780"),
            "tmdb_url": f"https://www.themoviedb.org/movie/{det.get('id')}",
            "trailer": yt, 
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "notice": "This product uses the TMDB API but is not endorsed by TMDB."
        }
        with (out_dir / "movie" / f"{mid}.json").open("w", encoding="utf-8") as f:
            json.dump(per_movie, f, ensure_ascii=False, indent=2)

        list_items.append({
            "id": det.get("id"),
            "title": det.get("title") or det.get("original_title"),
            "release_date": det.get("release_date"),
            "vote_average": det.get("vote_average"),
            "poster_url": poster_url(det.get("poster_path")),
            "genres": [genres_map.get(gid) for gid in m.get("genre_ids", []) if genres_map.get(gid)],
        })

    payload = {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "region": REGION,
        "days_back": DAYS_BACK,
        "count": len(list_items),
        "items": list_items,
        "source": "TMDB",
        "notice": "This product uses the TMDB API but is not endorsed by TMDB."
    }
    with (out_dir / "movies.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {out_dir/'movies.json'} and {len(list_items)} movie detail files.")
    
if __name__ == "__main__":
    main()
