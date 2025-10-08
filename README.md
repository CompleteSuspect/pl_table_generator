# Premier League Table Generator:

A Python program that builds a Premier League table from weekly match CSV files.
It validates input data, detects errors and exports a clean league table to CSV.

## Features:

- Validates team names using a whitelist text file.
- Checks for missing or invalid data (scores, team names, columns)
- Catches duplicated team names per week.
- Skips postponed matches ("TBD" scores).
- Accumulates results across multiple match weeks.
- Calculates all core stats:
	- Played, Wins, Draws, Losses.
	- Goals For (GF), Goals Against (GA).
	- Goal Difference (GD).
	- Points.
- Sorts correctly by Points > GD > GF > Team(alphabetical).
- Exports final table to "pl_table.csv".

## Design Notes:

The project is built around a clear four-phase pipeline:

1. **Collection** - Load and validate match week CSVs.
2. **Accumulation** - Build the table by iterating over fixtures per week.
3. **Calculation** - Update per-team stats based on match results.
4. **Formatting** - Sort and export the table to CSV.

Error handling follows a "fail fast" philosophy:
if any errors (other than postponed matches) are detected, the program exits.

## File Layout:

-match_week_1.csv
-match_week_2.csv
-whitelist.txt
-pl_table_generator.py
-pl_table.csv # output file

## Usage:

- Run from command line or Thonny:
	- python pl_table_generator.py
- Ensure sure match_week_x.csv files are in the same folder.
- Match week files must include the header: Team_Home,Home_Score,Team_Away,Away_Score
- Teams in the match week files must match the whitelist exactly.
- There must be 20 teams in the whitelist.

If errors are found, they'll be printed in the console with the row and column the error was found.

##Version History:

- V1 - Core validation, table generation, CSV export
- V2(planned) - Helper functions, postponed-match logic, cross file duplication check, improved error handling.

## Author:

Created by Craig Hammond - Python learner and data enthusiast.
Currently studying Data Science at the University of Essex Online.
