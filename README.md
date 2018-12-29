# Introduction
A little matchmaking algorithm to create balanced teams based on the players' 
skillratings. This simple algorithm was written for a fun tournament of Quake
Champions. We wanted to play team-based modes and rather than have the players
form the teams themselves we wanted to balance out the skills between the teams
to get exciting matches.

In Quake Champions we used to have two skill ratings, which are based on the 
[Glicko-2 rating system](https://en.wikipedia.org/wiki/Glicko_rating_system) as
far as I know. One skill rating is the skill for Duel mode and the other one 
for the 2on2 mode. The latter unfortunately has been removed in the December
2018 patch of the game (please bring it back!). I will describe how I 
preprocessed this data and how the optimization 
algorithm works.

# Matchmaking Algorithm

## 1 Preprocessing the Data
First all available skill ratings of the participating players where gathered
using a simple Google Sheet.
If the skill rating was not available I had the players guess them or I made 
an estimation myself.
We need one single skill value for each player to create a good algorithm so I 
calculated the means of the Duel and 2on2 skill ratings. The 2on2 rating is 
probably the better estimation for team based modes, but you have to work with 
what you got.



## 2 Initial Seed

As a first step, players are subdivided into skill tiers. The number of
skill tiers is the same as the team size.
The best player from the highest skill tier is matched with the worst 
player from the lowest skill tier. From the middle skill tiers random 
players are chosen. For the next team the second best and 
the second worst are chosen plus random players from the middle skill tiers
then the third best/worst and so on. 

## 3 Balancing Algorithm

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

- Command line implementation to run the optimization and do the necessary 
preprocessing of the tables as they were exported from the Google Sheets: 
`cmd_create_teams.py`.

- Example input files: `gql_skillrating.csv` and `gql_skillrating_same_sr.csv`.


## Running from the command line.

You can run the algorithm from the command line.

Team size of 3 (5 even teams).
```
python cmd_create_teams.py -i gql_skillrating.csv -s 3
```
Team size of 8 (one team with 7, one with 8 players).
```
python cmd_create_teams.py -i gql_skillrating.csv -s 8
```

