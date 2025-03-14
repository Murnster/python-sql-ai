import json
import mysql.connector
import re
import requests

DB_CONFIG = {
	"host": "localhost",
	"user": "username",
	"password": "username",
	"database": "nfl_games"
}

def connect_to_db():
	return mysql.connector.connect(**DB_CONFIG)

def close_db_connection(db):
	db.close()

# Function to get the database schema
def get_db_schema(db):
	cursor = db.cursor()
	schema = {
		"metadata": {
			"database": DB_CONFIG["database"],
			"description": "NFL game statistics database with game results and team performance metrics"
		},
		"tables": {},
		"relationships": [
			{
				"from": "games",
				"to": "game_stats",
				"type": "one_to_many",
				"description": "One games row maps to exactly two game_stats rows by game_id.",
				"join_conditions": [
					"games.game_id = game_stats.game_id"
				],
				"cardinality": "1:2"
			}, {
				"from": "game_stats",
				"to": "games",
				"type": "many_to_one",
				"description": "Each team in game_stats corresponds to either team_city_name_winner or team_city_name_loser in games.",
				"join_conditions": [
					"game_stats.team_identifier = games.team_identifier_winner OR game_stats.team_identifier = games.team_identifier_loser"
				],
				"cardinality": "2:1"
			}
		],
		"common_queries": [
			{
				"purpose": "Count total games for a team in a season",
				"pattern": "SELECT COUNT(*) FROM games WHERE (nfl_team_name_winner = 'Team' OR nfl_team_name_loser = 'Team') AND season = YYYY"
			},
			{
				"purpose": "Count total games for a team in a date range",
				"pattern": "SELECT COUNT(*) FROM games WHERE (nfl_team_name_winner = 'Team' OR nfl_team_name_loser = 'Team') AND event_date BETWEEN 'YYYY-01-01' AND 'YYYY-12-31'"
			},
			{
				"purpose": "Get total wins for a team in a season",
				"pattern": "SELECT COUNT(*) FROM games WHERE nfl_team_name_winner = 'Team' AND season = YYYY"
			}
		]
	}
	
	cursor.execute("SHOW TABLES")
	table_names = [table[0] for table in cursor.fetchall()]
	
	# With tables, get columns and descriptions
	for table in table_names:
		schema["tables"][table] = {
			"description": (
				"NFL games between teams including scores, locations, and dates. Each row represents a complete game with both teams - one as winner and one as loser. To find all games for a team, check both nfl_team_name_winner AND nfl_team_name_loser columns."
				if table == "games" else
				"Game statistics for each team in a game (two rows per game)"
			),
			"columns": [],
			"sample_query": (
				"SELECT COUNT(*) FROM games WHERE nfl_team_name_winner = 'Eagles' OR nfl_team_name_loser = 'Eagles'"
				if table == "games" else
				"SELECT * FROM game_stats WHERE team_city_name = 'Philadelphia'"
			)
		}
		
		cursor.execute(f"DESCRIBE {table}")
		columns = cursor.fetchall()
		
		for col in columns:
			schema["tables"][table]["columns"].append({
				"name": col[0],
				"type": col[1],
				"key": col[3],
				"description": get_column_description(table, col[0])
			})
	
	return schema

# Function to get detailed column descriptions
def get_column_description(table, column):
	"""Return detailed description for specific columns"""
	descriptions = {
		"games": {
			"game_id": "Unique identifier for the game",
			"status": "Game status (e.g., final, in progress)",
			"season": "NFL season year",
			"week": "Week number of the NFL season",
			"week_day": "Day of the week game was played",
			"event_date": "Date of the game",
			"team_identifier_winner": "Unique identifier for winning team",
			"team_city_name_winner": "City name of winning team",
			"nfl_team_name_winner": "Official NFL name of winning team",
			"team_identifier_loser": "Unique identifier for losing team",
			"team_city_name_loser": "City name of losing team",
			"nfl_team_name_loser": "Official NFL name of losing team",
			"location_winner": "Home/Away status of winning team H or A",
			"location_loser": "Home/Away status of losing team H or A",
			"score_winner": "Final score of winning team",
			"score_loser": "Final score of losing team",
			"boxscore_stats_link": "URL link to detailed game statistics"
		},
		"game_stats": {
			"stat_id": "Unique identifier for the statistics entry",
			"game_id": "Identifier linking to the specific game",
			"season": "NFL season year",
			"event_date": "Date of the game",
			"team_identifier": "Unique team identifier",
			"team_city_name": "City name of the team",
			"nfl_team_name": "Official NFL team name",
			"rushing_attempts": "Number of rushing plays attempted",
			"rushing_yards": "Total yards gained from rushing",
			"rushing_touchdowns": "Number of touchdowns scored by rushing",
			"passing_completions": "Number of completed passes",
			"passing_attempts": "Number of attempted passes",
			"passing_completion_percentage": "Percentage of passes completed",
			"passing_yards": "Total yards gained from passing",
			"passing_touchdowns": "Number of touchdowns scored by passing",
			"passing_interceptions": "Number of passes intercepted",
			"passer_rating": "Quarterback rating calculated from passing statistics",
			"net_passing_yards": "Total passing yards minus yards lost from sacks",
			"total_yards": "Combined rushing and passing yards",
			"times_sacked": "Number of times quarterback was sacked",
			"yards_sacked_for": "Total yards lost from sacks",
			"fumbles": "Number of times the ball was fumbled",
			"fumbles_lost": "Number of fumbles recovered by opposing team",
			"turnovers": "Total number of interceptions and lost fumbles",
			"penalties": "Number of penalties called against the team",
			"penalty_yards": "Total yards lost from penalties",
			"first_downs": "Number of first downs achieved",
			"third_down_conversions": "Number of successful third down conversions",
			"third_down_attempts": "Total number of third down attempts",
			"third_down_conversion_percentage": "Percentage of successful third down conversions",
			"fourth_down_conversions": "Number of successful fourth down conversions",
			"fourth_down_attempts": "Total number of fourth down attempts",
			"fourth_down_conversion_percentage": "Percentage of successful fourth down conversions",
			"time_of_possession": "Total time team had possession of the ball in seconds",
			"boxscore_stats_link": "URL link to detailed game statistics"
		}
	}
	
	return descriptions.get(table, {}).get(column, f"The {column} field")

# Function to query the database
def query_db(query):
	conn = connect_to_db()
	cursor = conn.cursor()
	
	print(f"Executing query...")
	
	try:
		# Basic SQL injection prevention
		if any(keyword.lower() in query.lower() for keyword in ['insert', 'update', 'delete', 'drop', 'truncate']):
			raise Exception("Invalid query type detected")
		
		cursor.execute(query)
		results = cursor.fetchall()
		
		return results
	except mysql.connector.Error as err:
		print(f"Database error: {err}")
		return None
	finally:
		cursor.close()
		conn.close()

# Function to generate SQL query from user question
def generate_sql(question):
	db = connect_to_db()
	schema = get_db_schema(db)
	
	print(schema)
	
	close_db_connection(db)
	
	prompt = f"""
	You are an expert in converting natural language to SQL queries.
	
	Database Schema:
	{json.dumps(schema, default=str, indent=2, ensure_ascii=False, sort_keys=True)}
	
	Example queries:
	"How many games total did the Bengals play in 2024?"
	SELECT COUNT(*) FROM `games` WHERE (`nfl_team_name_winner` = 'Bengals' OR `nfl_team_name_loser` = 'Bengals') AND `season` = 2024;
	
	"Give me the game ID, date, week, passing yards, rushing yards and total yards stats for the Patriots in 2023."
	SELECT g.game_id, g.event_date, g.week, gs.passing_yards, gs.rushing_yards, gs.total_yards FROM games g JOIN game_stats gs ON g.game_id = gs.game_id WHERE gs.nfl_team_name = 'Patriots' AND g.season = 2023 ORDER BY g.event_date;
	
	"What was the average passing yards per game for the Eagles in 2023?"
	SELECT 'Eagles' AS team_name, ROUND(AVG(gs.passing_yards), 1) AS avg_passing_yards_per_game FROM games g JOIN game_stats gs ON g.game_id = gs.game_id WHERE gs.nfl_team_name = 'Eagles' AND g.season = 2023;
	
	"What was the time of possession for the Chiefs in 2023?"
	SELECT team_city_name, CONCAT(FLOOR(time_of_possession/60), ':', LPAD(time_of_possession%60, 2, '0')) AS possession_time FROM game_stats WHERE season = 2023 AND nfl_team_name = 'Chiefs';
	
	User Query: {question}
	
	Generate a valid MySQL query that answers the user's question.
	Return ONLY the SQL query without any explanation or markdown.
	"""
	
	response = requests.post(
		"http://localhost:11434/api/generate",
		json={
			"model": "qwen2.5-coder:14b",
			"prompt": prompt,
			"stream": False
		}
	)
	
	if response.status_code == 200:
		query = response.json().get('response', '')
		match = re.search(r'<SQL>(.*?)</SQL>', query, re.DOTALL)
		
		if match:
			query = match.group(1).strip()
		else:
			query = query.replace('```sql', '').replace('```', '').strip()
			
		print(f"\nGenerated query: {query}\n")
		return query
	else:
		return f"Error: Failed to generate query. Status code: {response.status_code}"

# Function to send results to Ollama for further analysis
def analyze_with_ollama(results, question):
	print("Sending results to Ollama for analysis...")
	
	formatted_results = []

	for row in results:
		formatted_results.append(list(map(str, row)))
	
	prompt = f"""
	You are an NFL analyst providing insights with the given data that was formatted from a MySQL query.
	
	Question: {question}
	Data: {results}
	
	Provide a very brief, direct answer using the data.
	Only include relevant numbers that the data provides.
	Use past-tense as these games have already happened.
	"""
	
	response = requests.post(
		"http://localhost:11434/api/generate",
		json={
			"model": "qwen2.5-coder:14b",
			"prompt": prompt,
			"stream": False
		}
	)
	
	if response.status_code == 200:
		analysis = response.json().get('response', '')
		return analysis.strip()
	else:
		return f"Error: Failed to analyze results. Status code: {response.status_code}"
	
def main():
	while True:
		question = input("\nEnter your NFL analysis question (or 'quit' to exit): ")
		if question.lower() == 'quit':
			break
			
		print("\nBeginning analysis...")
		
		sql_query = generate_sql(question)
		
		results = query_db(sql_query)
		
		if results:
			analysis = analyze_with_ollama(results, question)
			print("\nAnalysis:")
			print(analysis)
		else:
			print("\nNo results found or error in query execution.")

if __name__ == "__main__":
	main()