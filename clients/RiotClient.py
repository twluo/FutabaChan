import requests


VERSION_ENDPOINT = "https://ddragon.leagueoflegends.com/realms/na.json"
SUMMONER_SPELL_ENDPOINT = "http://ddragon.leagueoflegends.com/cdn/%s/data/en_US/summoner.json"

class RiotClient:
    def __init__(self):
        self.version = self.get_version()
        self.summoner_spell_data = self.get_summoner_spell_data()
        print(self.summoner_spell_data)

    def get_version(self):
        return requests.get(VERSION_ENDPOINT).json()['v']

    def get_summoner_spell_data(self):
        return requests.get(SUMMONER_SPELL_ENDPOINT % self.version).json()

RiotClient()