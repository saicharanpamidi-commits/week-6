"""A small class for pulling artist data from the Genius API."""

import pandas as pd
import requests


class Genius:
    """Search Genius and look up information about artists.

    Example:
        genius = Genius(access_token=ACCESS_TOKEN)
        genius.get_artist("Radiohead")
    """

    base_url = "https://api.genius.com"

    def __init__(self, access_token):
        """Store the access token used for every request."""
        self.access_token = access_token

    def _get(self, path, params=None):
        """Send a GET request to the Genius API and return the JSON."""
        response = requests.get(
            self.base_url + path,
            params=params,
            headers={"Authorization": "Bearer " + self.access_token},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def search(self, search_term, per_page=10):
        """Return the list of "hits" for a search term."""
        json_data = self._get("/search",
                              params={"q": search_term,
                                      "per_page": per_page})
        return json_data["response"]["hits"]

    @staticmethod
    def _pick_artist(hits, search_term):
        """Choose the most likely artist from a list of search hits.

        The first hit is usually right, but not always: a search for
        "U2" can return a song by another artist that features U2. So
        prefer a primary artist whose name matches the search term,
        and fall back to the first hit's artist if none does.
        """
        artists = [hit["result"]["primary_artist"] for hit in hits]

        for artist in artists:
            if artist["name"].lower() == search_term.lower():
                return artist

        return artists[0]

    def get_artist_id(self, search_term):
        """Return the ID of the most likely artist, or None."""
        hits = self.search(search_term)

        if not hits:
            return None

        return self._pick_artist(hits, search_term)["id"]

    def get_artist(self, search_term):
        """Return the JSON for the most likely artist for a search term.

        The search results are songs, so this finds the artist behind
        them and then asks the /artists endpoint about that artist.
        Returns an empty dictionary when nothing matches.
        """
        artist_id = self.get_artist_id(search_term)

        if artist_id is None:
            return {}

        return self._get(f"/artists/{artist_id}")

    def _artist_row(self, search_term):
        """Turn one search term into a row for get_artists."""
        json_data = self.get_artist(search_term)
        artist = json_data.get("response", {}).get("artist", {})

        return {
            "search_term": search_term,
            "artist_name": artist.get("name"),
            "artist_id": artist.get("id"),
            "followers_count": artist.get("followers_count"),
        }

    def get_artists(self, search_terms):
        """Return a DataFrame with one row of artist data per search term."""
        rows = [self._artist_row(term) for term in search_terms]

        return pd.DataFrame(rows, columns=["search_term", "artist_name",
                                           "artist_id", "followers_count"])
