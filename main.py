# External imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Internal imports
from stats import *

# Builtins
import json
import os
import pickle

CONF_FILE = 'conf.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def process_statistics(hearts_data):
    """
    Process the statistics

    :param hearts_data: The latest hearts data
    :return:
    """
    game_data = hearts_data["games"]
    expanded_data = hearts_data["expanded_data"]
    player_data = hearts_data["player_data"]
    players = []
    for row in player_data[1:]:
        first_name = row[3]
        last_name = row[4]
        player_id = int(row[2])
        tag = row[1]
        rating = float(row[5])
        players.append(Player(
            rating,
            first_name,
            last_name,
            tag,
            player_id
        ))
    game_chunks = []
    curr_games = {
        "sheet_left": [],
        "sheet_right": []
    }

    def resolve_chunk(slice, players, curr_chunk):
        """

        :param slice: The table slice to process
        :param game_chunks: The current state of games
        :param players: The list of current player objects
        :return line_data: The first step sanitized data to put into the sectional sheet chunk
        """
        def resolve_name(name, players):
            """
            Given a name and the list of Player objects, match it to a player
            (currently assuming all players have distinct first names!!)

            :param name: The name to find
            :param players: The list of players
            :return player: A Player object representing who that is
            """
            for p in players:
                if p.first_name == name:
                    return p
            return None
        line_data = {}
        try:
            game_id = int(slice[0])
            line_data.update({"game_id": game_id})
            # Resolve player names
            for idx, name in enumerate(slice[1:]):
                player = resolve_name(name, players)
                if player:
                    line_data.update({f"player_{idx}": player})
                else:
                    print(f"Warning: could not resolve name {name} from {slice}")
                    continue
        # Not an id row
        except ValueError:
            identifier = slice[0]
            assert identifier in ["Old Rating", "New Rating", "Right", "Left", "Across", "Hold", "Total"]
            line_data.update({"identifier": identifier})
            for idx, val in enumerate(slice[1:]):
                # Match an index to a player
                relevant_player = curr_chunk[0][f"player_{idx}"]
                if identifier in ["Old Rating", "New Rating"]:
                    val = float(val)
                else:
                    val = int(val)
                line_data.update({relevant_player: val})
        return line_data
    for game_row in game_data:
        if game_row:
            try:
                if game_row[0] and game_row[0] != "x" and game_row[1]:
                    left_data = resolve_chunk(game_row[0:5], players, curr_games["sheet_left"])
                    curr_games["sheet_left"].append(left_data)
                if game_row[6] and game_row[6] != "x" and game_row[7]:
                    right_data = resolve_chunk(game_row[6:11], players, curr_games["sheet_right"])
                    curr_games["sheet_right"].append(right_data)
            except IndexError:
                continue
        else:
            if curr_games["sheet_left"]:
                game_chunks.append(curr_games["sheet_left"])
            if curr_games["sheet_right"]:
                game_chunks.append(curr_games["sheet_right"])
            curr_games = {
                "sheet_left": [],
                "sheet_right": []
            }
    games = []
    for game_data in game_chunks:
        games.append(Game(game_data))
    print('\n------\n'.join([str(g) for g in games]))


def extract_data(conf_data):
    """
    Get data from the google sheet where larry records Hearts scores

    :param conf_data: The configuration
    :return values: A 2d array of rows and columns containing all the rows
    """
    sheet_id = conf_data['sheet_id']
    hearts_data = {}
    for page_range in conf_data['range']:
        range = f'{page_range["page"]}!{page_range["start"]}:{page_range["end"]}'
        print(f"Loading in data from sheet {sheet_id} range {range}")
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(host='localhost', port=5000)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id,
                                    range=range).execute()
        values = result.get('values', [])
        hearts_data.update({page_range["name"]: values})
    return hearts_data


def load_configuration(configuration_file):
    """
    Load configuration data in from a JSON file

    :param configuration_file: The path of the file to load in data from

    :return conf_data: The loaded data
    """
    assert os.path.isfile(configuration_file)
    conf_data = json.loads(open(configuration_file, encoding='utf-8').read())
    required_keys = ['sheet_id', 'range']
    for key in required_keys:
        assert key in conf_data.keys()
    return conf_data


if __name__ == "__main__":
    conf = load_configuration(CONF_FILE)
    hearts_data = extract_data(conf)
    with open('hearts_data.json', 'w') as outfile:
        outfile.write(json.dumps(hearts_data, indent=4))
    process_statistics(hearts_data)
