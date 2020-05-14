4/21/2020   

Author:         Chris Idso
Project Name:   NHL Expansion Draft Simulator
Description:    An attempt to simulate the NHL expansion draft, the process by which
                a new team selects players from the other teams, using the rules set
                forth by the NHL. The idea being to get a feel for how strong the 
                resulting team would be compared to the rest of the league.  And to 
                learn as much as I could about hockey in the process.

Expansion in sports leagues usually (but not always) happens in pairs, for ease of 
scheduling, and for balance in divisions and conferences. And there is a sort of 
friendly competition between expansion teams to be the first to win a championship.

I am old enough to remember the expansion drafts of the Seahawks and the Mariners in
the mid 1970's when those teams joined their respective leagues. And I remember just
how bad both teams were. The Mariners won one game out of every three in their first
year, and the Seahawks won two games in their first season. 

The Mariners remained a bad team for years, and could only watch as their sister
expansion team, the Toronto Blue Jays, improved and eventually won two world series 
in the early 1990's. The Mariners still have not been to the World Series.

The Seahawks fared somewhat better, winning nine games in their third year, and
finally winning the superbowl in 2014.  Their sister expansion team, the Tampa Bay
Buccaneers, didn't win a game until late in their second year, but won a superbowl
before the Seahwks did, in the early 2000's.

For Seattle sports fans, there will be another expansion draft in 2021 when Seattle's 
team (to be named later) joins the NHL and starts playing. Our sister expansion team
is already in the league. They are called the Vegas Golden Knights and they joined 
the leage NHL in 2017. They did so well in their expansion draft and in their first 
entry draft that they made a run at the championship (Stanley Cup) in their first year
but ultimately fell just short.

So, how did they do so well? I was curious about this, because if they could do 
so well then perhaps Seattle's team could do just as well. Fortunately, information 
about this was available on-line, where I could look up the NHL expansion draft rules 
and find a list of transactions made by the Knights related to their expansion draft
and the entry draft that followed.

It seems there were two main reasons for their success. One was the rules for the 
expansion draft, which do not let a team protect as many players as they would
like, which leaves quite a few good players on the table. The other was the trades
they were able to make, which allowed them to acquire more draft picks 
(some in the first round).  

Trade Ex:  
Golden Knights to one of the existing teams: We see that you left a couple of 
good players out there (A and B). We know you want to keep player A, so how much
would you give us to take player B instead of player A?

I also found that the NHL had changed the expansion draft rules, and the existing 
teams may not have been properly prepared, or did not realize the impact the 
changes would have.

So with this information in the back of my mind I began designing an expansion draft
simulator. I was determined to incorporate as many of the expansion draft rules as
possible. There would need to be a way to calculate the relative strength of the 
teams in the NHL, as well as a way to calculate how good a player is (something the 
NHL has trying to do for some time with varying degrees of success). There would also 
need to be a way to decide which players to protect, and a method for selecting and 
grading the expansion team. 

Other considerations include players exempt from draft, teams exempt from the 
draft, players playing too few games to be protected or selected, and players too 
old (38, 39, 40+ years old). I did not consider goalies in this project.

Along the way I tried to put myself in the shoes of a general manager, deciding which
players to protect, and in the mind of Seattle's general manager, deciding which 
players to take.  

The data for this project was available on line at NHL Reference.  You just find the 
data you want (in the form of a big table) and convert it to text, and then copy it
into a spreadsheet and save it to a csv file.  Then it loads easily into a dataframe.

I was able to get data for skaters for the years 2011 to 2019. And data on player
debuts from 2010 to 2019. I also found data on-line for players in 2019-2020 who had a 
No Movement Clause (NMC) in their contract. This has been added too (but only for 2019-2020) because NMC's are addressed in the NHL's expansion draft rules.

Here are the Expansion Draft rules:
1) Expansion team can take only one player from any given team.  
2) Expansion team must take 14 forwards and 9 defensemen and 3 goalies.
3) A team can protect a) any 8 skaters or b) 7 forwards and 3 defensemen.
4) A team has to leave 2 forwards and 1 defensemen unprotected who played
   at least 40 games in the current season or 70 games in the last two seasons. 
5) Players with NMC's must be protected and count against the abovementioned 
   limits.  Players with NMC's can waive that clause.
6) Players in their first or second year are exempt from the expansion draft. 
7) When Seattle drafts in 2021 the Vegas Golden Knights will be exempt.   

And some interesting hockey info:
1) Useful player stats include TOI (time on ice in minutes), +/- (goal differential)
   and PTS (Points - goals + assists)
2) The stats in (1) above do not make sense at first.  Ex: A player can record many 
   points, and play lots of minutes, and all or most of the 82 games in a season,
   but still have a negative +/-.
3) A team is allowed to suit up 20 players for a game.  They usually go with 
   12 forwards, 6 defensemen, and 2 goalies.
4) Average shift time for a player is in the neighborhood of 40 seconds, but this
   varies. Different for players on the ice during a powerplay or when killing a 
   penalty. And different for best players on the team than for other players.
   Also different for defensemen (longer shifts) than for forwards (slightly shorter
   shifts) - due to defensemen not having to skate as hard.
5) Hockey teams can expand their rosters late in the season, just as baseball teams
   can.   
6) Some players are on the ice when the team is shorthanded, team is on powerplay, and
   when teams are at even strength.  
7) Some players are on the ice when the team is on powerplay, when teams are at even
   strength, and not when the team is shorthanded.
8) Some players are on the ice only when teams are at even strength. 

As you might expect the last four items in the list above make the problem of
evaluating players difficult, since it seems unlikely that there is one formula
that could be applied to all forwards and defensemen, and would involve all three
of the abovementioned player stats.

This proved to be the biggest challenge in this project. Other challenges include
how to handle trades (more than one line in the data for traded player), handling of a changing position list in the data, a strike-shortened season (2012), and a season shortened by coronavirus (2019).     

My finished project consists of a series of functions:

1) load_setup(year)   -   Takes the year (2011 - 2019) and adds some variables,
    does some cleanup (trades) and removes players who played <=20 games during 
    the season.  These players are probably callups late in the season and can have
    weird stats. 
2) calc_base_stats - Sums the +/- stats for the players on each team and calculates
    the mean and std over all the teams. Does this with the PS stat and the Ztot stat too.  Uses this later to evaluate the results of the draft.
3) calc_player_value - evaluates the players using their +/- and PTS stats. Score for
    each player is recorded in the Ztot variable.  Ztot = Z-score(+/-) + Z-score(PTS) 
    for each player.
4) calc_team_strength - Calculates team strength and stores it in a dataframe for
    later reference when drafting a team.
5) remove_first_second_years - Removes first and second year players, since they are
    exempt from the draft. Thought they should remain in the data during calculations.
6) reduce_vars - Reduces the variable list to only those variables that are needed from
    this point on.  
7) team_processor - For each team decides which players to protect and then creates a
    dataframe with the unprotected players.
8) team_selector_by_team_strength - Selects a team by reading from the team_strength
    list which is ordered by team strength. For each team selects best available player from the unprotected players list.    
9) team_selector_best_top_down - Reads the unprotected players list from the top down
    and selects the best players, tracking the teams the players play for to keep only one player from any given team.
10) team_selector_fwd_first - Reads the unprotected players list from the top down
     and selects all the forwards first and then all the defensemen.  
11) team_selector_def_first - Reads the unprotected players list from the top down
     and selects all the defensemen first and then all the forwards.
12) team_selector_alternate - Reads the unprotected player list and selects nine
     forwards and nine defensemen in alternating fashion, then adds five more forwards to round out the team.     
    
   NOTE: For each of the team-selecting functions the unprotected player list gets
    sorted by Ztot. When the team-selecting functions run they produce a list of
    the players selected. At the end of the list (you might need to scroll down a 
    little) they write out three versions of the team score. One uses the sum of the players' +/- stats, one uses the PS stat, and one uses my own Ztot stat, all of which are evaluated using the team stats calculated by the calc_base_stats function, to determine how many standard deviations away from the 
    mean the score is. 

13) simulate_nhl_exp_draft - One function to control them all. So you only have to 
     call one function.   

Also included in this project, are some juypter notebooks. One (project_demo) has the 
functions above in it so you can run them. Another one (project_walkthrough) has some
code I wrote as I was working on this project. It will run too, and will give you an 
idea of what this project does, and of the problems I faced, how I dealt with them, and 
of my thoughts as I worked on this.

There is work that still could be done on this project. I may need to find a way to correct the player evaluations for the strength of the team they play for. And I might be able to add age constraints for players protected or for players selected.  

Ex:  Only protect players who are 35 years old or younger, or maybe 25 years old
or older. Or only select players between 25 and 30 years old.

I have run this simulator many times now, and it looks like the results (+/-) are mostly
in a range between 1.2 and about 1.8. So it looks like our team will be pretty good.
I expect the other teams in the league will be more prepared for this expansion draft
than they were for the last one (in 2017) so we probably will not do quite as well
as the Knights did.

When Seattle's team joins the league we will be in the same division (Pacific) as the
Knights, so there should be some really good games between Seattle and Vegas!!! 

If you have any questions for me, or ideas on how this project might be improved, you
can send me an email at ci_walk99@yahoo.com.  

Cheers!   



 
