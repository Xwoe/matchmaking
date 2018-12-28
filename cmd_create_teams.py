import pandas as pd 
import numpy as np
import matchmaking as mm


def main():
    df = pd.read_csv('D:/DEV/even_teams/gql_skillrating.csv')
    df['skill'] = np.nan
    df['skill'] = df.apply(lambda row: np.nanmean([row['SR_Duel'], row['SR_2v2']]), axis=1)

    my_mm = mm.EvenTeams(df)
    my_mm.optimize()

    my_mm = mm.EvenTeams(df, r_groupsize=8, n_groups=2)
    my_mm.optimize()


if __name__ == '__main__':
    main()