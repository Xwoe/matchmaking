import argparse
import numpy as np
import pandas as pd 

import matchmaking as mm

from log import get_logger
logger = get_logger(__name__)


def main():


     # initiate the parser
    parser = argparse.ArgumentParser()

    # add long and short argument
    parser.add_argument("--input", "-i",
                        help="csv-file to read from.")
    parser.add_argument("--size", "-s", help="size of the teams")

    # read arguments from the command line
    args = parser.parse_args()

    if args.input:
        df = pd.read_csv(args.input)
    else:
        parser.print_help()

    if args.size:
        size = args.size
    else:
        parser.print_help()

    if 'skill' not in df.columns:
        df['skill'] = np.nan
        df['skill'] = df.apply(lambda row: np.nanmean([row['SR_Duel'], row['SR_2v2']]), 
                               axis=1)

    my_mm = mm.MatchMaking(df, teamsize=int(size))
    my_mm.optimize()


if __name__ == '__main__':
    main()