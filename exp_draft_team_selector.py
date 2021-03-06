import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import math

Teams = []
team_Plus_Minus = []
team_PS = []
team_Ztot = []
team_Avg_PlusMinus = 0.0
team_Std_PlusMinus = 0.0
team_Avg_Ztot = 0.0
team_Std_Ztot = 0.0
team_Avg_PS = 0.0
team_Std_PS = 0.0
team_Strength = None

# Noticed that in the player data, the list of values for Position ('Pos') changes
# occasionally. From 2011 to 2016 the list was 'C', 'D', 'LW' and 'RW'.  From
# From 2017 to 2019 'W' was added, and in 2020 'F' was added.  A player who is 
# listed as 'F' probably spends most of his time on the ice as a wing, since there
# are more centers in the league than wings. So 'F' and 'W' are considered 
# interchangeable. 
POSITION_LIST_WINGS = ['LW', 'RW', 'W', 'F']  
 

def load_setup(year):
    """ This function loads the original data to a dataframe and handles the initial 
    processing."""
    fname = "season" + str(year) + ".csv"
    df = pd.read_csv(fname,header=0, encoding='utf_16')

    # Add and calculate three new variables (extending for 82 games)
    # one for evaluating players and two for tracking.
    df['adjPTS'] = 82*df['PTS']/df['GP']
    df['adj+/-'] = 82*df['+/-']/df['GP']
    df['adjTOI'] = 82*df['TOI']/df['GP']
    df['M'] = 0       
    df['Status'] = 0
    df['Z+/-'] = 0.0
    df['Zpts'] = 0.0
    df['Ztot'] = 0.0       

    # When a players is traded, he has three or more lines in the data frame - 
    # One for each of the teams he played for and a TOTAL line.  Want the total line
    # with the team changed from TOT to the last team he played for.
    for i in range(len(df)):
        if df.iat[i,3] == 'TOT':
            n = df.iat[i,1]
            df_player = df[df['Player'] == n]
            l = len(df_player) -1
            pos = i
            df.iat[pos,3] = df_player.iat[l,3]
            for j in range(1,len(df_player)):
                df.iat[pos+j,31] = 1

    # Remove extra lines, leaving only the total line for traded players
    is_not_dup = df['M'] == 0
    df0 =  df[is_not_dup]   

    # Player's names have a code at the end, afterf a /, so remove that part.  
    for i in range(len(df0)):
        temp = df0.iat[i,1]
        place = temp.find('\\')
        df0.iat[i,1] = temp[0:place]  

    # Over time the NHL changed the abbreviations for the player's positions.
    # Data from 2019 adds 'C; LW'.  Need to account for these changes.  There
    # are very few of these, so we will consider 'C; LW' to be 'C'.
    df0.replace(to_replace='C; LW', value='C', inplace=True)

    global Teams
    Teams = df0['Tm'].unique()   

    df1 = _not_enough_games(df0)

    return df1

def remove_first_second_years(df, year):
    """ Players who are in their first or second years are exempt from the expansion draft.
    So need to remove them.""" 
    prev_year = year - 1
    fname_current = "debuts" + str(year) + ".csv"
    fname_prev = "debuts" + str(prev_year) + ".csv"
    df_deb_prev = pd.read_csv(fname_prev,header=0, encoding='utf_16')
    df_deb_current = pd.read_csv(fname_current,header=0, encoding='utf_16')
    debs_prev = list(df_deb_prev['Name'])
    debs_current = list(df_deb_current['Name'])

    for i in range(len(df)):
        if df.iat[i,1] in debs_prev or df.iat[i,1] in debs_current:
            df.iat[i,32] = 1

    df0 = df[df['Status'] == 0]

    return df0  

def _not_enough_games(df):
    """ Removes players who played less than 20 games.   These players were probably call-ups
    late in the season."""         
    return df[df['GP']>20]

def reduce_vars(df):
    """ Reduces the var list in the data frame to only those needed."""
    return df.iloc[:,[1,2,3,4,5,9,11,28,29,30,32,33,34,35]]

def calc_base_stats(df):    
    """ Calculates team stats - for Plus_Minus, PS, and Ztot. Ztot is a stat
    of my own creation."""
    global team_Plus_Minus
    global team_PS
    global team_Ztot
    for team in Teams:
        df2_myteam = df[df['Tm'] == team]
        team_Plus_Minus.append(df2_myteam['+/-'].sum())
        team_PS.append(df2_myteam['PS'].sum())
        team_Ztot.append(df2_myteam['Ztot'].sum())
    
    tot = 0
    global team_Avg_PlusMinus
    for i in team_Plus_Minus:
        tot += i
    team_Avg_PlusMinus = tot/len(team_Plus_Minus)    
    
    tot = 0
    global team_Std_PlusMinus
    for i in team_Plus_Minus:
        tot += (i - team_Avg_PlusMinus)**2
    team_Std_PlusMinus = math.sqrt(tot/len(team_Plus_Minus)) 

    tot = 0
    global team_Avg_PS
    for i in team_PS:
        tot += i
    team_Avg_PS = tot/len(team_PS)    
    
    tot = 0
    global team_Std_PS
    for i in team_PS:
        tot += (i - team_Avg_PS)**2
    team_Std_PS = math.sqrt(tot/len(team_PS)) 

    tot = 0
    global team_Avg_Ztot
    for i in team_Ztot:
        tot += i
    team_Avg_Ztot = tot/len(team_Ztot)    
    
    tot = 0
    global team_Std_Ztot
    for i in team_Ztot:
        tot += (i - team_Avg_Ztot)**2
    team_Std_Ztot = math.sqrt(tot/len(team_Ztot))

def calc_team_strength(df, year):
    # Calculate the strength of each team - and make a data frame with that information
    # Check if Golden Knights are exempt
    # The Vegas Golden Knights (VGK) were an expansion team in 2017, so they are immune
    # from expansion drafts from 2017 to 2019. They will be immune too when Seattle's
    # expansion draft happens in 2021. So from 2017 on need to remove their players.
    
    global Teams
    d = {'Team'}
    ts = pd.DataFrame(Teams, columns = d)    
    ts['Strength'] = 0.0    
    for i in range(len(ts)):
        z_Plus_Minus = (team_Plus_Minus[i] - team_Avg_PlusMinus)/team_Std_PlusMinus
        #z_PS = (team_PS[i] - team_Avg_PS)/team_Std_PS
        #z_Ztot = (team_Ztot[i] - team_Avg_Ztot)/team_Std_Ztot        
        ts.iat[i,1] = z_Plus_Minus
    
    # Need to remove Vegas Knights players if year is >= 2017    
    if year >= 2017:
        df1 = df[df['Tm'] != 'VEG']
        Teams = df1['Tm'].unique()
        ts1 = ts[ts['Team'] != 'VEG']
    else:
        df1 = df
        ts1 = ts   

    global team_Strength
    team_Strength = ts1.sort_values(by=['Strength'], ascending = False, axis=0)   
    return df1   

def calc_player_value(df):
    """ Calculates a player value using plus/minus stat and pts stat.  Complication
    is that there are different tiers of players. """ 

    topc = None
    topw = None
    topd = None
    lev2f = None
    botc = None
    botw = None
    botd = None   

    for team in Teams:
        df_team = df[df['Tm']==team]
        dfx = df_team.sort_values(axis=0, ascending=False,by=['adjTOI'])
        
        # Top two centers
        num_topc = 0
        for i in range(len(dfx)):
            if dfx.iat[i,4] == 'C':
                dfx.iat[i,32] = 1
                num_topc += 1
            if num_topc == 2:
                break
                
        df_c = dfx[dfx['Status']==1]
        if topc is None:
            topc = df_c
        else:
            topc = pd.concat([topc,df_c])        
        
        dfx1 = dfx[dfx['Status']==0]
        
        # Top two wings
        num_topw = 0
        for i in range(len(dfx1)):
            if dfx1.iat[i,4] in POSITION_LIST_WINGS:
                dfx1.iat[i,32] = 1
                num_topw += 1
            if num_topw == 2:
                break    
                
        df_w = dfx1[dfx1['Status']==1] 
        if topw is None:
            topw = df_w
        else:
            topw= pd.concat([topw,df_w])
            
        dfx2 = dfx1[dfx1['Status']==0]  
        
        # Top four defensemen
        num_topd = 0
        for i in range(len(dfx2)):
            if dfx2.iat[i,4] == 'D':
                dfx2.iat[i,32] = 1
                num_topd += 1
            if num_topd == 4:
                break  
                
        df_d = dfx2[dfx2['Status']==1]  
        if topd is None:
            topd = df_d
        else:
            topd= pd.concat([topd,df_d])
        
        dfx3 = dfx2[dfx2['Status']==0]
        
        # The next two wings
        num_lev2f = 0
        for i in range(len(dfx3)):
            if dfx3.iat[i,4] in POSITION_LIST_WINGS:
                dfx3.iat[i,32] = 1
                num_lev2f += 1
            if num_lev2f == 2:
                break  
                
        df_lev2f = dfx3[dfx3['Status']==1]
        if lev2f is None:
            lev2f = df_d
        else:
            lev2f= pd.concat([lev2f,df_lev2f])
            
        dfx4 = dfx3[dfx3['Status']==0]
        
        dfx4_def = dfx4[dfx4['Pos']=='D']
        dfx4_cent = dfx4[dfx4['Pos']=='C']
        dfx4_wings = dfx4[(dfx4['Pos']=='LW') | (dfx4['Pos']=='RW') | (dfx4['Pos']=='W') | (dfx4['Pos']=='F')]
        
        if botd is None:
            botd = dfx4_def
        else: 
            botd = pd.concat([botd,dfx4_def])
            
        if botc is None:
            botc = dfx4_cent
        else:
            botc = pd.concat([botc,dfx4_cent])
            
        if botw is None:
            botw = dfx4_wings
        else:
            botw = pd.concat([botw, dfx4_wings])
            
      
    num_c = 0
    num_d = 0
    num_w = 0
    for i in range(len(df)):
        if df.iat[i,4] == 'C':
            num_c += 1
            if num_c <= 2:
                df.iat[i,33] = (df.iat[i,29] - topc['adj+/-'].mean()) / topc['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - topc['adjPTS'].mean()) / topc['adjPTS'].std()
            else:
                df.iat[i,33] = (df.iat[i,29] - botc['adj+/-'].mean()) / botc['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - botc['adjPTS'].mean()) / botc['adjPTS'].std() 
                
        if df.iat[i,4] == 'D':
            num_d += 1
            if num_d <= 4:
                df.iat[i,33] = (df.iat[i,29] - topd['adj+/-'].mean()) / topd['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - topd['adjPTS'].mean()) / topd['adjPTS'].std()
            else:
                df.iat[i,33] = (df.iat[i,29] - botd['adj+/-'].mean()) / botd['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - botd['adjPTS'].mean()) / botd['adjPTS'].std() 
                
        if df.iat[i,4] in POSITION_LIST_WINGS:
            num_w += 1
            if num_w <= 2:
                df.iat[i,33] = (df.iat[i,29] - topw['adj+/-'].mean()) / topw['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - topw['adjPTS'].mean()) / topw['adjPTS'].std()
            elif num_w == 3 or num_w == 4:
                df.iat[i,33] = (df.iat[i,29] - lev2f['adj+/-'].mean()) / lev2f['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - lev2f['adjPTS'].mean()) / lev2f['adjPTS'].std()
            else:
                df.iat[i,33] = (df.iat[i,29] - botw['adj+/-'].mean()) / botw['adj+/-'].std()
                df.iat[i,34] = (df.iat[i,28] - botw['adjPTS'].mean()) / botw['adjPTS'].std()
        
            
        df.iat[i,35] = df.iat[i,33] + df.iat[i,34]    

    return df    

def team_processor(df, year, strategy):
    """ For each team, sorts and filters the team, and adds a column to indicate 
    a players status. 
    Strategy can have three different values:   
    1)  "any8" - protect any 8 skaters.  Means top 4 defensemen and top 4 forwards.
    2)  "split73" - use a 7 fwd and 3 def split. Choose top 3 defensemen and top 7 
        forwards.
    3)  "hybrid" - for each team it makes a decision as to which of the first two 
        methods to use. 
        
    Notes:  "any8" Selects four defensemen, and only four forwards so when this method 
            is used the resulting list of unprotected players will when sorted 
            by player strength have lots of forwards at the top. Resulting team will 
            be forward heavy.

            "split73" If this method is chosen more forwards will be protected so the
            resulting team will be defensemen heavy. """ 

    temp_df = None 
    # Add a column to indicate which players are being protected.
    df['Protect'] = 0
    # Load the nmc data and add it to the dataframe - only have this data for 2020
    if year == 2019:
        fname = "nmc" + str(year) + ".csv"
        df_nmc = pd.read_csv(fname,header=0, encoding='utf_16')
        nmc_players = list(df_nmc['Name'])
        for i in range(len(df)):
            if df.iat[i,0] in nmc_players:
                df.iat[i,14] = 1

    # Teams are supposed to leave unprotected two forwards and one defenseman
    # who played at least 40 games in current season or 70 games in current plus
    # previous season. This limit may not apply in 2020 due to coronavirus.
    # Turns out that 2012-2013 season was strike shortened (48 games). Need to
    # allow for that too.
    num_games = 40
    if year == 2019:
        num_games = 33    
    if year == 2012:
        num_games = 24

    #path = './' + str(year)
    for team in Teams:
        # These two lines and the 'path = ' line before the for statement are used below to write
        # team files out.  Used this to check that the processing was being dome correctly.
        #fname = 'unprotected2011.csv'
        #fname2 = 'protected' + team  + '.csv'        
        
        df2_myteam = df[df['Tm'] == team]         
                    
        df2_myteam.sort_values(by=['adjTOI'],axis=0,inplace=True, ascending=False)       
        
        df2_red_gp = df2_myteam[df2_myteam['GP'] > num_games]    
        # Too old - no point in protecting these players.
        df2_red_age2 = df2_red_gp[df2_red_gp['Age'] < 39]           

        # Determine whether to protect any eight skaters or 7 fwd and 3 def.   
        num_def_protected = 0

        if strategy == 'any8':
            num_def_protected = 4
        elif strategy == 'split73':
            num_def_protected = 3
        elif strategy == 'hybrid':
            def_tot_count = 0        
            for i in range(len(df2_red_age2)):
                if df2_red_age2.iat[i,3] == 'D':            
                    def_tot_count += 1
                    
            def_top8_count = 0
            for i in range(8):                
                if df2_red_age2.iat[i,3] == 'D':            
                    def_top8_count += 1
                    
            if def_top8_count <= 3:
                num_def_protected = 3       
            if def_top8_count > 4:
                num_def_protected = 4
            if def_top8_count == 4:
                if def_tot_count > 4:
                    num_def_protected = 4
                else:
                    num_def_protected = 3
        else:
            print("Invalid strategy.  Must use -any8- or -split73- or -hybrid-.")            
        
        # Protect defensemen            
        def_count = 0   
        for i in range(len(df2_red_age2)):
            if df2_red_age2.iat[i,3] == 'D':
                if not df2_red_age2.iat[i,14] == 1:               
                    df2_red_age2.iat[i,14] = 1
                def_count += 1
            if def_count == num_def_protected:
                break
                
        num_fwd_protected = 0        
        if num_def_protected == 3:
            num_fwd_protected = 7
        else:
            num_fwd_protected = 4
            
        # Protect forwards    
        fwd_count = 0    
        for i in range(len(df2_red_age2)):
            if not df2_red_age2.iat[i,3] == 'D':
                if not df2_red_age2.iat[i,14] == 1:
                    df2_red_age2.iat[i,14] = 1                
                fwd_count += 1
            if fwd_count == num_fwd_protected:
                break 
        
        # These next two lines are for writing our these files.  
        #dfx = df2_red_age2[df2_red_age2['Protect']==1]
        #dfx.to_csv(os.path.join(path,fname2), index = False)
        df3_myteam = df2_red_age2[df2_red_age2['Protect'] == 0]
        if temp_df is None:
            temp_df = df3_myteam
        else:
            temp_df = pd.concat([temp_df,df3_myteam])

    # The line below is for writing out these files to check that the processing works. 
    # temp_df.to_csv(os.path.join(path,fname), index=False) 
    return temp_df 

def team_selector_best_top_down(df):
    """ The function that chooses the team from the list of available players.  Starts at the top of the 
        player list and goes down, noting the team a chosen player plays for so that each team has only one 
        representative. The player list is sorted by Ztot which is a calculation of each 
        players strength. """        

    eg = df.sort_values(by=['Ztot'], ascending = False, axis=0)

    num_fwds = 0
    num_lws = 0
    num_rws = 0
    num_defs = 0
    num_ctrs = 0
    team_tracker = []
    max_fwds = 14
    max_defs = 9
    min_lws = 3
    min_rws = 3
    min_ctrs = 4
    max_players = 23
    num_players = 0
    min_lws_reached = False
    min_rws_reached = False
    min_ctrs_reached = False

    for i in range(len(eg)):
        tm = eg.iat[i,2]
        if not tm in team_tracker and num_players < max_players:
            pos = eg.iat[i,3]
            if not pos == 'D' and num_fwds < max_fwds:
                if pos == 'LW':
                    if min_lws_reached == True:
                        players_needed = 0
                        if min_rws_reached == False:
                            players_needed += (min_rws - num_rws)
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                
                    else:
                        # addit
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                
                if pos == 'RW':
                    if min_rws_reached == True:
                        players_needed = 0
                        if min_lws_reached == False:
                            players_needed += (min_lws - num_lws)
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                
                    else:
                        # addit
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
                            
                if pos == 'C':
                    if min_ctrs_reached == True:
                        players_needed = 0
                        if min_rws_reached == False:
                            players_needed += (min_rws - num_rws)
                        if min_lws_reached == False:
                            players_needed += (min_lws - num_lws)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_ctrs += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_ctrs >= min_ctrs:
                                min_ctrs_reached = True
                
                    else:
                        # addit
                        num_players += 1
                        num_ctrs += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_ctrs >= min_ctrs:
                            min_ctrs_reached = True

                if pos == 'W' or pos == 'F':
                    if min_lws_reached == True and min_rws_reached == True:
                        players_needed = 0
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed: 
                            # add it - but which position
                            if num_lws < num_rws:
                                # add as lw
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                            elif num_rws < num_lws:
                                # add as rw
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                            else:
                                # flip a coin
                                if np.random.rand() < 0.5:
                                    # add as lw
                                    num_players += 1
                                    num_lws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_lws >= min_lws:
                                        min_lws_reached = True
                                else:
                                    # add as rw
                                    num_players += 1
                                    num_rws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_rws >= min_rws:
                                        min_rws_reached = True
                    elif min_lws_reached == True and min_rws_reached == False:
                        # add as rw
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
                    elif nim_rws_reached == True and min_lws_reached == False:
                        # add as lw
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                    else:
                        # flip a coin
                        if np.random.rand() < 0.5:
                            # add as lw
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                        else:
                            # add as rw
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True 
                                
            else:    
                if pos == 'D' and num_defs < max_defs:
                    # add it
                    team_tracker.append(tm)
                    eg.iat[i,14] = 1
                    num_defs += 1
                    num_players += 1   

    _display_team(eg[eg['Protect']==1])
    
def team_selector_fwd_first(df):
    """ Selects a team by choosing the allotment of forwards first and then
    the defensemen. Searches through a list of unprotected players sorted by Ztot."""
    eg = df.sort_values(by=['Ztot'], ascending = False, axis=0)

    num_fwds = 0
    num_lws = 0
    num_rws = 0
    num_defs = 0
    num_ctrs = 0
    team_tracker = []
    max_fwds = 14
    max_defs = 9
    min_lws = 3
    min_rws = 3
    min_ctrs = 4
    max_players = 23
    num_players = 0
    min_lws_reached = False
    min_rws_reached = False
    min_ctrs_reached = False    

    for i in range(len(eg)):
        tm = eg.iat[i,2]
        if not tm in team_tracker and num_fwds < max_fwds:
            pos = eg.iat[i,3]
            if pos == 'LW':
                if min_lws_reached == True:
                    players_needed = 0
                    if min_rws_reached == False:
                        players_needed += (min_rws - num_rws)
                    if min_ctrs_reached == False:
                        players_needed += (min_ctrs - num_ctrs)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed:
                        #addit
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
            
                else:
                    # addit
                    num_players += 1
                    num_lws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_lws >= min_lws:
                        min_lws_reached = True
            
            if pos == 'RW':
                if min_rws_reached == True:
                    players_needed = 0
                    if min_lws_reached == False:
                        players_needed += (min_lws - num_lws)
                    if min_ctrs_reached == False:
                        players_needed += (min_ctrs - num_ctrs)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed:
                        #addit
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
            
                else:
                    # addit
                    num_players += 1
                    num_rws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_rws >= min_rws:
                        min_rws_reached = True
                        
            if pos == 'C':
                if min_ctrs_reached == True:
                    players_needed = 0
                    if min_rws_reached == False:
                        players_needed += (min_rws - num_rws)
                    if min_lws_reached == False:
                        players_needed += (min_lws - num_lws)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed:
                        #addit
                        num_players += 1
                        num_ctrs += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_ctrs >= min_ctrs:
                            min_ctrs_reached = True
            
                else:
                    # addit
                    num_players += 1
                    num_ctrs += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_ctrs >= min_ctrs:
                        min_ctrs_reached = True

            if pos == 'W' or pos == 'F':
                if min_lws_reached == True and min_rws_reached == True:
                    players_needed = 0
                    if min_ctrs_reached == False:
                        players_needed += (min_ctrs - num_ctrs)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed: 
                        # add it - but which position
                        if num_lws < num_rws:
                            # add as lw
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                        elif num_rws < num_lws:
                            # add as rw
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                        else:
                            # flip a coin
                            if np.random.rand() < 0.5:
                                # add as lw
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                            else:
                                # add as rw
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                elif min_lws_reached == True and min_rws_reached == False:
                    # add as rw
                    num_players += 1
                    num_rws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_rws >= min_rws:
                        min_rws_reached = True
                elif nim_rws_reached == True and min_lws_reached == False:
                    # add as lw
                    num_players += 1
                    num_lws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_lws >= min_lws:
                        min_lws_reached = True
                else:
                    # flip a coin
                    if np.random.rand() < 0.5:
                        # add as lw
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                    else:
                        # add as rw
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True             

    for i in range(len(eg)):
        tm = eg.iat[i,2]
        if not tm in team_tracker and num_defs < max_defs and eg.iat[i,3] == 'D':
            # add it
            team_tracker.append(tm)
            eg.iat[i,14] = 1
            num_defs += 1
            num_players += 1                               

    _display_team(eg[eg['Protect']==1])
    
def team_selector_def_first(df):
    """ Chooses a team by selecting the allotment of defensemen first and then the 
    allotment of forwards.  Searches through a list of players sorted by Ztot."""
    eg = df.sort_values(by=['Ztot'], ascending = False, axis=0)

    num_fwds = 0
    num_lws = 0
    num_rws = 0
    num_defs = 0
    num_ctrs = 0
    team_tracker = []
    max_fwds = 14
    max_defs = 9
    min_lws = 3
    min_rws = 3
    min_ctrs = 4
    max_players = 23
    num_players = 0
    min_lws_reached = False
    min_rws_reached = False
    min_ctrs_reached = False

    for i in range(len(eg)):
        tm = eg.iat[i,2]
        if not tm in team_tracker and num_defs < max_defs and eg.iat[i,3] == 'D':
            # add it
            team_tracker.append(tm)
            eg.iat[i,14] = 1
            num_defs += 1
            num_players += 1

    for i in range(len(eg)):
        tm = eg.iat[i,2]
        if not tm in team_tracker and num_fwds < max_fwds:
            pos = eg.iat[i,3]
            if pos == 'LW':
                if min_lws_reached == True:
                    players_needed = 0
                    if min_rws_reached == False:
                        players_needed += (min_rws - num_rws)
                    if min_ctrs_reached == False:
                        players_needed += (min_ctrs - num_ctrs)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed:
                        #addit
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
            
                else:
                    # addit
                    num_players += 1
                    num_lws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_lws >= min_lws:
                        min_lws_reached = True
            
            if pos == 'RW':
                if min_rws_reached == True:
                    players_needed = 0
                    if min_lws_reached == False:
                        players_needed += (min_lws - num_lws)
                    if min_ctrs_reached == False:
                        players_needed += (min_ctrs - num_ctrs)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed:
                        #addit
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
            
                else:
                    # addit
                    num_players += 1
                    num_rws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_rws >= min_rws:
                        min_rws_reached = True
                        
            if pos == 'C':
                if min_ctrs_reached == True:
                    players_needed = 0
                    if min_rws_reached == False:
                        players_needed += (min_rws - num_rws)
                    if min_lws_reached == False:
                        players_needed += (min_lws - num_lws)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed:
                        #addit
                        num_players += 1
                        num_ctrs += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_ctrs >= min_ctrs:
                            min_ctrs_reached = True
            
                else:
                    # addit
                    num_players += 1
                    num_ctrs += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_ctrs >= min_ctrs:
                        min_ctrs_reached = True   

            if pos == 'W' or pos == 'F':
                if min_lws_reached == True and min_rws_reached == True:
                    players_needed = 0
                    if min_ctrs_reached == False:
                        players_needed += (min_ctrs - num_ctrs)
                    num_fwds_needed = max_fwds - num_fwds
                    if players_needed < num_fwds_needed: 
                        # add it - but which position
                        if num_lws < num_rws:
                            # add as lw
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                        elif num_rws < num_lws:
                            # add as rw
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                        else:
                            # flip a coin
                            if np.random.rand() < 0.5:
                                # add as lw
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                            else:
                                # add as rw
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                elif min_lws_reached == True and min_rws_reached == False:
                    # add as rw
                    num_players += 1
                    num_rws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_rws >= min_rws:
                        min_rws_reached = True
                elif nim_rws_reached == True and min_lws_reached == False:
                    # add as lw
                    num_players += 1
                    num_lws += 1
                    num_fwds += 1
                    eg.iat[i,14] = 1
                    team_tracker.append(tm)
                    if num_lws >= min_lws:
                        min_lws_reached = True
                else:
                    # flip a coin
                    if np.random.rand() < 0.5:
                        # add as lw
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                    else:
                        # add as rw
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True                     

    _display_team(eg[eg['Protect']==1])


def team_selector_alternate(df):
    """ Selects a team by choosing nine defensemen and nine forwards, alternating
    between them.  Then picks five more forwards to round out the team."""
    eg = df.sort_values(by=['Ztot'],ascending=False, axis=0) 

    num_fwds = 0
    num_lws = 0
    num_rws = 0
    num_defs = 0
    num_ctrs = 0
    team_tracker = []
    max_fwds = 14
    max_defs = 9
    min_lws = 3
    min_rws = 3
    min_ctrs = 4
    max_players = 23
    num_players = 0
    min_lws_reached = False
    min_rws_reached = False
    min_ctrs_reached = False    

    for j in range(9):
        # Find a forward
        for i in range(len(eg)):
            tm = eg.iat[i,2]
            if not tm in team_tracker and not eg.iat[i,3] == 'D' and eg.iat[i,14] == 0:
                pos = eg.iat[i,3]
                if pos == 'LW':
                    if min_lws_reached == True:
                        players_needed = 0
                        if min_rws_reached == False:
                            players_needed += (min_rws - num_rws)
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                            break    
                
                    else:
                        # addit
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                        break    
                
                if pos == 'RW':
                    if min_rws_reached == True:
                        players_needed = 0
                        if min_lws_reached == False:
                            players_needed += (min_lws - num_lws)
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                            break    
                
                    else:
                        # addit
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
                        break    
                            
                if pos == 'C':
                    if min_ctrs_reached == True:
                        players_needed = 0
                        if min_rws_reached == False:
                            players_needed += (min_rws - num_rws)
                        if min_lws_reached == False:
                            players_needed += (min_lws - num_lws)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_ctrs += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_ctrs >= min_ctrs:
                                min_ctrs_reached = True
                            break    
                
                    else:
                        # addit
                        num_players += 1
                        num_ctrs += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_ctrs >= min_ctrs:
                            min_ctrs_reached = True
                        break       

                if pos == 'W' or pos == 'F':
                    if min_lws_reached == True and min_rws_reached == True:
                        players_needed = 0
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed: 
                            # add it - but which position
                            if num_lws < num_rws:
                                # add as lw
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                                break    
                            elif num_rws < num_lws:
                                # add as rw
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                                break    
                            else:
                                # flip a coin
                                if np.random.rand() < 0.5:
                                    # add as lw
                                    num_players += 1
                                    num_lws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_lws >= min_lws:
                                        min_lws_reached = True
                                    break    
                                else:
                                    # add as rw
                                    num_players += 1
                                    num_rws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_rws >= min_rws:
                                        min_rws_reached = True
                                    break    
                    elif min_lws_reached == True and min_rws_reached == False:
                        # add as rw
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
                        break    
                    elif nim_rws_reached == True and min_lws_reached == False:
                        # add as lw
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                        break    
                    else:
                        # flip a coin
                        if np.random.rand() < 0.5:
                            # add as lw
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                            break    
                        else:
                            # add as rw
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm) 
                            if num_rws >= min_rws:
                                min_rws_reached = True
                            break

        for i in range(len(eg)):
            # Find defenseman
            tm = eg.iat[i,2]
            if not tm in team_tracker and eg.iat[i,3] == 'D' and eg.iat[i,14] == 0:
                team_tracker.append(tm)
                eg.iat[i,14] = 1
                num_defs += 1
                num_players += 1   
                break                               

    for j in range(5):
        # Find five more forwards
        for i in range(len(eg)):
            tm = eg.iat[i,2]
            if not tm in team_tracker and not eg.iat[i,3] == 'D' and eg.iat[i,14] == 0:
                pos = eg.iat[i,3]
                if pos == 'LW':
                    if min_lws_reached == True:
                        players_needed = 0
                        if min_rws_reached == False:
                            players_needed += (min_rws - num_rws)
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                            break    
                
                    else:
                        # addit
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                        break    
                
                if pos == 'RW':
                    if min_rws_reached == True:
                        players_needed = 0
                        if min_lws_reached == False:
                            players_needed += (min_lws - num_lws)
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                            break    
                
                    else:
                        # addit
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
                        break    
                            
                if pos == 'C':
                    if min_ctrs_reached == True:
                        players_needed = 0
                        if min_rws_reached == False:
                            players_needed += (min_rws - num_rws)
                        if min_lws_reached == False:
                            players_needed += (min_lws - num_lws)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed:
                            #addit
                            num_players += 1
                            num_ctrs += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_ctrs >= min_ctrs:
                                min_ctrs_reached = True
                            break    
                
                    else:
                        # addit
                        num_players += 1
                        num_ctrs += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_ctrs >= min_ctrs:
                            min_ctrs_reached = True
                        break       

                if pos == 'W' or pos == 'F':
                    if min_lws_reached == True and min_rws_reached == True:
                        players_needed = 0
                        if min_ctrs_reached == False:
                            players_needed += (min_ctrs - num_ctrs)
                        num_fwds_needed = max_fwds - num_fwds
                        if players_needed < num_fwds_needed: 
                            # add it - but which position
                            if num_lws < num_rws:
                                # add as lw
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                                break    
                            elif num_rws < num_lws:
                                # add as rw
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                                break    
                            else:
                                # flip a coin
                                if np.random.rand() < 0.5:
                                    # add as lw
                                    num_players += 1
                                    num_lws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_lws >= min_lws:
                                        min_lws_reached = True
                                    break    
                                else:
                                    # add as rw
                                    num_players += 1
                                    num_rws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_rws >= min_rws:
                                        min_rws_reached = True
                                    break    
                    elif min_lws_reached == True and min_rws_reached == False:
                        # add as rw
                        num_players += 1
                        num_rws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_rws >= min_rws:
                            min_rws_reached = True
                        break    
                    elif nim_rws_reached == True and min_lws_reached == False:
                        # add as lw
                        num_players += 1
                        num_lws += 1
                        num_fwds += 1
                        eg.iat[i,14] = 1
                        team_tracker.append(tm)
                        if num_lws >= min_lws:
                            min_lws_reached = True
                        break    
                    else:
                        # flip a coin
                        if np.random.rand() < 0.5:
                            # add as lw
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                            break    
                        else:
                            # add as rw
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm) 
                            if num_rws >= min_rws:
                                min_rws_reached = True
                            break

    _display_team(eg[eg['Protect']==1])                        


def team_selector_by_team_strength(df):
    """ Picks players by reading a list of teams and choosing the best available 
    player for that team. """
        
    eg = df.sort_values(by=['Ztot'],ascending=False, axis=0)        

    num_fwds = 0
    num_lws = 0
    num_rws = 0
    num_defs = 0
    num_ctrs = 0
    team_tracker = []
    max_fwds = 14
    max_defs = 9
    min_lws = 3
    min_rws = 3
    min_ctrs = 4
    max_players = 23
    num_players = 0
    min_lws_reached = False
    min_rws_reached = False
    min_ctrs_reached = False    

    team_list = team_Strength    
    
    for j in range(len(team_list)):
        t = team_list.iat[j,0]
        for i in range(len(eg)):
            if t == eg.iat[i,2] and num_players < max_players:
                pos = eg.iat[i,3]
                if not pos == 'D' and num_fwds < max_fwds:
                    if pos == 'LW':
                        if min_lws_reached == True:
                            players_needed = 0
                            if min_rws_reached == False:
                                players_needed += (min_rws - num_rws)
                            if min_ctrs_reached == False:
                                players_needed += (min_ctrs - num_ctrs)
                            num_fwds_needed = max_fwds - num_fwds
                            if players_needed < num_fwds_needed:
                                #addit
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                #team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                                break    
                    
                        else:
                            # addit
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            #team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                            break    
                    
                    if pos == 'RW':
                        if min_rws_reached == True:
                            players_needed = 0
                            if min_lws_reached == False:
                                players_needed += (min_lws - num_lws)
                            if min_ctrs_reached == False:
                                players_needed += (min_ctrs - num_ctrs)
                            num_fwds_needed = max_fwds - num_fwds
                            if players_needed < num_fwds_needed:
                                #addit
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                #team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                                break    
                    
                        else:
                            # addit
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            #team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                            break    
                                
                    if pos == 'C':
                        if min_ctrs_reached == True:
                            players_needed = 0
                            if min_rws_reached == False:
                                players_needed += (min_rws - num_rws)
                            if min_lws_reached == False:
                                players_needed += (min_lws - num_lws)
                            num_fwds_needed = max_fwds - num_fwds
                            if players_needed < num_fwds_needed:
                                #addit
                                num_players += 1
                                num_ctrs += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                #team_tracker.append(tm)
                                if num_ctrs >= min_ctrs:
                                    min_ctrs_reached = True
                                break    
                    
                        else:
                            # addit
                            num_players += 1
                            num_ctrs += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            #team_tracker.append(tm)
                            if num_ctrs >= min_ctrs:
                                min_ctrs_reached = True
                            break   

                    if pos == 'W' or pos == 'F':
                        if min_lws_reached == True and min_rws_reached == True:
                            players_needed = 0
                            if min_ctrs_reached == False:
                                players_needed += (min_ctrs - num_ctrs)
                            num_fwds_needed = max_fwds - num_fwds
                            if players_needed < num_fwds_needed: 
                                # add it - but which position
                                if num_lws < num_rws:
                                    # add as lw
                                    num_players += 1
                                    num_lws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_lws >= min_lws:
                                        min_lws_reached = True
                                    break    
                                elif num_rws < num_lws:
                                    # add as rw
                                    num_players += 1
                                    num_rws += 1
                                    num_fwds += 1
                                    eg.iat[i,14] = 1
                                    team_tracker.append(tm)
                                    if num_rws >= min_rws:
                                        min_rws_reached = True
                                    break    
                                else:
                                    # flip a coin
                                    if np.random.rand() < 0.5:
                                        # add as lw
                                        num_players += 1
                                        num_lws += 1
                                        num_fwds += 1
                                        eg.iat[i,14] = 1
                                        team_tracker.append(tm)
                                        if num_lws >= min_lws:
                                            min_lws_reached = True
                                        break    
                                    else:
                                        # add as rw
                                        num_players += 1
                                        num_rws += 1
                                        num_fwds += 1
                                        eg.iat[i,14] = 1
                                        team_tracker.append(tm)
                                        if num_rws >= min_rws:
                                            min_rws_reached = True
                                        break    
                        elif min_lws_reached == True and min_rws_reached == False:
                            # add as rw
                            num_players += 1
                            num_rws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_rws >= min_rws:
                                min_rws_reached = True
                            break    
                        elif nim_rws_reached == True and min_lws_reached == False:
                            # add as lw
                            num_players += 1
                            num_lws += 1
                            num_fwds += 1
                            eg.iat[i,14] = 1
                            team_tracker.append(tm)
                            if num_lws >= min_lws:
                                min_lws_reached = True
                            break    
                        else:
                            # flip a coin
                            if np.random.rand() < 0.5:
                                # add as lw
                                num_players += 1
                                num_lws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_lws >= min_lws:
                                    min_lws_reached = True
                                break    
                            else:
                                # add as rw
                                num_players += 1
                                num_rws += 1
                                num_fwds += 1
                                eg.iat[i,14] = 1
                                team_tracker.append(tm)
                                if num_rws >= min_rws:
                                    min_rws_reached = True
                                break  
                    
                else:    
                    if pos == 'D' and num_defs < max_defs:
                        # add it
                        #team_tracker.append(tm)
                        eg.iat[i,14] = 1
                        num_defs += 1
                        num_players += 1
                        break

    _display_team(eg[eg['Protect']==1])                    
    

def _display_team(eg1):    
    print(eg1.iloc[:,[0,1,2,3,6,7,8,9,13]].round(2))
    print("Team is scored by the following stats: ")     
    print("+/-: Goal differential. One of many player stats.")
    print("PS: Player score:  An overall player evaluation stat provided by the NHL")
    print("Ztot: My own overall player evaluation stat.")        
    exp_team_tot = eg1['adj+/-'].sum()
    team_score = (exp_team_tot - team_Avg_PlusMinus) / team_Std_PlusMinus
    print("Team adj+/- score: {:.2f} standard deviations away from the adj+/- mean".format(team_score))  
    exp_team_tot = eg1['PS'].sum()
    team_score = (exp_team_tot - team_Avg_PS) / team_Std_PS
    print("Team PS score: {:.2f} standard deviations away from the PS mean".format(team_score))  
    exp_team_tot = eg1['Ztot'].sum()
    team_score = (exp_team_tot - team_Avg_Ztot) / team_Std_Ztot
    print("Team Ztot score: {:.2f} standard deviations away from the Ztot mean".format(team_score))  

def simulate_nhl_exp_draft(year, protect_method, pick_method):
    """ Controlling function.  Runs all of the others in order to simulate 
    an NHL expansion draft.
    Instructions:
       Need to pass four parameters:
       1)  Year:  The is the year of the expansion draft. 
           Ex: 2017 means the draft occurs after the 2016 2017 season
       2)  Protect_method:  The method by which the teams protect players.
           Use 'any8' - take any eight skaters.  Means top 4 def and top four fwds.
               'split73 - a 7 fwd 3 def split.  Means top 3 def and top 7 fwds.
               'hybrid' - a mixture of the first two.  Makes decision as to which
                          method to use for each team.
       3)  Pick method:  The method by which unprotected players are drafted.
           Use 'strength' - takes the best player for each team, where teams come from a 
                            list ordered by team strength.
               'topdown' -  reads from a list of unprotected players, ordered by
                            player strength.  Reads the list top down. 
               'deffirst' - Chooses defensemen first, then forwards. Reads the player
                            list top down.
               'fwdfirst' - Chooses the forwards first, then the defensemen.  Reads the
                            player list top down. 
               'alternate'- Chooses nine forwards and nine defensemen in alternating
                            fashion and then add the last five forwards.  """                                                      
        
    df = load_setup(year)
    df1 = calc_player_value(df) 
    calc_base_stats(df1)    
    df2 = calc_team_strength(df1, year)
    df3 = remove_first_second_years(df2,year)        
    df4 = reduce_vars(df3)  
    df5 = team_processor(df4, year, protect_method)  
    if pick_method == "strength":       
        team_selector_by_team_strength(df5)
    elif pick_method == "topdown":
        team_selector_best_top_down(df5)
    elif pick_method == "fwdfirst":
        team_selector_fwd_first(df5)
    elif pick_method == "deffirst":
        team_selector_def_first(df5)
    elif pick_method == "alternate":
        team_selector_alternate(df5)
    else:
        print("Invalid pick method. Need to use 'strength', 'topdown', 'fwdfirst' or 'deffirst'.") 


    








