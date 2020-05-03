import requests
from requests.utils import requote_uri
from AUTH_KEYS import RIOT_API_KEY
import copy
import time
import json

VERSION_ENDPOINT = "https://ddragon.leagueoflegends.com/realms/na.json"
SUMMONER_SPELL_ENDPOINT = "http://ddragon.leagueoflegends.com/cdn/%s/data/en_US/summoner.json"
RIOT_ENDPOINT = "https://na1.api.riotgames.com"
GET_SUMMONER_BY_NAME_ENDPOINT = RIOT_ENDPOINT + "/lol/summoner/v4/summoners/by-name/%s"
GET_MATCH_LIST_BY_ACCOUNT_ENDPOINT = RIOT_ENDPOINT + "/lol/match/v4/matchlists/by-account/%s"
GET_MATCH_INFO_BY_MATCH_ID_ENDPOINT = RIOT_ENDPOINT + "/lol/match/v4/matches/%s"
MATCH_HISTORY = "https://matchhistory.na.leagueoflegends.com/en/#match-details/NA1/%s/%s?tab=overview"

DELAY = 1.2
DEBUG = 1
RETRY_COUNT = 5


def write_to_file(map, filename):
    dump = json.dumps(map)
    f = open(filename, "w")
    f.write(dump)
    f.close()


class RiotClient:
    def __init__(self):
        self.then_time = time.time()
        self.version = self.get_version()
        self.summoner_spell_data = self.get_summoner_spell_data()
        self.headers = {'X-Riot-Token': RIOT_API_KEY}
        self.summoner_name_map = {}
        self.match_id_map = {}
        with open('summoner_name_map.json') as json_file:
            self.summoner_name_map = json.load(json_file)
        with open('match_id_map.json') as json_file:
            self.match_id_map = json.load(json_file)

    def get_version(self):
        return self.get_request(VERSION_ENDPOINT).json()['v']

    @staticmethod
    def check_summoner_data_equality(summoner1_data, summoner2_data):
        return summoner1_data['summonerName'] == summoner2_data['summonerName']

    def get_request(self, url, headers=None, params=None):
        retry_attempt = 0
        while retry_attempt <= RETRY_COUNT:
            now_time = time.time()
            gap = now_time - self.then_time
            if gap < DELAY:
                time.sleep(DELAY - gap)
            self.then_time = time.time()
            encoded_url = requote_uri(url)
            request = requests.get(encoded_url, headers=headers, params=params)
            print(request.status_code)
            if request.status_code == 200:
                return request
            retry_attempt += 1
            print("Retry # %s" % retry_attempt)

    def get_summoner_spell_data(self):
        return self.get_request(SUMMONER_SPELL_ENDPOINT % self.version).json()

    def get_player_info(self, summoner_name):
        if summoner_name in self.summoner_name_map:
            return self.summoner_name_map[summoner_name]
        url = GET_SUMMONER_BY_NAME_ENDPOINT % summoner_name
        data = self.get_request(url, headers=self.headers)
        if data.status_code == 200:
            data = data.json()
            data_dict = {'accountId': data['accountId'], 'summonerName': data['name']}
            self.summoner_name_map.update({data['name']: data_dict})
            write_to_file(self.summoner_name_map, "summoner_name_map.json")
            return data_dict
        return None

    def get_all_match_info_participants(self, summoner_name, begin_index=0, end_index=1):
        if begin_index >= end_index:
            end_index = begin_index+1
        participants = set()
        account_id = self.get_player_info(summoner_name)['accountId']
        params = {'endIndex': end_index, 'beginIndex': begin_index}
        get_match_list_url = GET_MATCH_LIST_BY_ACCOUNT_ENDPOINT % account_id
        matches_data = self.get_request(get_match_list_url, headers=self.headers, params=params).json()
        for match in matches_data['matches']:
            match_id = match['gameId']
            if DEBUG:
                print("Checking %s" % match_id)
            match_participants = self.get_match_info_participants(match_id)
            for participant in match_participants:
                participants.add((participant['summonerName'], match_id))
        return participants

    def get_match_info_participants(self, match_id):
        if match_id in self.match_id_map:
            return self.match_id_map[match_id]
        get_match_data_url = GET_MATCH_INFO_BY_MATCH_ID_ENDPOINT % match_id
        match_data = self.get_request(get_match_data_url, headers=self.headers).json()
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
                write_to_file(self.summoner_name_map, "summoner_name_map.json")
            participants.append(data_dict)
        self.match_id_map.update({match_id: participants})
        write_to_file(self.match_id_map, "match_id_map.json")
        return participants

    def find_shortest_distance(self, summoner1, summoner2):
        summoner1_data = self.get_player_info(summoner1)
        summoner2_data = self.get_player_info(summoner2)
        if summoner1_data is None or summoner2_data is None:
            return [], []
        if self.check_summoner_data_equality(summoner1_data, summoner2_data):
            return [summoner1_data['summonerName']], []
        discovered_set = set(summoner1_data['summonerName'])
        discovery_q = [(summoner1_data['summonerName'], [], [])]
        while len(discovery_q) != 0:
            summoner, path_so_far_, match_id_path_ = discovery_q.pop(0)
            if DEBUG:
                print(summoner, path_so_far_, match_id_path_)
            if self.check_summoner_data_equality(self.get_player_info(summoner), summoner2_data):
                path_so_far_.append(summoner)
                match_history = [self.get_match_history_url(name, id) for name, id in zip(path_so_far_, match_id_path_)]
                return path_so_far_, match_history
            for participant, match_id in self.get_all_match_info_participants(summoner, end_index=10):
                if participant not in discovered_set:
                    path_so_far = copy.deepcopy(path_so_far_)
                    match_id_path = copy.deepcopy(match_id_path_)
                    match_id_path.append(match_id)
                    path_so_far.append(summoner)
                    discovered_set.add(participant)
                    discovery_q.append((participant, path_so_far, match_id_path))

    def get_match_history_url(self, summoner_name, match_id):
        return MATCH_HISTORY % ( match_id, self.get_player_info(summoner_name)['matchHistoryId'])