import streamlit as st
import requests
import pandas as pd
import mysql.connector

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", ["Home", "LiveScore", "Player Information","SQL Analytics","CRUD Operation"])

if page == "Home":
    st.markdown("<h1 style='text-align: center; color: red;'> Welcome to Cricbuzz</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: green;'>🏏 Cricket Dashboard</h2>",unsafe_allow_html=True)
    st.image("D:\Prabu\cricket_buzz_image.jpeg")
    #Live Score block
elif page == "LiveScore":
    st.title("🏏 Match Center")
    match_type = st.radio("Select Match Type", ["Live", "Recent"])

    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live" if match_type == "Live" else "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/recent"
    headers = {
        "x-rapidapi-key": "af06ca3954mshac617103945081ap11717ejsn97324ff1b680",
        "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    match_list = []

    if response.status_code == 200:
        data = response.json()

        for type_match in data.get("typeMatches", []):
            for series_matches in type_match.get("seriesMatches", []):
                series_data = series_matches.get("seriesAdWrapper", {})
                series_id = series_data.get("seriesId")
                series_name = series_data.get("seriesName")

                for match in series_data.get("matches", []):
                    info = match.get("matchInfo", {})
                    match_id = info.get("matchId")
                    match_desc = info.get("matchDesc")
                    match_format = info.get("matchFormat")
                    start_date = info.get("startDate")
                    status = info.get("status")
                    team1 = info.get("team1", {}).get("teamName")
                    team2 = info.get("team2", {}).get("teamName")
                    venue = f"{info.get('venueInfo', {}).get('ground')}, {info.get('venueInfo', {}).get('city')}"

                    score = match.get("matchScore", {})
                    team1_innings = score.get("team1Score", {}).get("inngs1", {})
                    team2_innings = score.get("team2Score", {}).get("inngs1", {})

                    match_list.append({
                        "series_id": series_id,
                        "series_name": series_name,
                        "match_id": match_id,
                        "match_desc": match_desc,
                        "match_format": match_format,
                        "start_date": start_date,
                        "status": status,
                        "team1": team1,
                        "team2": team2,
                        "venue": venue,
                        "team1_runs": team1_innings.get("runs", 0),
                        "team1_wickets": team1_innings.get("wickets", 0),
                        "team1_overs": team1_innings.get("overs", 0),
                        "team2_runs": team2_innings.get("runs", 0),
                        "team2_wickets": team2_innings.get("wickets", 0),
                        "team2_overs": team2_innings.get("overs", 0)
                    })

        teams = sorted(set([m["team1"] for m in match_list] + [m["team2"] for m in match_list]))
        series_names = sorted(set([m["series_name"] for m in match_list]))

        selected_team = st.selectbox("Filter by Team", ["All"] + teams)
        selected_series = st.selectbox("Filter by Series", ["All"] + series_names)

        filtered_matches = match_list
        if selected_team != "All":
            filtered_matches = [m for m in filtered_matches if selected_team in (m["team1"], m["team2"])]
        if selected_series != "All":
            filtered_matches = [m for m in filtered_matches if m["series_name"] == selected_series]

        df = pd.DataFrame(filtered_matches)

        st.subheader(f"📋 {match_type} Match Summary")
        if not df.empty:
            st.dataframe(df)
            # select match id for scorecard
            match_id = st.selectbox("Select Match ID for Scorecard", df["match_id"].unique())
            # button to fetch scorecard
            if st.button("Get Scorecard"):
                scorecard_url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"
                scorecard_response = requests.get(scorecard_url, headers=headers)
                if scorecard_response.status_code == 200:
                    match_score_card = scorecard_response.json()

                    for innings in match_score_card.get('scorecard', []):
                        innings_id = innings.get('inningsid', 'Unknown Innings')
                        team_name = innings.get('team', {}).get('teamName', f"Innings {innings_id}")
                        score = innings.get('score')
                        extras = innings.get('extras')
                        extra_total = extras.get('total', 0)
                        overs = innings.get('overs')
                        wickets = innings.get('wickets')
                        team_name = innings.get('batteamname', f"Innings {innings_id}")

                        with st.expander(f"🏏 Innings {innings_id}", expanded=True):
                            st.subheader(f"Team: {team_name} | Score: {score} | Extras: {extra_total} | Overs: {overs} | Wickets: {wickets}")

                            # Batting Stats
                            batting_list = []
                            for batting in innings.get('batsman', []):
                                batting_list.append({
                                    "Player": batting.get('name', 'Unknown'),
                                    "Runs": batting.get('runs', 0),
                                    "Balls": batting.get('balls', 0),
                                    "Fours": batting.get('fours', 0),
                                    "Sixes": batting.get('sixes', 0),
                                    "Strike Rate": batting.get('strkrate', 0.0),
                                    "Dismissal": batting.get('outdec', 'Not Out')
                                })

                            batting_df = pd.DataFrame(batting_list)
                            st.subheader("Batting Scorecard")
                            st.dataframe(batting_df)

                            # Bowling Stats
                            bowling_list = []
                            for bowler in innings.get('bowler', []):
                                bowling_list.append({
                                    "Bowler": bowler.get('name', 'Unknown'),
                                    "Overs": bowler.get('overs', 0),
                                    "Maidens": bowler.get('maidens', 0),
                                    "Runs Conceded": bowler.get('runs', 0),
                                    "Wickets": bowler.get('wickets', 0),
                                    "Economy": bowler.get('econ', 0.0)
                                })

                            bowling_df = pd.DataFrame(bowling_list)
                            st.subheader("Bowling Scorecard")
                            st.dataframe(bowling_df)
                else:
                    st.error("Failed to fetch scorecard data.")
        else:
            st.info(f"No {match_type.lower()} matches found for the selected filters.")
    else:
        st.error(f"Failed to fetch {match_type.lower()} match data.")
elif page == "Player Information":
    st.write("Player information updates will appear here.")
    st.title("🔍 Player Search")

    # Input field for player name
    player_name = st.text_input("Enter Player Name")

    if player_name:
        url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
        querystring = {"plrN": player_name}
        headers = {
            "x-rapidapi-key": "af06ca3954mshac617103945081ap11717ejsn97324ff1b680",
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code == 200:
            data = response.json()
            players = data.get('player', [])
            player_info = []

            if players:
                st.subheader("🎯 Search Results")
                for player in players:
                    name = player.get('name', 'Unknown')
                    player_id = player.get('id', 'N/A')
                    player_info.append((name, player_id))

                player_dict = {name: pid for name, pid in player_info}
                selected_name = st.selectbox("Select a Player", list(player_dict.keys()))
                selected_id = player_dict[selected_name]
                st.write(f"Selected Player ID: {selected_id}")

                # Fetch detailed stats
                stats_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{selected_id}"
                stats_response = requests.get(stats_url, headers=headers)

                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    st.subheader(f"📊 Career Stats for {selected_name}")

                    # Extract key profile info
                    profile_name = stats_data.get('name', 'Unknown')
                    nick_name = stats_data.get('nickName', 'Unknown')
                    country = stats_data.get('intlTeam', 'Unknown')
                    role = stats_data.get('role', 'Unknown')
                    batting_style = stats_data.get('bat', 'Unknown')
                    bowling_style = stats_data.get('bowl', 'Unknown')
                    dob = stats_data.get('DoB', 'Unknown')
                    birth_place = stats_data.get('birthPlace', 'Unknown')
                    height = stats_data.get('height', 'Unknown')
                    rankings = stats_data.get('rankings', {})
                    batting_rank = rankings.get('bat', {})
                    test_rank = batting_rank.get('testBestRank', 'N/A')
                    odi_rank = batting_rank.get('odiBestRank', 'N/A')
                    t20_rank = batting_rank.get('t20BestRank', 'N/A')
                    bowling_rank = rankings.get('bowl', {})
                    test_bowl_rank = bowling_rank.get('testBestRank', 'N/A')
                    odi_bowl_rank = bowling_rank.get('odiBestRank', 'N/A')
                    t20_bowl_rank = bowling_rank.get('t20BestRank', 'N/A')

                    with st.expander("📋 Player Profile", expanded=True):
                        st.markdown(f"### 🏏 {profile_name}")
                        st.markdown(f"**Nick Name:** {nick_name}")
                        st.markdown(f"**Country:** {country}")
                        st.markdown(f"**Role:** {role}")
                        st.markdown(f"**Batting Style:** {batting_style}")
                        st.markdown(f"**Bowling Style:** {bowling_style}")
                        st.markdown(f"**Date of Birth:** {dob}")
                        st.markdown(f"**Birthplace:** {birth_place}")
                        st.markdown(f"**Height:** {height}")
                        st.markdown(f"**Batting Ranks:** Test: {test_rank}, ODI: {odi_rank}, T20: {t20_rank}")
                        st.markdown(f"**Bowling Ranks:** Test: {test_bowl_rank}, ODI: {odi_bowl_rank}, T20: {t20_bowl_rank}")

                    # Fetch batting details
                    batting_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{selected_id}/batting"
                    batting_response = requests.get(batting_url, headers=headers)

                    if batting_response.status_code == 200:
                        batting_data = batting_response.json()
                        bat_headers = batting_data.get('headers', [])[1:]  # Skip 'ROWHEADER'
                        bat_values = batting_data.get('values', [])

                        bat_stats = {}
                        for i, fmt in enumerate(bat_headers):
                            bat_stats[fmt] = {}
                            for stat in bat_values:
                                stat_name = stat['values'][0]
                                stat_value = stat['values'][i + 1]
                                bat_stats[fmt][stat_name] = stat_value

                        bat_df = pd.DataFrame(bat_stats)

                        with st.expander("📈 Batting Career Summary", expanded=False):
                            st.dataframe(bat_df)
                    else:
                        st.error("Failed to fetch batting details.")

                    # Fetch bowling details
                    bowling_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{selected_id}/bowling"
                    bowling_response = requests.get(bowling_url, headers=headers)

                    if bowling_response.status_code == 200:
                        bowling_data = bowling_response.json()
                        bowl_headers = bowling_data.get('headers', [])[1:]  # Skip 'ROWHEADER'
                        bowl_values = bowling_data.get('values', [])

                        bowl_stats = {}
                        for i, fmt in enumerate(bowl_headers):
                            bowl_stats[fmt] = {}
                            for stat in bowl_values:
                                stat_name = stat['values'][0]
                                stat_value = stat['values'][i + 1]
                                bowl_stats[fmt][stat_name] = stat_value

                        bowl_df = pd.DataFrame(bowl_stats)

                        with st.expander("🎳 Bowling Career Summary", expanded=False):
                            st.dataframe(bowl_df)
                    else:
                        st.error("Failed to fetch bowling details.")
                else:
                    st.error("Failed to fetch detailed player stats.")
            else:
                st.info("No players found with that name.")
        else:
            st.error("Failed to fetch player data.")
elif page == "SQL Analytics":
    st.title("SQL Analytics")
    st.write("Run and visualize SQL queries here.")
    # Connect to MySQL
    import mysql.connector
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Welcome*1",
        database="cricbuzz"
    )
    cursor = conn.cursor()

   # Define question groups
    simple_questions = [
    "Question 1 : Find all players who represent India",
    "Question 2 : Show all cricket matches that were played in the last Few days",
    "Question 3 : List the top 10 highest run scorers in ODI cricket.",
    "Question 4 : Display all cricket venues that have a seating capacity of more than 30,000 ",
    "Question 5 : Calculate how many matches each team has won",
    "Question 6 : Count how many players belong to each playing role",
    "Question 7 : Find the highest individual batting score achieved in each cricket format",
    "Question 8 : Show all cricket series that started in the year 2024"
]

    medium_questions = [
    "Question 9 : Find all-rounder players who have scored more than 1000 runs AND taken more than 50 wickets in their career",
    "Question 10 : Get details of the last 20 completed matches.",
    "Question 11 : Compare each player's performance across different cricket formats. For players who have played at least 2 different formats",
    "Question 12 : Analyze each international team's performance when playing at home versus playing away",
    "Question 13 : Identify batting partnerships where two consecutive batsmen (batting positions next to each other) scored a combined total of 100 or more runs in the same innings.",
    "Question 14 : Examine bowling performance at different venues. For bowlers who have played at least 3 matches at the same venue, calculate their average economy rate, total wickets taken, and number of matches played at each venue.",
    "Question 15 : Identify players who perform exceptionally well in close matches. A close match is defined as one decided by less than 50 runs OR less than 5 wickets.",
    "Question 16 : Track how players' batting performance changes over different years. For matches since 2020, show each player's average runs per match and average strike rate for each year."
]

    complex_questions = [
    "Question 17 : Investigate whether winning the toss gives teams an advantage in winning matches. Calculate what percentage of matches are won by the team that wins the toss, broken down by their toss decision (choosing to bat first or bowl first).",
    "Question 18 : Find the most economical bowlers in limited-overs cricket (ODI and T20 formats).",
    "Question 19 : Determine which batsmen are most consistent in their scoring. Calculate the average runs scored and the standard deviation of runs for each player.",
    "Question 20 : Analyze how many matches each player has played in different cricket formats and their batting average in each format.",
    "Question 21 : Create a comprehensive performance ranking system for players. Combine their batting performance (runs scored, batting average, strike rate), bowling performance (wickets taken, bowling average, economy rate), and fielding performance (catches, stumpings) into a single weighted score",
    "Question 22 : Build a head-to-head match prediction analysis between teams. For each pair of teams that have played at least 5 matches against each other in the last 3 years",
    "Question 23 : Analyze recent player form and momentum. For each player's last 10 batting performances",
    "Question 24 : Study successful batting partnerships to identify the best player combinations.",
    "Question 25 : Perform a time-series analysis of player performance evolution. Track how each player's batting performance changes over time by"
]
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Simple", "Medium", "Complex"])

# Simple Tab
    with tab1:
        simple_selection = st.selectbox("Choose a simple query", simple_questions)
        if st.button("Execute Simple"):
            if simple_selection == simple_questions[0]:
                cursor.execute("""
                SELECT player_name, category AS 'Playing Role', batting_style, bowling_style
                FROM team_players_updated
                WHERE team_id = 2;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Player Name', 'Playing Role', 'Batting Style', 'Bowling Style'])
                st.dataframe(df)

            elif simple_selection == simple_questions[1]:
                cursor.execute("""
                SELECT match_desc AS 'Match Description',
                       team1_name AS 'Team 1',
                       team2_name AS 'Team 2',
                       CONCAT(venue_ground, ', ', venue_city) AS 'Venue',
                       DATE(start_date) AS 'Match Date'
                FROM recent_matches
                WHERE start_date >= NOW() - INTERVAL 15 DAY
                ORDER BY start_date DESC;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Match Description', 'Team 1', 'Team 2', 'Venue', 'Match Date'])
                st.dataframe(df)

            elif simple_selection == simple_questions[2]:
                cursor.execute("""
                SELECT tp.player_name AS 'Player Name',
                       pbs.runs AS 'Total Runs',
                       pbs.average AS 'Batting Average',
                       pbs.hundreds AS 'Centuries'
                FROM player_batting_stats pbs
                JOIN team_players tp ON pbs.player_id = tp.player_id
                WHERE pbs.format = 'ODI'
                ORDER BY CAST(pbs.runs AS UNSIGNED) DESC
                LIMIT 10;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Player Name', 'Total Runs', 'Batting Average', 'Centuries'])
                st.dataframe(df)

            elif simple_selection == simple_questions[3]:
                cursor.execute("""
                SELECT name AS 'Venue Name',
                       city AS 'City',
                       country AS 'Country',
                       capacity AS 'Capacity'
                FROM venue_details
                WHERE CAST(capacity AS UNSIGNED) > 30000
                ORDER BY CAST(capacity AS UNSIGNED) DESC;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Venue Name', 'City', 'Country', 'Capacity'])
                st.dataframe(df)

            elif simple_selection == simple_questions[4]:
                cursor.execute("""
                SELECT winner AS team_name,
                       COUNT(DISTINCT match_id) AS total_wins
                FROM match_scorecards
                WHERE winner IS NOT NULL
                GROUP BY winner
                ORDER BY total_wins DESC;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Team', 'Matches Won'])
                st.dataframe(df)

            elif simple_selection == simple_questions[5]:
                cursor.execute("""
                SELECT category AS playing_role,
                       COUNT(*) AS player_count
                FROM team_players_updated
                GROUP BY category
                ORDER BY player_count DESC;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Playing Role', 'Player Count'])
                st.dataframe(df)

            elif simple_selection == simple_questions[6]:
                cursor.execute("""
                SELECT format,
                       MAX(highest) AS highest_score
                FROM player_batting_stats_updated
                WHERE format IN ('Test', 'ODI', 'T20', 'IPL')
                GROUP BY format;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Format', 'Highest Score'])
                st.dataframe(df)

            elif simple_selection == simple_questions[7]:
                cursor.execute("""
                SELECT series_name,
                       match_format,
                       venue_city,
                       COUNT(series_name) AS total_matches
                FROM match_details
                WHERE YEAR(start_date) = 2024
                GROUP BY series_name, match_format, venue_city
                ORDER BY total_matches DESC;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Series Name', 'Match Format', 'Venue City', 'Total Matches'])
                st.dataframe(df)

# Medium Tab
    with tab2:
        medium_selection = st.selectbox("Choose a medium query", medium_questions)
        if st.button("Execute Medium"):
            if medium_selection == medium_questions[0]:
                cursor.execute("""
                SELECT PLAYER_NAME, B.FORMAT, SUM(B.RUNS), SUM(C.WICKETS)
                FROM team_players_updated A
                JOIN player_batting_stats_updated B ON A.player_id = B.player_id
                JOIN player_bowling_stats C ON A.player_id = C.player_id
                WHERE category = 'ALL ROUNDER'
                  AND B.RUNS > 1000
                  AND C.WICKETS > 50
                GROUP BY PLAYER_NAME, B.FORMAT;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Player Name', 'Format', 'Total Runs', 'Total Wickets'])
                st.dataframe(df)

            elif medium_selection == medium_questions[1]:
                cursor.execute("""
                SELECT  
                    match_desc,team1_name,team2_name,state_title,status,                      
                CASE 
                    WHEN status LIKE '%won by%run%' THEN 'Runs'
                    WHEN status LIKE '%won by%wkt%' THEN 'Wickets'
                ELSE 'Tied'                
                END AS victory_type,
                CONCAT(venue_ground, ', ', venue_city)
                FROM  recent_matches  
                order by end_date desc limit 20;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Match Description', 'Team 1', 'Team 2', 'Winning Team', 'Victory Margin','Vitory Type','Venue'])
                st.dataframe(df)

            elif medium_selection == medium_questions[2]:
                cursor.execute("""
                SELECT 
                    pp.name,
                    pbs.player_id,
                    SUM(CASE WHEN pbs.format = 'Test' THEN pbs.runs ELSE 0 END) AS test_runs,
                    SUM(CASE WHEN pbs.format = 'ODI' THEN pbs.runs ELSE 0 END) AS odi_runs,
                    SUM(CASE WHEN pbs.format = 'T20' THEN pbs.runs ELSE 0 END) AS t20_runs,
                    ROUND(SUM(pbs.runs) / SUM(pbs.innings), 2) AS overall_batting_average
                FROM 
                    player_batting_stats_updated pbs
                JOIN 
                    player_profiles pp ON pbs.player_id = pp.player_id
                WHERE 
                    pbs.format IN ('Test', 'ODI', 'T20')
                GROUP BY 
                    pbs.player_id, pp.name
                HAVING 
                    COUNT(DISTINCT pbs.format) >= 2;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Player Name','Player ID', 'Test', 'ODI','T20', 'Batting Average'])
                st.dataframe(df)
            elif medium_selection == medium_questions[3]:
                cursor.execute ( """
                SELECT 
                    winning_team.team_name,
                CASE 
                    WHEN tp.country_name = vd.country THEN 'Home'
                ELSE 'Away'
                END AS match_location,
                COUNT(*) AS wins
                FROM (
                SELECT 
                    match_id,
                CASE 
		            WHEN LOWER(match_status) LIKE CONCAT('%', LOWER(team1_name), ' won%') THEN team1_name
                    WHEN LOWER(match_status) LIKE CONCAT('%', LOWER(team2_name), ' won%') THEN team2_name
                END AS team_name,
                    venue_ground,
                    venue_city
                FROM 
                    team_result_details
                WHERE 
                    lower(match_status) LIKE '% won%'
                    ) AS winning_team
                JOIN 
                    international_teams tp ON winning_team.team_name = tp.team_name
                JOIN 
                    venue_details vd ON winning_team.venue_ground = vd.name AND winning_team.venue_city = vd.city
                GROUP BY 
                    winning_team.team_name, match_location
                ORDER BY 
                    winning_team.team_name, match_location;    
                            """)
                df = pd.DataFrame(cursor.fetchall(), columns=['Team Name','Match Location', 'Total Win'])
                st.dataframe(df)
            elif medium_selection == medium_questions[4]:
                cursor.execute ( """
                SELECT 
                    t1.match_id, 
                    t1.inningsid,
                    t1.player_name AS batsman1,
                    t2.player_name AS batsman2,
                    p.total_runs
                FROM batting_sequence t1
                JOIN batting_sequence t2
                    ON t1.inningsid = t2.inningsid
                AND t1.batting_sequence + 1 = t2.batting_sequence
                JOIN scorecard_match_partnership p
                ON p.inningsid = t1.inningsid
                and p.match_id = t1.match_id
                and p.match_id = t2.match_id
                AND (
                    (p.player1_id = t1.player_id AND p.player2_id = t2.player_id) OR
                    (p.player1_id = t2.player_id AND p.player2_id = t1.player_id)
                    )
                WHERE p.total_runs > 100;""")
                df = pd.DataFrame(cursor.fetchall(), columns = ['Match ID',"InningsId","Batsman 1","Batsman 2","Total Runs"]) 
                st.dataframe(df)
            elif medium_selection == medium_questions[5]:
                cursor.execute("""
                SELECT 
                    b.player_id,
                    b.player_name,
                    m.venue_city,
                    COUNT(*) AS matches_played,
                    SUM(b.wickets) AS total_wickets,
                    ROUND(AVG(CAST(b.economy AS DECIMAL(5,2))), 2) AS avg_economy
                FROM scorecard_match_bowling b
                JOIN match_details m ON b.match_id = m.match_id
                WHERE 
                    CAST(SUBSTRING_INDEX(b.overs, '.', 1) AS UNSIGNED) >= 4
                    GROUP BY b.player_id, b.player_name, m.venue_city
                    HAVING COUNT(*) >= 3;   
                           """) 
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Venue","Match Played","Total Wickets","Average Economy"]) 
                st.dataframe(df)
            elif medium_selection == medium_questions[6]:
                cursor.execute("""
                SELECT 
                    b.player_id,
                    b.player_name,
                    COUNT(*) AS close_matches_played,
                    ROUND(AVG(b.runs), 2) AS avg_runs_in_close_matches,
                SUM(CASE 
                    WHEN b.batting_teamname = SUBSTRING_INDEX(m.status, ' won by', 1) THEN 1 
                    ELSE 0 
                    END) AS matches_won_by_team
                FROM scorecard_match_batsmen b
                JOIN match_details m ON b.match_id = m.match_id
                WHERE (
                    (m.status LIKE '%won by % run%' AND CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(m.status, ' run', 1), 'won by ', -1) AS UNSIGNED) < 50)
                OR
                    (m.status LIKE '%won by % wkt%' AND CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(m.status, ' wkt', 1), 'won by ', -1) AS UNSIGNED) < 5)
                    )
                GROUP BY b.player_id, b.player_name
                HAVING COUNT(*) >= 1
                ORDER BY avg_runs_in_close_matches DESC;
            """)
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Close Match Played","Average Runs","Matches Won"]) 
                st.dataframe(df)
            elif medium_selection == medium_questions[7]:    
                cursor.execute("""
                SELECT 
                    b.player_id,
                    b.player_name,
                    YEAR(m.start_date) AS match_year,
                    COUNT(DISTINCT b.match_id) AS matches_played,
                    ROUND(SUM(b.runs) / COUNT(DISTINCT b.match_id), 2) AS avg_runs_per_match,
                     ROUND(SUM(b.runs) * 100.0 / SUM(b.balls), 2) AS avg_strike_rate
                FROM scorecard_match_batsmen b
                JOIN match_details m ON b.match_id = m.match_id
                WHERE YEAR(m.start_date) >= 2020
                GROUP BY b.player_id, b.player_name, YEAR(m.start_date)
                HAVING COUNT(DISTINCT b.match_id) >= 5
                ORDER BY b.player_id, match_year;
            """)  
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Match Year","Match Played","Average Runs","Average strike rate"]) 
                st.dataframe(df)                        
    with tab3:
        complex_selection = st.selectbox("Choose a Complex query", complex_questions)
        if st.button("Execute Complex"):
            if complex_selection == complex_questions[0]:    
                cursor.execute("""
                    SELECT 
                    CASE 
                        WHEN m.toss_status LIKE '%opt to bat%' THEN 'bat'
                        WHEN m.toss_status LIKE '%opt to bowl%' THEN 'bowl'
                        ELSE 'unknown'
                    END AS toss_decision,
                        COUNT(*) AS total_matches,
                        SUM(CASE 
                         WHEN SUBSTRING_INDEX(m.short_status, ' won', 1) = t.team_short_name 
                        AND SUBSTRING_INDEX(m.toss_status, ' opt to', 1) = t.team_name THEN 1
                        ELSE 0
                    END) AS matches_won_by_toss_winner,
                    ROUND(SUM(CASE 
                    WHEN SUBSTRING_INDEX(m.short_status, ' won', 1) = t.team_short_name 
                    AND SUBSTRING_INDEX(m.toss_status, ' opt to', 1) = t.team_name THEN 1
                    ELSE 0
                    END) * 100.0 / COUNT(*), 2) AS win_percentage
                    FROM match_detail_information m
                    JOIN international_teams t 
                    ON SUBSTRING_INDEX(m.toss_status, ' opt to', 1) = t.team_name
                    WHERE 
                        m.state = 'Complete'
                        AND m.toss_status IS NOT NULL
                        AND m.short_status IS NOT NULL
                        AND m.short_status LIKE '%won'
                        GROUP BY toss_decision;
                           """)
                df = pd.DataFrame(cursor.fetchall(), columns = ['Toss Decesion',"Total Matches","Match Won By toss Winner","Win %"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[1]:    
                cursor.execute("""
                    SELECT 
                        p.player_id,
                        tp.player_name,
                        p.format,
                        p.matches,
                        p.balls,
                        ROUND(p.balls / 6.0, 2) AS total_overs,
                        p.runs,
                        p.wickets,
                        ROUND(p.runs / (p.balls / 6.0), 2) AS economy_rate
                    FROM player_bowling_stats p
                    JOIN team_players tp ON p.player_id = tp.player_id
                    WHERE 
                        p.format IN ('ODI', 'T20') AND
                        p.matches >= 10 AND
                        p.balls / p.matches >= 12
                    ORDER BY economy_rate ASC;
                           """)
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Format","Matches","Balls","Total Overs","Runs","Wickets","Economy Rate"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[2]:    
                cursor.execute("""
                    SELECT 
                        b.player_id,
                        tp.player_name,
                        COUNT(*) AS innings_played,
                        ROUND(AVG(b.runs), 2) AS avg_runs,
                        ROUND(STDDEV(b.runs), 2) AS run_stddev
                    FROM scorecard_match_batsmen b
                        JOIN match_details m ON b.match_id = m.match_id
                        JOIN team_players tp ON b.player_id = tp.player_id
                    WHERE 
                        m.start_date >= '2022-01-01'
                    GROUP BY b.player_id, tp.player_name
                    HAVING 
                        COUNT(*) >= 1 AND
                        AVG(b.balls) >= 10 
                        ORDER BY run_stddev ASC;
                           """
            )
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Innings Played","Average Runs","Run Std Dev"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[3]:    
                cursor.execute("""
                    SELECT 
                        p.player_id,
                        tp.player_name,
                    SUM(CASE WHEN p.format = 'Test' THEN p.matches ELSE 0 END) AS test_matches,
                    ROUND(SUM(CASE WHEN p.format = 'Test' THEN p.average ELSE 0 END), 2) AS test_avg,
    
                    SUM(CASE WHEN p.format = 'ODI' THEN p.matches ELSE 0 END) AS odi_matches,
                    ROUND(SUM(CASE WHEN p.format = 'ODI' THEN p.average ELSE 0 END), 2) AS odi_avg,
    
                    SUM(CASE WHEN p.format = 'T20' THEN p.matches ELSE 0 END) AS t20_matches,
                    ROUND(SUM(CASE WHEN p.format = 'T20' THEN p.average ELSE 0 END), 2) AS t20_avg,
    
                    SUM(p.matches) AS total_matches
                FROM player_batting_stats_updated p
                JOIN team_players tp ON p.player_id = tp.player_id
                GROUP BY p.player_id, tp.player_name
                HAVING total_matches >= 20
                ORDER BY total_matches DESC;
                           """
            )          
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Test","Test Average ","ODI","ODI Average","T20","T20 Average","Total Matches"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[4]:    
                cursor.execute("""
                SELECT 
                pbs.player_id,
                tp.player_name,
                pbs.format,
                ROUND((pbs.runs * 0.01) + (pbs.average * 0.5) + (pbs.strike_rate * 0.3), 2) AS batting_points,
                ROUND((pbls.wickets * 2) + ((50 - pbls.average) * 0.5) + ((6 - pbls.economy) * 2), 2) AS bowling_points,
                ROUND(
                (pbs.runs * 0.01) + (pbs.average * 0.5) + (pbs.strike_rate * 0.3) +
                (pbls.wickets * 2) + ((50 - pbls.average) * 0.5) + ((6 - pbls.economy) * 2),
                2) AS total_score
                FROM player_batting_stats pbs
                JOIN player_bowling_stats pbls 
                ON pbs.player_id = pbls.player_id AND pbs.format = pbls.format
                JOIN team_players tp 
                ON pbs.player_id = tp.player_id
                ORDER BY pbs.format, total_score DESC;
                """
                )    
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Format","Batting Points ","Bowling Points","Total Score"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[5]:    
                cursor.execute("""
                    SELECT 
                        MIN(ta.team_name) AS team_a_name,
                        MAX(tb.team_name) AS team_b_name,
                        CONCAT(MIN(ta.team_name), ' vs ', MAX(tb.team_name)) AS matchup,
                        COUNT(*) AS total_matches,
                        SUM(CASE WHEN SUBSTRING_INDEX(m.short_status, ' won', 1) = ta.team_short_name THEN 1 ELSE 0 END) AS team_a_wins,
                        SUM(CASE WHEN SUBSTRING_INDEX(m.short_status, ' won', 1) = tb.team_short_name THEN 1 ELSE 0 END) AS team_b_wins,
                        SUM(CASE WHEN m.toss_status LIKE CONCAT(ta.team_name, '%opt to bat%') AND SUBSTRING_INDEX(m.short_status, ' won', 1) = ta.team_short_name THEN 1 ELSE 0 END) AS team_a_bat_first_wins,
                        SUM(CASE WHEN m.toss_status LIKE CONCAT(ta.team_name, '%opt to bowl%') AND SUBSTRING_INDEX(m.short_status, ' won', 1) = ta.team_short_name THEN 1 ELSE 0 END) AS team_a_bowl_first_wins,
                        SUM(CASE WHEN m.toss_status LIKE CONCAT(tb.team_name, '%opt to bat%') AND SUBSTRING_INDEX(m.short_status, ' won', 1) = tb.team_short_name THEN 1 ELSE 0 END) AS team_b_bat_first_wins,
                        SUM(CASE WHEN m.toss_status LIKE CONCAT(tb.team_name, '%opt to bowl%') AND SUBSTRING_INDEX(m.short_status, ' won', 1) = tb.team_short_name THEN 1 ELSE 0 END) AS team_b_bowl_first_wins,
                        ROUND(SUM(CASE WHEN SUBSTRING_INDEX(m.short_status, ' won', 1) = ta.team_short_name THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS team_a_win_pct,
                        ROUND(SUM(CASE WHEN SUBSTRING_INDEX(m.short_status, ' won', 1) = tb.team_short_name THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS team_b_win_pct
                    FROM match_detail_information m
                    JOIN international_teams ta ON ta.team_id = LEAST(m.team1_id, m.team2_id)
                    JOIN international_teams tb ON tb.team_id = GREATEST(m.team1_id, m.team2_id)
                    WHERE 
                        m.state = 'Complete' AND
                        m.short_status LIKE '%won' AND
                        m.start_date >= DATE_SUB(CURDATE(), INTERVAL 3 YEAR)
                    GROUP BY LEAST(m.team1_id, m.team2_id), GREATEST(m.team1_id, m.team2_id)
                        HAVING total_matches >= 4
                        ORDER BY total_matches DESC;
                           """)                                
                df = pd.DataFrame(cursor.fetchall(), columns = ['Team A',"Team B","Match","Total Matches","Team A Wins","Team B Wins",
                    "Team A Bat first Wins","Team A Bowl First Wins","Team B Bat first Wins","Team B Bowl First Wins","Team A Win Pct","Team B Win Pct"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[6]:    
                cursor.execute(""" 
                    WITH recent_batting AS (
                    SELECT 
                        b.player_id,
                        tp.player_name,
                        b.runs,
                        b.balls,
                        b.match_id,
                        ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.start_date DESC) AS rn
                    FROM scorecard_match_batsmen b
                    JOIN match_details m ON b.match_id = m.match_id
                    JOIN team_players tp ON b.player_id = tp.player_id
                        )
                    SELECT 
                        player_id,
                        player_name,
                    ROUND(AVG(CASE WHEN rn <= 5 THEN runs ELSE NULL END), 2) AS avg_runs_last_5,
                    ROUND(AVG(CASE WHEN rn <= 10 THEN runs ELSE NULL END), 2) AS avg_runs_last_10,
                    ROUND(AVG(CASE WHEN rn <= 5 THEN (runs / balls) * 100 ELSE NULL END), 2) AS strike_rate_last_5,
                    ROUND(AVG(CASE WHEN rn <= 10 THEN (runs / balls) * 100 ELSE NULL END), 2) AS strike_rate_last_10,
                    SUM(CASE WHEN rn <= 10 AND runs >= 50 THEN 1 ELSE 0 END) AS scores_50_plus,
                    ROUND(STDDEV(CASE WHEN rn <= 10 THEN runs ELSE NULL END), 2) AS consistency_score,
                CASE
                    WHEN AVG(CASE WHEN rn <= 5 THEN runs ELSE NULL END) >= 50 AND STDDEV(CASE WHEN rn <= 10 THEN runs ELSE NULL END) <= 15 THEN 'Excellent Form'
                    WHEN AVG(CASE WHEN rn <= 5 THEN runs ELSE NULL END) >= 35 THEN 'Good Form'
                    WHEN AVG(CASE WHEN rn <= 5 THEN runs ELSE NULL END) >= 20 THEN 'Average Form'
                    ELSE 'Poor Form'
                END AS form_category
                FROM recent_batting
                WHERE rn <= 10
                GROUP BY player_id, player_name
                ORDER BY avg_runs_last_5 DESC;
                """
            )         
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name","Average last 5","Average Last 10","Strike rate last 5","Strike Rate last 10",
                    "Score 50 plus","Consistency Score","Form"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[7]:    
                cursor.execute(""" 
                    WITH consecutive_pairs AS (
                    SELECT 
                        b1.match_id,
                        b1.inningsid,
                        b1.player_id AS player1_id,
                        b2.player_id AS player2_id
                    FROM batting_sequence b1
                    JOIN batting_sequence b2 
                    ON b1.match_id = b2.match_id 
                    AND b1.inningsid = b2.inningsid
                    AND ABS(b1.batting_sequence - b2.batting_sequence) = 1
                    AND b1.player_id < b2.player_id  -- avoid duplicate pairs
                    )
                SELECT 
                    cp.player1_id,
                    tp1.player_name AS player1_name,
                    cp.player2_id,
                    tp2.player_name AS player2_name,    
                    COUNT(*) AS partnership_count,
                    ROUND(AVG(p.total_runs), 2) AS avg_partnership_runs,
                    MAX(p.total_runs) AS highest_partnership,
                    SUM(CASE WHEN p.total_runs > 50 THEN 1 ELSE 0 END) AS fifty_plus_partnerships,
                    ROUND(SUM(CASE WHEN p.total_runs > 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate
                FROM consecutive_pairs cp
                JOIN scorecard_match_partnership p 
                ON cp.match_id = p.match_id 
                AND cp.inningsid = p.inningsid
                AND ((cp.player1_id = p.player1_id AND cp.player2_id = p.player2_id) 
                OR (cp.player1_id = p.player2_id AND cp.player2_id = p.player1_id))
                JOIN team_players tp1 ON cp.player1_id = tp1.player_id
                JOIN team_players tp2 ON cp.player2_id = tp2.player_id
                GROUP BY cp.player1_id, cp.player2_id
                HAVING COUNT(*) >= 5
                ORDER BY success_rate DESC, avg_partnership_runs DESC;
                """
            )        
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player1 ID',"Player1 Name",'Player2 ID',"Player2 Name","Partmership Count","Average Partnership","Highest Partnership","Fifty Plus Partnership",
                    "Scuccess Rate"]) 
                st.dataframe(df)
            elif complex_selection == complex_questions[8]:    
                cursor.execute("""
                    WITH player_quarterly_stats AS (
                    SELECT 
                        b.player_id,
                        tp.player_name,
                        CONCAT(YEAR(m.start_date), '-Q', QUARTER(m.start_date)) AS quarter,
                        COUNT(*) AS match_count,
                        ROUND(AVG(b.runs), 2) AS avg_runs,
                        ROUND(AVG((b.runs / b.balls) * 100), 2) AS avg_strike_rate
                    FROM scorecard_match_batsmen b
                    JOIN match_details m ON b.match_id = m.match_id
                    JOIN team_players tp ON b.player_id = tp.player_id
                    WHERE b.balls > 0
                    GROUP BY b.player_id, quarter
                    HAVING COUNT(*) >= 2
                    ),
                with_trends AS (
                SELECT *,
                    LAG(avg_runs) OVER (PARTITION BY player_id ORDER BY quarter) AS prev_avg_runs,
                CASE
                 WHEN avg_runs > LAG(avg_runs) OVER (PARTITION BY player_id ORDER BY quarter) THEN 'Improving'
                WHEN avg_runs < LAG(avg_runs) OVER (PARTITION BY player_id ORDER BY quarter) THEN 'Declining'
                ELSE 'Stable'
                END AS trend
                FROM player_quarterly_stats
                ),
                career_phase AS (
            SELECT 
                player_id,
                player_name,
                COUNT(DISTINCT quarter) AS quarters_played,
                SUM(CASE WHEN trend = 'Improving' THEN 1 ELSE 0 END) AS improving_quarters,
                SUM(CASE WHEN trend = 'Declining' THEN 1 ELSE 0 END) AS declining_quarters,
                SUM(CASE WHEN trend = 'Stable' THEN 1 ELSE 0 END) AS stable_quarters,
            CASE
                WHEN SUM(CASE WHEN trend = 'Improving' THEN 1 ELSE 0 END) >= 4 THEN 'Career Ascending'
                WHEN SUM(CASE WHEN trend = 'Declining' THEN 1 ELSE 0 END) >= 4 THEN 'Career Declining'
                ELSE 'Career Stable'
                END AS career_phase
            FROM with_trends
            GROUP BY player_id, player_name
            HAVING COUNT(DISTINCT quarter) >= 5
            )
            SELECT * FROM career_phase
            ORDER BY career_phase, improving_quarters DESC;
                           """
            )    
                df = pd.DataFrame(cursor.fetchall(), columns = ['Player ID',"Player Name",'Quarters Played',"Improving Quaters","Declining Quaters","Stable quaters","Career Phase"]) 
                st.dataframe(df)                                                  
    # Close connection
    cursor.close()

elif page == "CRUD Operation":
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Create", "📖 Read", "✏️ Update", "🗑️ Delete"])
    def get_connection():
        return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Welcome*1",
        database="cricbuzz"
        )
    with tab1:
        st.subheader("➕ Add New Player")
        player_name = st.text_input("Player Name")
        format = st.selectbox("Format", ["ODI", "T20", "Test"])
        matches = st.number_input("Matches", min_value=0)
        innings = st.number_input("Innings", min_value=0)
        runs = st.number_input("Runs", min_value=0)
        balls = st.number_input("Balls Faced", min_value=0)
        average = st.number_input("Batting Average", min_value=0.0)
        strike_rate = st.number_input("Strike Rate", min_value=0.0)

        if st.button("Add Player"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO temp_cricket_stats (player_name, format, matches, innings, runs, balls, average, strike_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (player_name, format, matches, innings, runs, balls, average, strike_rate))
            conn.commit()
            st.success(f"Player '{player_name}' added successfully!")

    with tab2:
        st.subheader("📖 View Player Stats")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT player_id, player_name, format, matches, innings, runs, balls, average, strike_rate
        FROM temp_cricket_stats
        """)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    
        df = pd.DataFrame(rows, columns=columns)
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.subheader("✏️ Update Player Stats")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT player_id, player_name FROM temp_cricket_stats")
        players = cursor.fetchall()
        player_map = {f"{p[1]} (ID: {p[0]})": p[0] for p in players}
        selected = st.selectbox("Select Player to Update", list(player_map.keys()))
        player_id = player_map[selected]

        new_matches = st.number_input("New Matches", min_value=0)
        new_innings = st.number_input("New Innings", min_value=0)
        new_runs = st.number_input("New Runs", min_value=0)
        new_balls = st.number_input("New Balls Faced", min_value=0)
        new_average = st.number_input("New Batting Average", min_value=0.0)
        new_strike_rate = st.number_input("New Strike Rate", min_value=0.0)

        if st.button("Update Player"):
            cursor.execute("""
            UPDATE temp_cricket_stats
            SET matches = %s, innings = %s, runs = %s, balls = %s, average = %s, strike_rate = %s
            WHERE player_id = %s
            """, (new_matches, new_innings, new_runs, new_balls, new_average, new_strike_rate, player_id))
            conn.commit()
            st.success(f"Player ID {player_id} updated successfully!")

    with tab4:
        st.subheader("🗑️ Delete Player")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT player_id, player_name FROM temp_cricket_stats")
        players = cursor.fetchall()
        player_map = {f"{p[1]} (ID: {p[0]})": p[0] for p in players}
        selected = st.selectbox("Select Player to Delete", list(player_map.keys()))
        player_id = player_map[selected]

        if st.button("Delete Player"):
            cursor.execute("DELETE FROM temp_cricket_stats WHERE player_id = %s", (player_id,))
            conn.commit()
            st.success(f"Player ID {player_id} deleted successfully!")
 