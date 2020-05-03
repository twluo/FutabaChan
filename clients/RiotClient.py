import requests
from requests.utils import requote_uri
from AUTH_KEYS import RIOT_API_KEY, TEST_USER

VERSION_ENDPOINT = "https://ddragon.leagueoflegends.com/realms/na.json"
SUMMONER_SPELL_ENDPOINT = "http://ddragon.leagueoflegends.com/cdn/%s/data/en_US/summoner.json"
RIOT_ENDPOINT = "https://na1.api.riotgames.com"
GET_SUMMONER_BY_NAME_ENDPOINT = RIOT_ENDPOINT + "/lol/summoner/v4/summoners/by-name/%s"
GET_MATCH_LIST_BY_ACCOUNT_ENDPOINT = RIOT_ENDPOINT + "/lol/match/v4/matchlists/by-account/%s"
GET_MATCH_INFO_BY_MATCH_ID_ENDPOINT = RIOT_ENDPOINT + "/lol/match/v4/matches/%s"


def get_request(url, headers=None, params=None):
    encoded_url = requote_uri(url)
    return requests.get(encoded_url, headers=headers, params=params)


class RiotClient:
    def __init__(self):
        self.version = self.get_version()
        self.summoner_spell_data = self.get_summoner_spell_data()
        self.headers = {'X-Riot-Token': RIOT_API_KEY}
        self.summoner_name_map = {}
        self.match_id_map = {}

    @staticmethod
    def get_version():
        return get_request(VERSION_ENDPOINT).json()['v']

    def get_summoner_spell_data(self):
        return get_request(SUMMONER_SPELL_ENDPOINT % self.version).json()

    def get_player_info(self, summoner_name):
        if summoner_name in self.summoner_name_map:
            return self.summoner_name_map[summoner_name]
        url = GET_SUMMONER_BY_NAME_ENDPOINT % summoner_name
        data = get_request(url, headers=self.headers).json()
        data_dict = {'accountId': data['accountId'], 'summonerName': summoner_name}
        self.summoner_name_map.update({summoner_name: data_dict})
        return data_dict

    def get_all_match_info_participants(self, summoner_name, begin_index=0, end_index=1):
        if begin_index >= end_index:
            end_index = begin_index+1
        participants = set()
        account_id = self.get_player_info(summoner_name)['accountId']
        params = {'endIndex': end_index, 'beginIndex': begin_index}
        get_match_list_url = GET_MATCH_LIST_BY_ACCOUNT_ENDPOINT % account_id
        matches_data = get_request(get_match_list_url, headers=self.headers, params=params).json()
        for match in matches_data['matches']:
            match_participants = self.get_match_info_participants(match['gameId'])
            for participant in match_participants:
                participants.add(participant['summonerName'])
        return participants

    def get_match_info_participants(self, match_id):
        if match_id in self.match_id_map:
            return self.match_id_map[match_id]
        get_match_data_url = GET_MATCH_INFO_BY_MATCH_ID_ENDPOINT % match_id
        match_data = get_request(get_match_data_url, headers=self.headers).json()
        participants = []
        for participant in match_data['participantIdentities']:
            player = participant['player']
            summoner_name = player['summonerName']
            account_id = player['currentAccountId']
            match_history_id = player['matchHistoryUri'].split('/')[-1]
            data_dict = {'accountId': account_id, 'summonerName': summoner_name, 'matchHistoryId': match_history_id}
            if summoner_name in self.summoner_name_map:
                self.summoner_name_map[summoner_name] = data_dict
            else:
                self.summoner_name_map.update({summoner_name: data_dict})
            participants.append(data_dict)
        self.match_id_map.update({match_id: participants})
        return participants


rc = RiotClient()
print(rc.get_all_match_info_participants(TEST_USER, end_index=2))

