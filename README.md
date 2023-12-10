# Introduction
A little matchmaking algorithm to create balanced teams based on the players' 
skillratings. This simple algorithm was written for a fun tournament of Quake
Champions. We wanted to play team-based modes and rather than have the players
form the teams themselves we wanted to balance out the skills between the teams
to get exciting matches.

[**Streamlit frontend is available here.**](https://matchmaking.streamlit.app/)

## 1 Initial Seed

As a first step, players are subdivided into skill tiers. The number of
skill tiers is the same as the team size.
The best player from the highest skill tier is matched with the worst 
player from the lowest skill tier. From the middle skill tiers random 
players are chosen. For the next team the second best and 
the second worst are chosen plus random players from the middle skill tiers
then the third best/worst and so on. 

## 2 Balancing Algorithm

The optimization tries to minimize the score. As a scoring function first
the average skill ratings of all teams are calculated. The score is 
calculated from the maximum deviation a team has from the total average
skill rating.
In each iteration of the balancing algorithm two teams are chosen at 
random or the minimum and the maximum scoring teams based on the 
`min_max_pairing` flag. Single players are swapped between the two teams. 
After swapping the new score is calculated. If the swapping improves the 
overall score the changes are kept.
As stopping criteria either the number of iterations is used or the number
of iterations without a change.


## The Code

- The optimization algorithim is implemented in `matchmaking.py`.

- A streamlit frontend is implemented in `matchmaking_fe.py`.

- Command line implementation to read csv files and run the optimization: 
`cmd_create_teams.py`.

- Example input file: `test.csv`


## Running from the command line.

You can run the algorithm from the command line.

Team size of 4 (4 even teams).
```
python cmd_create_teams.py -i test.csv -s 4
```
Team size of 3 (one player will stay without a team).
```
python cmd_create_teams.py -i test.csv -s 3
```

## Run Streamlit Frontend Locally

```
streamlit run matchmaking_fe.py
```