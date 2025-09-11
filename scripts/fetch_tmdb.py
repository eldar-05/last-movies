import os
import json
import requests

API_KEY = os.getenv("TMDB_API_KEY")
URL = f"https://api.themoviedb.org/3/movie/now_playing?api_key={API_KEY}&language=en-US&page=1"

DATA_FILE = "docs/data.json"

def fetch_movies():
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()

    movies = []
    for movie in data["results"][:10]:  # максимум 10 за один запуск
        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else "",
            "overview": movie.get("overview", ""),
            "release_date": movie.get("release_date", ""),
        })
    return movies

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_movies(movies):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    new_movies = fetch_movies()
    existing_movies = load_existing()

    existing_ids = {m["id"] for m in existing_movies}
    for m in new_movies:
        if m["id"] not in existing_ids:
            existing_movies.append(m)

    save_movies(existing_movies)
    print(f"Added {len(new_movies)} new movies. Total: {len(existing_movies)}")
