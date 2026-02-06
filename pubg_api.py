import requests
import os

class PUBGAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('PUBG_API_KEY')
        self.base_url = "https://api.pubg.com/shards"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json"
        }

    def get_player_stats(self, platform, gamertag):
        # Platform should be 'xbox' or 'psn'
        shard = "xbox" if platform.lower() == "xbox" else "psn"
        url = f"{self.base_url}/{shard}/players?filter[playerNames]={gamertag}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def get_match_details(self, platform, match_id):
        shard = "xbox" if platform.lower() == "xbox" else "psn"
        url = f"{self.base_url}/{shard}/matches/{match_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def extract_player_stats_from_match(self, match_data, account_id):
        # Extract kills and placement for a specific player from match data
        included = match_data.get('included', [])
        for item in included:
            if item.get('type') == 'participant':
                attributes = item.get('attributes', {})
                stats = attributes.get('stats', {})
                if stats.get('playerId') == account_id:
                    return {
                        'kills': stats.get('kills', 0),
                        'placement': stats.get('winPlace', 0),
                        'win': stats.get('winPlace') == 1
                    }
        return None
