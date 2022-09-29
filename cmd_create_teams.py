import argparse

import numpy as np
import pandas as pd

import matchmaking as mm
from log import get_logger

logger = get_logger(__name__)


def main():

    logger.info("#### Matchmaking by Xwoe ####")
    # initiate the parser
    argparser = argparse.ArgumentParser()

    # add long and short argument
    argparser.add_argument("--input", "-i", help="csv-file to read from.")
    argparser.add_argument("--size", "-s", help="size of the teams")

    # read arguments from the command line
    args = argparser.parse_args()
    logger.info(args)

    if args.input:
        df = pd.read_csv(args.input)
    else:
        argparser.print_help()
        return

    if args.size:
        size = args.size
    else:
        argparser.print_help()
        return

    if "skill" not in df.columns:
        df["skill"] = np.nan
        df["skill"] = df.apply(
            lambda row: np.nanmean([row["Duel SR"], row["2v2 SR"]]), axis=1
        )

    my_mm = mm.MatchMaking(df, teamsize=int(size))
    my_mm.optimize()
    logger.info(f"+++++ finished after {my_mm.num_iterations} iterations")


if __name__ == "__main__":
    main()
