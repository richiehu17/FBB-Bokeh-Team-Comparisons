import requests
import sys
import traceback
import pprint


# get all player stats


def get_team_names(season, league_id):
#     print('Calling ESPN API for Team Info')
    url = ('http://fantasy.espn.com/apis/v3/games/fba/seasons/{}/segments/0/leagues/{}')\
        .format(season, league_id)
    data = call_espn_api(league_id, url)
    return create_team_list(data['teams'])


def create_team_list(teams):
    team_list = []
    for team in teams:
        team_list.append(team['location'] + ' ' + team['nickname'])
    return team_list


# takes ESPN team info and creates dictionary relating team id and team name
def create_team_dictionary(teams):
    team_dict = {}
    for team in teams:
        team_dict[team['location'] + ' ' + team['nickname']] = team['id']
    return team_dict


# if stats dictionary doesn't have key, return 0 instead
def key_check(stats, key_val):
    if key_val in stats:
        return stats[key_val]
    else:
        return 0.0


def parse_stats(stats, player_name):
    player_stats = []
    try:
        player_fgm = key_check(stats['averageStats'], '13')
        player_fga = key_check(stats['averageStats'], '14')
        player_fg_pct = key_check(stats['averageStats'], '19')
        player_ftm = key_check(stats['averageStats'], '15')
        player_fta = key_check(stats['averageStats'], '16')
        player_ft_pct = key_check(stats['averageStats'], '20')
        player_3pm = key_check(stats['averageStats'], '17')
        player_reb = key_check(stats['averageStats'], '6')
        player_ast = key_check(stats['averageStats'], '3')
        player_stl = key_check(stats['averageStats'], '2')
        player_blk = key_check(stats['averageStats'], '1')
        player_to = key_check(stats['averageStats'], '11')
        player_pts = key_check(stats['averageStats'], '0')
        player_stats.append(round(player_fgm, 1))
        player_stats.append(round(player_fga, 1))
        player_stats.append('{:.3f}'.format(round(player_fg_pct, 3)))
        player_stats.append(round(player_ftm, 1))
        player_stats.append(round(player_fta, 1))
        player_stats.append('{:.3f}'.format(round(player_ft_pct, 3)))
        player_stats.append(round(player_3pm, 1))
        player_stats.append(round(player_reb, 1))
        player_stats.append(round(player_ast, 1))
        player_stats.append(round(player_stl, 1))
        player_stats.append(round(player_blk, 1))
        player_stats.append(round(player_to, 1))
        player_stats.append(round(player_pts, 1))
        return player_stats
    except KeyError:
        print(f'Error parsing stats for {player_name}')
        raise


def parse_roster_info(season, roster, scoring_period):
    player_list = []
    ir_list = []
    empty_stat_list = [0.0, 0.0, "0.000", 0.0, 0.0, "0.000", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    scoring_period_dict = {'2023': '00' + season, 'Last 7 Days': '01' + season,
                           'Last 15 Days': '02' + season, 'Last 30 Days': '03' + season,
                           '2023 Projections': '10' + season}
    scoring_period_id = scoring_period_dict[scoring_period]
    for player in roster:
        player_name = player['playerPoolEntry']['player']['fullName']
        injury_status = player['playerPoolEntry']['player']['injuryStatus']
        player_injury = False
        # do something about this?
        if (injury_status == 'DAY_TO_DAY') or (injury_status == 'OUT'):
            player_injury = True
        player_stats = [player_name, player_injury]
        for stats in player['playerPoolEntry']['player']['stats']:
            # check for correct season and if stats dictionary is empty (injury)
            if stats['id'] == scoring_period_id:
                if 'averageStats' not in stats:
                    player_stats += empty_stat_list
                else:
                    player_stats += parse_stats(stats, player_name)
        if player['lineupSlotId'] >= 13:
            ir_list.append(player_stats)
        else:
            player_list.append(player_stats)
    return player_list, ir_list


def generate_team_sums(player_list):
    player_sums = ['Total', '', 0.0, 0.0, None, 0.0, 0.0, None, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for player in player_list:
        for i in range(2, 15):
            # fg% and ft% cases
            if i != 4 and i != 7:
                player_sums[i] += player[i]
    for i in range(2, 15):
        if i != 4 and i != 7:
            player_sums[i] = round(player_sums[i], 1)
    player_sums[4] = '{:.3f}'.format(round(player_sums[2] / player_sums[3], 3))
    player_sums[7] = '{:.3f}'.format(round(player_sums[5] / player_sums[6], 3))
    return player_sums


def generate_team_diff(team1_sums, team2_sums):
    team_diff = ['Differences', None, None, '', None, None, '', None, None, None, None, None, None, None]
    for i in range(1, 14):
        if i == 3 or i == 6:
            diff = float(team1_sums[i]) - float(team2_sums[i])
            if diff > 0:
                team_diff[i] = '{0:+.3f}'.format(round(diff, 3))
            else:
                team_diff[i] = '{:.3f}'.format(round(diff, 3))
        else:
            diff = float(team1_sums[i]) - float(team2_sums[i])
            if diff > 0:
                team_diff[i] = '{0:+.1f}'.format(round(diff, 1))
            else:
                team_diff[i] = round(diff, 1)
    return team_diff


def get_roster_info(season, league_id, scoring_period, team_id):
    url = ('http://fantasy.espn.com/apis/v3/games/fba/seasons/{}/segments/0/leagues/{}?view=mRoster&'
           'rosterForTeamId={}').format(season, league_id, team_id)
    roster_info = call_espn_api(league_id, url)['teams'][team_id - 1]['roster']['entries']
    return parse_roster_info(season, roster_info, scoring_period)

def call_espn_api(league_id, url):
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as ex:
        print('Could not make ESPN API call')
        traceback.print_exc()
        # abort(500)
        sys.exit()
    data = r.json()
    return data

def get_team_info(season, league_id):
    url = ('http://fantasy.espn.com/apis/v3/games/fba/seasons/{}/segments/0/leagues/{}')\
        .format(season, league_id)
    data = call_espn_api(league_id, url)
    status = 'public'
    if 'status' not in data:
        print('error get team info')
        status = 'private'
    return status, data['teams']