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

DELAY = 1.5
DEBUG = 1
RETRY_COUNT = 5


class RiotClient:
    class Player:
        def __init__(self, account_id, summoner_name):
            self.account_id = account_id
            self.summoner_name = summoner_name

        def __str__(self):
            return self.summoner_name

        def __repr__(self):
            return str(self)

    def __init__(self):
        self.then_time = time.time()
        self.version = self.get_version()
        self.summoner_spell_data = self.get_summoner_spell_data()
        self.headers = {'X-Riot-Token': RIOT_API_KEY}

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
            if DEBUG:
                print(request.status_code, url)
            if request.status_code == 200:
                return request
            retry_attempt += 1
            print("Retry # %s" % retry_attempt)

    def get_summoner_spell_data(self):
        return self.get_request(SUMMONER_SPELL_ENDPOINT % self.version).json()

    def get_player_info(self, summoner_name):
        url = GET_SUMMONER_BY_NAME_ENDPOINT % summoner_name
        data = self.get_request(url, headers=self.headers)
        if data.status_code == 200:
            data = data.json()
            return self.Player(data['accountId'], data['name'])
        return None

    def get_rival_record(self, protag_name, rival_name, begin_index=0, end_index=10):
        protag = self.get_player_info(protag_name)
        matches_info = self.get_all_match_info_participants(protag, begin_index, end_index)
        with_wins = 0
        against_wins = 0
        with_losses = 0
        against_losses = 0
        rivals = []
        friends = []
        for match in matches_info:
            protag_win = match[protag_name]
            if rival_name in match:
                rival_win = match[rival_name]
                if protag_win is True:
                    if protag_win is rival_win:
                        with_wins += 1
                    else:
                        against_wins += 1
                else:
                    if protag_win is rival_win:
                        with_losses += 1
                    else:
                        against_losses += 1
            for name in match:
                if match[name] is protag_win and name != protag_name:
                    friends.append(name)
                elif match[name] is not protag_win:
                    rivals.append(name)
        return with_wins, with_losses, against_wins, against_losses, friends, rivals

    def get_all_match_info_participants(self, summoner, begin_index=0, end_index=10):
        if begin_index >= end_index:
            end_index = begin_index+1
        participants = []
        account_id = summoner.account_id
        params = {'endIndex': end_index, 'beginIndex': begin_index}
        get_match_list_url = GET_MATCH_LIST_BY_ACCOUNT_ENDPOINT % account_id
        matches_data = self.get_request(get_match_list_url, headers=self.headers, params=params).json()
        for match in matches_data['matches']:
            match_id = match['gameId']
            if DEBUG:
                print("Checking %s" % match_id)
            participants.append(self.get_match_info_participants(match_id))
        return participants

    def get_match_info_participants(self, match_id):
        match_id = str(match_id)
        get_match_data_url = GET_MATCH_INFO_BY_MATCH_ID_ENDPOINT % match_id
        match_data = self.get_request(get_match_data_url, headers=self.headers).json()
        participants = dict()
        participant_team_dict = dict()
        winners = None
        for team in match_data['teams']:
            if team['win'] == 'Win':
                winners = team['teamId']
        for participant in match_data['participants']:
            participant_team_dict[participant['participantId']] = participant['teamId']
        for participant in match_data['participantIdentities']:
            participant_id = participant['participantId']
            player = participant['player']
            summoner_name = player['summonerName']
            account_id = player['currentAccountId']
            player = self.Player(account_id, summoner_name)
            participants[player.summoner_name] = True if participant_team_dict[participant_id] == winners else False
        return participants