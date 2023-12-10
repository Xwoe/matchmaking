import os
import time

import numpy as np
import pandas as pd

from log import get_logger

logger = get_logger(__name__)


def check_input(df):
    df.columns = [c for c in df.columns]
    err_msg = f"Columns, which have to be present in the csv file: "
    found_error = False
    if "skill" not in df.columns:
        err_msg += '"skill"'
        found_error = True
    elif "player" not in df.columns:
        err_msg += ' "player"'
        found_error = True
    else:
        # check numbers in skill
        try:
            df["skill"].astype(float)
            if df["skill"].isna().any():
                err_msg = "Skill column has missing values"
                return err_msg

        except ValueError:
            err_msg = "Skill column contains non number entries."
            print(err_msg)
            return err_msg

    if found_error:
        return err_msg


class MatchMaking:
    """
    Implementation of a matchmaking algorithm to create balanced teams based on
    a skill rating.

    On initialization an initial seed is performed. When calling the `optimize`
    function the algorithm to balance the teams is being run.

    Initial seed
    ------------
    As a first step, players are subdivided into skill tiers. The number of
    skill tiers is the same as the team size.
    The best player from the highest skill tier is matched with the worst
    player from the lowest skill tier. For the next team the second best and
    the second worst are chosen and so on. From the middle skill tiers random
    players are chosen.

    Balancing Algorithm
    -------------------
    The optimization tries to minimize the score. As a scoring function first
    the average skill ratings of all teams are calculated. The score is
    calculated from the maximum deviation a team has from the total average
    skill rating.
    In each iteration of the balancing algorithm two teams are chosen at
    random or the minimum and the maximum scoring teams based on the
    `min_max_pairing` flag). Single players are swapped between the two teams.
    After swapping the new score is calculated. If the swapping improves the
    overall score - the changes are kept.
    As stopping criteria either the number of iterations is used or the number
    of iterations without a change.

    """

    def __init__(
        self,
        df,
        teamsize=3,
        min_max_pairing=False,
        noise_size=10000,
        noise_digits=2,
        to_file=False,
    ):
        """
        Parameters
        ----------
        df: pandas.DataFrame
            Must contain a 'skill' columns.
        teamsize: int
            Size of the teams.
        min_max_pairing: boolean
            If true as swapping pairs the team with the maximum and the
            minimum deviation are used. Not recommended as the algorithm can
            quickly get stuck in a local minimum.
        noise_size: int
            Size of the Laplace noise, which is added.
        noise_digits: int
            Number of digits, which are used to round off the noised values.
        """
        logger.info("... starting matchmaking")
        self.num_iterations = 0
        self.df = self._process_df(df)
        self.num_players = df.shape[0]
        self.teamsize = teamsize
        self.num_groups = self.num_players // self.teamsize
        self.to_file = to_file
        self._set_outputdir()
        self.min_max_pairing = min_max_pairing
        self._add_noise(noise_size, noise_digits)
        self._set_bins()
        self._init_teams()

    def _process_df(self, df):
        df["skill"] = df["skill"].astype(float)
        return df

    def _set_outputdir(self):
        """
        Create a subfolder `output` as subdirectory of the script.
        """
        if self.to_file:
            self.OUTPUTDIR = os.path.join(os.getcwd(), "output")
            os.makedirs(self.OUTPUTDIR, exist_ok=True)

    def _add_noise(self, noise_size, noise_digits):
        """
        In order to avoid problems with binning by skill values in `set_bins` a
        little Laplace noise is being added. If we have two or more players
        with the exact same skillrating at a bin's edge this will lead to
        uneven team sizes.

        Parameters
        ----------
        noise_size: int
            Size of the Laplace noise, which is added.
        noise_digits: int
            Number of digits, which are used to round off the noised values.
        """
        self.df["original_skill"] = self.df["skill"]
        self.df["skill"] = np.round(
            np.random.laplace(
                self.df["skill"], self.df["skill"] / noise_size, self.df.shape[0]
            ),
            noise_digits,
        )

    def _set_bins(self):
        """
        Put players into skill tiers (bins). The number of bins depends on
        `self.teamsize`.
        """
        self.df["skill_bin"], self.bins = pd.qcut(
            self.df.skill, self.teamsize, retbins=True, labels=False
        )
        self.max_bin = self.df.skill_bin.max()
        self.min_bin = self.df.skill_bin.min()

    def _init_teams(self):
        """
        Intitial seeding for teams. The best player from the highest skill tier
        is matched with the worst player from the lowest skill tier. For the
        next team the second best and the second worst are chosen and so on.
        From the middle skill tiers random players are chosen.
        """
        self.df["team"] = -1
        for team_num in range(self.num_groups):
            logger.info(f"team_num: {team_num}")
            _df = self.df[self.df["team"] == -1]
            for skill_bin, group in _df.groupby("skill_bin"):
                skill_tier = ""
                if skill_bin == self.max_bin:
                    idx = group["skill"].idxmax()
                    self.df.loc[idx, "team"] = team_num
                    skill_tier = "BEST"

                elif skill_bin == self.min_bin:
                    idx = group["skill"].idxmin()
                    self.df.loc[idx, "team"] = team_num
                    skill_tier = "MIN"

                else:
                    idx = np.random.choice(group.index)
                    self.df.loc[idx, "team"] = team_num
                    skill_tier = "MEDI"

            logger.info(
                f"skill_tier: {skill_tier} skill_bin: "
                + "{skill_bin}, team_num: {team_num}"
            )

        self._update_team_means()

    def _update_team_means(self):
        """
        Update the average team deviation and update the overall score.
        """
        self.team_means = self.calc_team_means(self.df)
        self.score = self.calc_score(self.team_means)
        self.num_iterations += 1

    def swap_teams(self):
        """
        The main optimization mechanism. Take two random teams (or the minimum
        and the maximum scoring teams) and swap single players between them. If
        the swapping improves the overall score - keep the changes.
        """
        # get the groups with the highest and the lowest deviations
        if self.min_max_pairing:
            team_0 = self.team_means.idxmin()
            team_1 = self.team_means.idxmax()
        else:
            team_ids = np.random.choice(list(self.team_means.index), 2, replace=False)
            team_0 = team_ids[0]
            team_1 = team_ids[1]

        logger.info(f"try swapping team {team_0} and team {team_1}")

        idxs_0 = list(self.df[self.df.team == team_0].index)
        idxs_1 = list(self.df[self.df.team == team_1].index)

        combos = self.get_idx_combos(idxs_0, idxs_1)

        swapped = False
        # swap members: if score gets smaller through swapping
        # -> update everything
        for combo in combos:
            _df = self.df.copy()
            _df.loc[combo[0], "team"] = team_0
            _df.loc[combo[1], "team"] = team_1

            team_means = self.calc_team_means(_df)
            score = self.calc_score(team_means)
            self.num_iterations += 1

            if score < self.score:
                self.score = score
                self.team_means = team_means
                self.df = _df
                logger.info(f"{combo[0]} {combo[1]} new score: {score}")
                swapped = True

        return swapped

    def optimize(self, max_iter=1000, max_counter=10):
        """
        Run the optimization algorithm.

        Parameters
        ----------
        max_iter: int
            Maximum number of iterations.
        max_counter: int
            Counter goes up with each iteration without an improvement. If
            there hasn't been an improvement since `max_counter` number of
            iterations, iteration will be aborted.
        """
        counter = 0
        iter_num = 0
        while (counter < max_counter) & (iter_num < max_iter):
            swapped = self.swap_teams()
            iter_num += 1

            if swapped:
                counter = 0
            else:
                counter += 1
            logger.info(f"Iteration {iter_num}, best score: {self.score}")
        logger.info(f"Best result: {self.score}")
        self._prepare_results()
        return self.df

    def _prepare_results(self):
        """
        Write the results of the optimization to a .csv file. Before storing
        the table is being sorted by teams.
        """
        self.df.sort_values("team", inplace=True)
        self.df["mean_dev"] = self.df["team"].apply(lambda x: self.team_means[x])
        self.df = self.df.rename(
            columns={"skill": "skill_plus_noise", "original_skill": "skill"}
        )
        self.df["team"] = self.df["team"] + 1
        if self.to_file:
            self.df.to_csv(
                os.path.join(self.OUTPUTDIR, f"et_groupsize_{self.teamsize}.csv")
            )
        logger.info("\n" + self.df.to_string())

    @staticmethod
    def get_idx_combos(idxs_0, idxs_1):
        """
        Get all combinations of two sets of indices when swapping only one
        member between the two sets.
        """
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
        """
        The team means are the differences of the team's player's mean skill to
        the overall mean skill of all players.
        """
        means = df.groupby("team")["skill"].mean()
        return means - means.mean()

    @staticmethod
    def calc_score(means_dev):
        """
        Calculate the score for the optimization function. The score is defined
        as the maximum deviation a team's skill has from the total average
        skill.
        """
        return np.abs(means_dev).max()
