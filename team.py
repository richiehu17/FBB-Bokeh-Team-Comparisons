import pandas as pd

import espn_api as api

class Team:
    def __init__(self, season, league_id, scoring_period):
        self.season = season
        self.league_id = league_id
        self.scoring_period = scoring_period

        self.df_cols = ['Player', 'Injured', 'FGM', 'FGA', 'FG%', 'FTM', 'FTA', 'FT%', '3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS']
        self.df_cols2 = ['Player', 'FGM', 'FGA', 'FG%', 'FTM', 'FTA', 'FT%', '3PM', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PTS']

        self.name = None
        self.team_id = None
        self.roster = None
        self.sums = None
        self.IR = None

    def get_scoring_period(self):
        return self.scoring_period

    def get_name(self):
        return self.name

    def get_team_id(self):
        return self.team_id

    def get_roster(self):
        return self.roster

    def get_sums(self):
        return self.sums

    def get_IR(self):
        return self.IR

    def set_scoring_period(self, scoring_period):
        self.scoring_period = scoring_period
        return

    def set_name(self, name):
        self.name = name
        return

    def set_team_id(self, team_id):
        self.team_id = team_id
        return

    def set_roster(self, roster):
        self.roster = roster
        return

    def set_sums(self, sums):
        self.sums = sums
        return

    def set_IR(self, IR):
        self.IR = IR
        return


    # use len of team roster to determine blank spaces when joining data
    def get_team_data(self):
        roster_list, IR_list = api.get_roster_info(self.season, self.league_id, self.scoring_period, self.team_id)
        sums_list = api.generate_team_sums(roster_list)
        self.roster = pd.DataFrame(roster_list, columns=self.df_cols)[self.df_cols2]
        if len(IR_list) == 0:
            empty_df = pd.DataFrame([[''] * 15] + [['IR'] + [''] * 14] + [[''] * 15], columns=self.df_cols)[self.df_cols2]
            self.IR = empty_df
        elif len(IR_list) == 1:
            self.IR = pd.DataFrame([[''] * 15] + [['IR'] + [''] * 14] + IR_list + [[''] * 15] + [[''] * 15], columns=self.df_cols)[self.df_cols2]
        else:
            self.IR = pd.DataFrame([[''] * 15] + [['IR'] + [''] * 14] + IR_list + [[''] * 15], columns=self.df_cols)[self.df_cols2]
        self.sums = pd.DataFrame([sums_list], columns=self.df_cols)[self.df_cols2]
        return


    def output_team_data(self):
        return pd.concat([self.roster, self.IR, self.sums]).to_dict(orient='list')

    
    def output_team_data_df(self):
        return pd.concat([self.roster, self.IR, self.sums])
    
    
    def get_stat_diff(self, team2: 'Team'):
        diff_list = api.generate_team_diff(self.sums.loc[0, :].values.tolist(), team2.get_sums().loc[0, :].values.tolist())
        diff_df = pd.DataFrame([diff_list], columns=self.df_cols2)
        diff_df[['FGM', 'FGA', 'FTM', 'FTA']] = ''

        totals_team1 = self.sums.copy()
        totals_team1['Player'] = self.name
        totals_team2 = team2.get_sums().copy()
        totals_team2['Player'] = team2.get_name()

        return pd.concat([totals_team1, totals_team2, diff_df])

    
    def update_sums(self):
        temp_roster = self.roster.copy()
        temp_roster.insert(1, 'temp', [''] * 13)
        roster_list = temp_roster.values.tolist()
        sums_list = api.generate_team_sums(roster_list)
        sums = pd.DataFrame([sums_list], columns=self.df_cols)[self.df_cols2]
        self.set_sums(sums)
    
    
    def swap_IR(self, to_roster, to_IR):
        roster = self.roster
        IR = self.IR
        
        new_roster = pd.concat([roster, IR.loc[IR['Player'] == to_roster]])
        new_roster = new_roster[new_roster.Player != to_IR]
        self.set_roster(new_roster)
        
        new_IR = pd.concat([IR.drop(IR.tail(1).index), roster.loc[roster['Player'] == to_IR]])
        new_IR = new_IR[new_IR.Player != to_roster]
        new_IR = pd.concat([new_IR, pd.DataFrame([[''] * 14], columns=self.df_cols2)])
        self.set_IR(new_IR)
        
        self.update_sums()
        