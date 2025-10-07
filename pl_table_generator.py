from pathlib import Path
from collections import defaultdict
import sys

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
   
def get_fixtures(file_name, white_list):
    temp_valids = []
    errors = []
    
    p = Path(file_name)
    raw = p.read_text(encoding = "utf-8")
    #print(raw)
    
    #create enumerated row_idxs 
    fixtures = [(row_idx, fixtures.strip().lower()) for row_idx, fixtures in enumerate(raw.splitlines(True))]
    
    #check the header integrity
    header = fixtures[0][1].lower()
    if header != "team_home,home_score,team_away,away_score":
        errors.append({"error": "BAD_HEADER",
                           "data": header,
                           "row_idx": 0,
                           "col_idx": None
                          })
        return fixtures, errors
    
    #create enumerated columns (fields)
    #print('fixture:')
    for row_idx, fixture in fixtures[1:]:
        fields = [(col_idx, fixture) for col_idx, fixture in enumerate(fixture.split(','))]
        row_errors = []
        
        #check for not 4 fields, discard row if True
        if len(fields) != 4:
            row_errors.append({"error": "NOT_4_FIELDS",
             "data": fixture,
             "row_idx": row_idx,
             "col_idx": None
             })
            continue
        
        #check each field for errors (falsey, whitelist, "TBD" and score is int)
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
                
            #check team scores if int or "tbd"
            elif col_idx in (1,3):
                if field == "tbd":
                    row_errors.append({"error": "POSTPONED",
                                       "data": fixture,
                                       "row_idx": row_idx,
                                       "col_idx": col_idx
                                      })
                else:   
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
       # print(valid)
        seen[valid["home_team"]].append(valid["row"])
        seen[valid["away_team"]].append(valid["row"])
    bad_rows = {row for rows in seen.values() if len(rows) > 1 for row in rows}
    
    for rows in seen.values():
        if len(rows) > 1:
            errors.append({"error": "DUPLICATE_TEAMS",
                     "data": [fixtures[row_idx][1] for row_idx in rows],
                     "row_idx": rows,
                     "col_idx": None
                     })
    valids = [v for v in temp_valids if v["row"] not in bad_rows]
    
    return (valids, errors)

#check for None and exit
#start building dicts gf, ga,

#whitelist check if empty
#match_week check if empty

table = {}

#main input file loop
week = 1
while True:
    file_name = f"match_week_{week}.csv"
    p = Path(file_name)
    if p.exists():
        print(f"Parsing {file_name}")
        fixtures, errors = get_fixtures(file_name,get_whitelist()) #unpack fixtures, errors
        week += 1
    else:
        print(f"{file_name} not found. Done!\n")
        break
    
    #exit if errors, however continue if match postponed
    if errors and any(e.get("error") != "POSTPONED" for e in errors):
        for e in errors:
            if e["error"] != "POSTPONED":
                print(e)
        sys.exit(1)
    
    #unpacking fixtures into 4 variables
    for fx in fixtures:
        h_t, h_s= fx["home_team"], fx["home_score"]
        a_t, a_s = fx["away_team"], fx["away_score"]
        
        #forming the default dicts for home and away teams:
        for t in (h_t, a_t): 
            table.setdefault(t,{"played": 0,
                                "wins": 0,
                                "draws": 0,
                                "losses": 0,
                                "gf": 0,
                                "ga": 0,
                                "gd": 0,
                                "points": 0
                                })
            
        #accumulating table data based off match results:
        table[h_t]["played"] += 1
        table[a_t]["played"] += 1
        
        if h_s > a_s:
            table[h_t]["wins"] +=1
            table[h_t]["points"] += 3
            table[a_t]["losses"] +=1
            
        elif h_s < a_s:
            table[a_t]["wins"] += 1
            table[a_t]["points"] += 3
            table[h_t]["losses"] += 1
            
        else:
            table[h_t]["draws"] += 1
            table[h_t]["points"] += 1
            table[a_t]["draws"] += 1
            table[a_t]["points"] += 1
        
        #calculating gf,gf,gd
        table[h_t]["gf"] += h_s
        table[a_t]["ga"] += h_s
        table[h_t]["ga"] += a_s
        table[a_t]["gf"] += a_s
        table[h_t]["gd"] = table[h_t]["gf"] - table[h_t]["ga"]
        table[a_t]["gd"] = table[a_t]["gf"] - table[a_t]["ga"]
    
#sort data based on (pts, GD, GF, team name)
srt_table = sorted(table.items(),
                   key = lambda item: (-item[1]["points"], -item[1]["gd"], -item[1]["gf"], item[0])
                   )

p = Path("pl_table.csv")

#print generated table and output generated table to csv
print(f"{'Pos':<3} {'Team':<15} {'MP':<2} {'W':<2} {'D' :<2} {'L':<2} {'GF':<3} {'GA':<3} {'GD':<3} {'Pts':<3}", flush = True)
out_txt = "Pos,Team,MP,W,D,L,GF,GA,GD,Pts\n"

for idx, (team, stats) in enumerate(srt_table, start = 1): #print and accumilate output text string
    print(f"{idx:<3} {team.capitalize():<15}"
          f"{stats['played']:>2} {stats['wins']:>2} {stats['draws']:>2} {stats['losses']:>2}"
          f"{stats['gf']:>3} {stats['ga']:>3} {stats['gd']:>3} {stats['points']:>3}",
          flush = True)
    
    out_txt += (f"{idx},{team.capitalize()},{','.join(str(stat) for stat in stats.values())}\n")
    
try:
    p.write_text(out_txt, encoding = "utf-8")
except PermissionError as e:
    print(e)
    sys.exit(1)