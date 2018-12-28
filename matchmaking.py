import pandas as pd
import numpy as np
import os

class MatchMaking:

    def __init__(self, df, m_players=15, r_groupsize=3, n_groups=5, 
        outpath='D:/DEV/even_teams/', min_max_pairing=False):

        self.m_players = m_players
        self.r_groupsize = r_groupsize
        self.n_groups = n_groups
        self.outpath = outpath
        self.min_max_pairing = min_max_pairing
        self.df = df
        self._set_bins()
        self._init_teams()

    

    def _set_bins(self):
        
        #TODO doesn't work if we have the same value for two
        # check if after cutting one member has not been assigned: put it into the smaller
        # bin or something
        self.df['skill_bin'], self.bins = pd.qcut(self.df.skill,
                                                self.r_groupsize,
                                                retbins=True,
                                                labels=False)
        self.max_bin = self.df.skill_bin.max()
        self.min_bin = self.df.skill_bin.min()

    def _init_teams(self):
        
        self.df['team'] = -1
        for team_num in range(self.n_groups):
            print(f'team_num: {team_num}')
            _df = self.df[self.df['team'] == -1]
            for skill_bin, group in _df.groupby('skill_bin'):
                
                skill_tier = ''
                if skill_bin == self.max_bin:
                    idx = group['skill'].idxmax()
                    self.df.loc[idx, 'team'] = team_num
                    skill_tier = 'BEST'
                
                elif skill_bin == self.min_bin:
                    idx = group['skill'].idxmin()
                    self.df.loc[idx, 'team'] = team_num
                    skill_tier = 'MIN'

                else:
                    idx = np.random.choice(group.index)
                    self.df.loc[idx, 'team'] = team_num
                    skill_tier = 'MEDI'

                print(f'skill_tier: {skill_tier}. skill_bin: {skill_bin}, team_num: {team_num} ')

        self._update_team_means()

    def _update_team_means(self):
        self.team_means = self.calc_team_means(self.df)
        self._update_score()

    def _update_score(self):
        self.score = self.calc_score(self.team_means)

    def swap_teams(self):

        # get the groups with the highest and the lowest deviations
        if self.min_max_pairing:
            team_0 = self.team_means.idxmin()
            team_1 = self.team_means.idxmax()
        else:
            team_ids = np.random.choice(list(self.team_means.index), 2)
            team_0 = team_ids[0]
            team_1 = team_ids[1]


        print(f'team_0: {team_0}, team_1: {team_1}')

        idxs_0 = list(self.df[self.df.team == team_0].index)
        idxs_1 = list(self.df[self.df.team == team_1].index)

        combos = self.get_idx_combos(idxs_0, idxs_1)
        
        swapped = False
        # swap members: if score gets smaller through swapping -> update everything
        for combo in combos:
            _df = self.df.copy()
            _df.loc[combo[0], 'team'] = team_0
            _df.loc[combo[1], 'team'] = team_1

            team_means = self.calc_team_means(_df)
            score = self.calc_score(team_means)
            
            if score < self.score:
                self.score = score
                self.team_means = team_means
                self.df = _df
                print(f'{combo[0]} {combo[1]} new score: {score}')
                swapped = True

        return swapped

    def optimize(self, max_iter=100, max_counter=10):

        old_score = self.score.copy()
        counter = 0
        iter_num = 0
        while (counter < max_counter) & (iter_num < max_iter):
            swapped = self.swap_teams()
            iter_num += 1
            
            if swapped:
                counter = 0
            else:
                counter += 1
        self._write_result()

    def _write_result(self):
        self.df.sort_values('team', inplace=True)
        self.df['mean_dev'] = self.df['team'].apply(lambda x: self.team_means[x])
        self.df.to_csv(os.path.join(self.outpath,
            f'et_groupsize_{self.r_groupsize}.csv'))



    @staticmethod
    def get_idx_combos(idxs_0, idxs_1):
        
        combos = []
        for idx_0 in idxs_0:
            for idx_1 in idxs_1:
                _idxs_0 = idxs_0.copy()
                _idxs_1 = idxs_1.copy()
                _idxs_0.remove(idx_0)
                _idxs_0.append(idx_1)
                _idxs_1.remove(idx_1)
                _idxs_1.append(idx_0)
                combos.append((_idxs_0, _idxs_1))
        return combos

    @staticmethod
    def calc_team_means(df):
        means = df.groupby('team')['skill'].mean()
        return means - means.mean()

    @staticmethod
    def calc_score(means_dev):
        return np.abs(means_dev).max()
    

