from pathlib import Path
from collections import defaultdict

def get_whitelist(file_name = "whitelist.txt", teams_total = 20):
    
    p = Path(file_name)
    if not p.exists():
        print(f'Error. Team whitelist "{file_name}" is not in directory!\n')
        return None
    
    teams = [team.strip().lower() for team in p.read_text(encoding = "utf-8").split()]
    if len(teams) != 20:
        print(f'Error: {len(teams)} teams found instead of the allowed {teams_total}')
        print(f'Check "{file_name}" for unwanted spaces insead of underscores in team names.')
        return None

    return set(teams)
   
def get_fixtures(file, white_list):
    temp_valids = []
    errors = []
    raw = file.read_text(encoding = "utf-8")
    #create enumerated row_idxs 
    fixtures = [(row_idx, fixtures.strip().lower()) for row_idx, fixtures in enumerate(raw.splitlines())]
    #check the header integrity
    header = fixtures[0][1].lower()
    if header != "team_home,home_score,team_away,away_score":
        errors.append({"error": "BAD_HEADER",
                           "data": header,
                           "row_idx": 0,
                           "col_idx": None
                          })
        
        return [], errors
    
    #create enumerated columns (fields)
    for row_idx, fixture in fixtures[1:]:
        fields = [(col_idx, fixture) for col_idx, fixture in enumerate(fixture.split(','))]
        row_errors = []
        
        #check for not 4 fields, discard row if True
        if len(fields) != 4:
            errors.append({"error": "NOT_4_FIELDS",
             "data": fixture,
             "row_idx": row_idx,
             "col_idx": None
             })
            continue
        
        #check if both teams within a fixture have been postponed
        if len([field for field in fields if field[1] == "tbd"]) == 2:
            row_errors.append({"error": "POSTPONED",
                   "data": fixture,
                   "row_idx": row_idx,
                   "col_idx": (1, 3)
                  })
            
            
        #check each field for errors (falsey, whitelist, and score is int)
        for col_idx, field in fields:
            #check falsey
            if not field:
                row_errors.append({"error": "MISSING_VALUE",
                                   "data": fixture,
                                   "row_idx": row_idx,
                                    "col_idx": col_idx
                                  })
            
            #check team names against whitelist
            elif col_idx in (0, 2):
                if field not in white_list:
                    row_errors.append({"error": "INVALID_TEAM",
                                       "data": fixture,
                                       "row_idx": row_idx,
                                       "col_idx": col_idx
                                      })
                
            #check score only if fixure has not been found to be postponed
            elif col_idx in (1,3):       
                if all([error.get("error") != "POSTPONED" for error in row_errors]):
                    try:
                        int(field)
                        if int(field) < 0:
                            row_errors.append({"error": "NEGATIVE_SCORE",
                                               "data": fixture,
                                               "row_idx": row_idx,
                                               "col_idx": col_idx
                                              })
                                            
                    except ValueError:
                        row_errors.append({"error": "INVALID_SCORE",
                                           "data": fixture,
                                           "row_idx": row_idx,
                                           "col_idx": col_idx
                                          })
                
            #end of per field actions  
        if row_errors:
            errors.extend(row_errors)
        
        else:
            (h, h_s, a, a_s) = (f for _, f in fields)
            temp_valids.append({"row": row_idx,
                                "home_team": h,
                                "home_score": int(h_s),
                                "away_team": a,
                                "away_score": int(a_s)
                               })
            
        #end of per row actions
    
    #duplicate check on valids list
    seen = defaultdict(list)
    for valid in temp_valids:
        seen[valid['home_team']].append(valid['row'])
        seen[valid['away_team']].append(valid['row'])
    bad_rows = {row for rows in seen.values() if len(rows) > 1 for row in rows}
    
    for rows in seen.values():
        if len(rows) > 1:
            errors.append({"error": "DUPLICATE_TEAMS",
                     "data": [fixtures[row_idx][1] for row_idx in rows],
                     "row_idx": rows,
                     "col_idx": None #add column numbers in future
                     })
        
            
    valids = [v for v in temp_valids if v['row'] not in bad_rows]
    return (valids, errors)

def generate_table(fixtures, table):
    #unpacking fixtures into 4 variables
    for fx in fixtures:
        h_t, h_s= fx['home_team'], fx['home_score']
        a_t, a_s = fx['away_team'], fx['away_score']
        
        #forming the default dicts for home and away teams:
        for team in (h_t, a_t): 
            table.setdefault(team,{"played": 0,
                                "home_wins": 0,
                                "away_wins": 0,
                                "home_draws": 0,
                                "away_draws":0,
                                "home_losses": 0,
                                "away_losses": 0,
                                "home_gf": 0,
                                "away_gf": 0,
                                "home_ga": 0,
                                "away_ga": 0,
                                "gd": 0,
                                "points": 0,
                                "last5" : [] #temporary list for accumulation
                                })
            
        #accumulating table data based off match results:
        table[h_t]['played'] += 1
        table[a_t]['played'] += 1
        
        if h_s > a_s:
            table[h_t]['home_wins'] += 1
            table[h_t]['points'] += 3
            table[a_t]['away_losses'] += 1
            table[h_t]["last5"].append("W")
            table[a_t]["last5"].append("L")
            
        elif h_s < a_s:
            table[a_t]['away_wins'] += 1
            table[a_t]['points'] += 3
            table[h_t]['home_losses'] += 1
            table[h_t]['last5'].append("L")
            table[a_t]['last5'].append("W")
            
        else:
            table[h_t]['home_draws'] += 1
            table[h_t]['points'] += 1
            table[a_t]['away_draws'] += 1
            table[a_t]['points'] += 1
            table[h_t]['last5'].append("D")
            table[a_t]['last5'].append("D")
        
        #calculating gf,gf,gd
        table[h_t]['home_gf'] += h_s
        table[h_t]['home_ga'] += a_s
        table[a_t]['away_ga'] += h_s
        table[a_t]['away_gf'] += a_s
        
        for t in (h_t, a_t):
            table[t]['gd'] = (table[t]['home_gf'] + table[t]['away_gf']) - (table[t]['home_ga'] + table[t]['away_ga'])

    return table

def sort_table(table: dict[str, dict]) -> list[tuple[str, dict]]:
    """Return teams sorted by points, GD, GF and name"""
    
    return sorted(table.items(),
                   key = lambda item: (-item[1]['points'],
                                       -item[1]['gd'],
                                       -(item[1]['home_gf'] + item[1]['away_gf']), #total gf
                                        item[0]
                                       )
                )

def write_csv(table):
    p = Path("pl_table.csv")
    
    #print generated table and output generated table to csv
    print(f"{'Pos':<3} {'Team':<15} {'MP':<3} {'W':<2} {'D' :<2} {'L':<2} {'GF':<3} {'GA':<3} {'GD':<3} {'Pts':<3} {'Last5':<4}")
    out_txt = "Pos,Team,MP,H_W,A_W,H_D,A_D,H_L,A_L,H_GF,A_GF,H_GA,A_GA,GD,Pts,Last_5\n"

    for idx, (team, stats) in enumerate(table, start = 1): #print and accumilate output text string
        stats['last5'] = ''.join(stats['last5'][-5:])
        print(f"{idx:<3} {team.capitalize():<15}"
              f"{stats['played']:>3}"
              f"{stats['home_wins'] + stats['away_wins']:>3}" #total wins
              f"{stats['home_draws'] + stats['away_draws']:>3}" #total draws
              f"{stats['home_losses'] + stats['away_losses']:>3}" # total losses
              f"{stats['home_gf'] + stats['away_gf']:>4}" #total gf
              f"{stats['home_ga'] + stats['away_ga']:>4}" #total ga
              f"{(stats['home_gf'] + stats['away_gf']) - (stats['home_ga'] + stats['away_ga']):>4}" #total gd
              f"{stats['points']:>4}"
              f"{stats['last5']:>7}"
             )
        
        out_txt += (f"{idx},{team.capitalize()},{','.join(str(stat) for stat in stats.values())}\n")
        
    try:
        p.write_text(out_txt, encoding = "utf-8")
        
    except PermissionError as e:
        print(e)
        return None


def main():
    table = {} #PL_table dictionary before sort
    all_errors = []
    whitelst = get_whitelist()
    week = 1
    
    if not whitelst:
        print("Error: no valid whitelist!")
        return None

    while True:
        p = Path(f"match_week_{week}.csv")
        
        if p.exists():
            print(f"Parsing {p}")
            fixtures, errors = get_fixtures(p, whitelst)
            
            if errors:  
                #accumulate table if all errors are postponed
                if all(error.get('error') == "POSTPONED" for error in errors):
                    table = generate_table(fixtures, table)
                    
                    for error in errors:
                        error['week'] = week
                        print(error)
                        
                else:
                    #or append error to all_errors
                    print(len(errors), "error(s) were found!")
                    for error in errors:
                        error['week'] = week #add week to the error
                        all_errors.append(error)
                        print(error)
                        
                
            else:
                table = generate_table(fixtures, table)
                
            week += 1
        
        else:    
            print("No further files found, done!\n")
            break
    
    if not all_errors:
        write_csv(sort_table(table))
        return None
    
    else:
        print("Errors found, could not generate table!")
        return None
        
if __name__ == "__main__":
    main()