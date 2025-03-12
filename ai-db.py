import json
import mysql.connector
import re
import requests

# Database connection settings
DB_CONFIG = {
	"host": "localhost",
	"user": "root",
	"password": "root",
	"database": "nfl_games"
}

OLLAMA_URL = "http://localhost:11434/api/generate"
ANALYIS_MODEL = "qwen2.5:14b"
SQL_MODEL = "qwen2.5-coder:14b"

NFL_CURRENT_SEASON = 2024 # Update this annually
NFL_EARLIEST_SEASON = 2000 # Earliest season in the database

# Function to connect to MySQL
def connect_to_db():
	return mysql.connector.connect(**DB_CONFIG)

def extract_season_from_question(question):
	"""
	Extract season year from various question formats:
	- 2024 season
	- 2024/2025 season
	- 2024-2025 season
	Returns the season year (e.g., 2024) or None if not found
	"""
	
	# Look for patterns like "2024/2025", "2024-2025", or "2024 season"
	season_patterns = [
		r'(\d{4})[/-]\d{4}', # matches 2024/2025 or 2024-2025
		r'(\d{4})\s+season', # matches 2024 season
	]
	
	for pattern in season_patterns:
		match = re.search(pattern, question)
		if match:
			season = int(match.group(1))
			if NFL_EARLIEST_SEASON <= season <= NFL_CURRENT_SEASON:
				return season
	return None

def get_nfl_season_date_condition(season):
	"""
	Returns SQL condition for NFL season dates.
	A season includes games from September of the season year
	through March of the following year.
	"""
	if not (NFL_EARLIEST_SEASON <= season <= NFL_CURRENT_SEASON):
		raise ValueError(f"Season must be between {NFL_EARLIEST_SEASON} and {NFL_CURRENT_SEASON}")
	return f"(event_date BETWEEN '{season}-09-01' AND '{season+1}-03-31')"

# Function to generate an SQL query using Ollama
def generate_sql_query(question):
	# Extract season from question
	season = extract_season_from_question(question)

	prompt = f"""You are a MySQL query generator specialized in NFL statistics. Generate a SQL query for: "{question}"

	DATABASE SCHEMA:
	Table: games
	- Primary purpose: Records of NFL games with teams, scores, and dates
	- Key columns:
	* `status` ( varchar(50) ) -- Current game status. Ex. closed
	* `season` ( int ) -- NFL season year
	* `week` ( int ) -- Week number in the NFL season
	* `week_day` ( varchar(10) ) -- Day of the week the game was played
	* `event_date` ( date ) -- Date of the game
	* `tm_nano` ( varchar(50) ) -- Unique identifier for the team that won the game
	* `tm_market` ( varchar(50) ) -- Team City Name of the team that won, Ex. Philadelphia
	* `tm_name` ( varchar(50) ) -- Team Name of the team that won, Ex. Eagles
	* `tm_alias` ( varchar(10) ) -- Team Alias of the team that won, Ex. PHI
	* `tm_alt_market` ( varchar(50) ) -- Alternative Team City Name of the team that won formatted like philadelphia-eagles
	* `tm_alt_alias` ( varchar(10) ) -- Alternative Team Alias of the team that won formatted like phi
	* `opp_nano` ( varchar(50) ) -- Unique identifier for the team that lost the game
	* `opp_market` ( varchar(50) ) -- Team City Name of the team that lost, Ex. Kansas City
	* `opp_name` ( varchar(50) ) -- Team Name of the team that lost, Ex. Chiefs
	* `opp_alias` ( varchar(10) ) -- Team Alias of the team that lost, Ex. KC
	* `opp_alt_market` ( varchar(50) ) -- Alternative Team City Name of the team that lost formatted like kansas-city-chiefs
	* `opp_alt_alias` ( varchar(10) ) -- Alternative Team Alias of the team that lost formatted like kan
	* `tm_location` ( char(1) ) -- An H or A representing if the team that won was home or away
	* `opp_location` ( char(1) ) -- An H or A representing if the team that lost was home or away
	* `tm_score` ( int ) -- Score of the team that won
	* `opp_score` ( int ) -- Score of the team that lost
	* `boxscore_stats_link` ( varchar(255) ) -- Link to the boxscore stats

	Table: game_stats
	- Primary purpose: Individual team statistics per game
	- Key columns:
	* `season` ( bigint ) -- Year number of the NFL season
	* `event_date` ( text ) -- Date of the game
	* `nano` ( text ) -- Unique identifier for the game
	* `market` ( text ) -- Team City Name, Ex. Philadelphia
	* `name` ( text ) -- Team Name, Ex. Eagles
	* `alias` ( text ) -- Team Alias, Ex. PHI
	* `rush_att` ( bigint ) -- Number of team rushing attempts
	* `rush_yds` ( bigint ) -- Total team rushing yards
	* `rush_tds` ( bigint ) -- Number of team rushing touchdowns
	* `pass_cmp` ( bigint ) -- Number of team completed passes
	* `pass_att` ( bigint ) -- Number of team pass attempts
	* `pass_cmp_pct` ( double ) -- Team pass completion percentage
	* `pass_yds` ( bigint ) -- Total team passing yards
	* `pass_tds` ( bigint ) -- Number of team passing touchdowns
	* `pass_int` ( bigint ) -- Number of team interceptions thrown
	* `passer_rating` ( double ) -- Team passer rating
	* `net_pass_yds` ( bigint ) -- Net team passing yards
	* `total_yds` ( bigint ) -- Total team yards gained
	* `times_sacked` ( bigint ) -- Number of times the team's quarterback was sacked
	* `yds_sacked_for` ( bigint ) -- Total yards lost due to sacks
	* `fumbles` ( bigint ) -- Number of team fumbles
	* `fumbles_lost` ( bigint ) -- Number of team fumbles lost
	* `turnovers` ( bigint ) -- Total number of team turnovers
	* `penalties` ( bigint ) -- Number of team penalties
	* `penalty_yds` ( bigint ) -- Total team penalty yards
	* `first_downs` ( bigint ) -- Number of team first downs
	* `third_down_conv` ( bigint ) -- Number of team third down conversions
	* `third_down_att` ( bigint ) -- Number of team third down attempts
	* `third_down_conv_pct` ( double ) -- Team third down conversion percentage
	* `fourth_down_conv` ( bigint ) -- Number of team fourth down conversions
	* `fourth_down_att` ( bigint ) -- Number of team fourth down attempts
	* `fourth_down_conv_pct` ( double ) -- Team fourth down conversion percentage
	* `time_of_possession` ( bigint ) -- Team time of possession
	* `boxscore_stats_link` ( text ) -- Link to the boxscore stats

	REQUIREMENTS:
	1. Use table alias 'g' for games and 'gs' for game_stats
	2. Always prefix columns with table alias (g. or gs.)
	3. For season filtering use: {get_nfl_season_date_condition(season if season else NFL_CURRENT_SEASON)}

	EXAMPLE QUERIES:
	1. Find Eagles games in 2023:
	SELECT g.event_date, g.tm_score, g.opp_score
	FROM games g
	WHERE (g.tm_name = 'Eagles' OR g.opp_name = 'Eagles')
	AND g.event_date BETWEEN '2023-09-01' AND '2024-03-31';

	2. Get Chiefs rushing stats in 2023:
	SELECT gs.event_date, gs.rush_yds, gs.rush_tds
	FROM game_stats gs
	WHERE (gs.name = 'Chiefs' OR gs.alias = 'KC')
	AND gs.event_date BETWEEN '2023-09-01' AND '2024-03-31';

	RESPONSE FORMAT:
	<SQL>
	Your SQL query here
	</SQL>"""

	print("Sending prompt to Ollama...\n")

	response = requests.post(
		OLLAMA_URL,
		json={
			"model": SQL_MODEL,
			"prompt": prompt,
			"stream": False
		}
	)

	if response.status_code == 200:
		query = response.json().get('response', '')
		# Extract query between <SQL> tags and clean it
		match = re.search(r'<SQL>(.*?)</SQL>', query, re.DOTALL)
		if match:
			query = match.group(1).strip()
		else:
			query = query.replace('```sql', '').replace('```', '').strip()
		print(f"\nGenerated query: {query}\n")
		return query
	else:
		return f"Error: Failed to generate query. Status code: {response.status_code}"

# Function to format results with column headers
def format_results(cursor, results):
	"""Format results with column headers"""
	if not results:
		return []
	
	# Get column names from cursor description
	headers = [desc[0] for desc in cursor.description]
	formatted_results = [headers]  # Start with headers
	
	# Format each row, handling None values
	for row in results:
		formatted_row = []
		for value in row:
			if isinstance(value, float):
				formatted_row.append(f"{value:.2f}")
			elif value is None:
				formatted_row.append("N/A")
			else:
				formatted_row.append(str(value))
		formatted_results.append(formatted_row)
	
	return formatted_results

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
		formatted_results = format_results(cursor, results)
		
		return formatted_results
	except mysql.connector.Error as err:
		print(f"Database error: {err}")
		return None
	finally:
		cursor.close()
		conn.close()

# Function to send results to Ollama for further analysis
def analyze_with_ollama(results, question):
	formatted_results = []

	for row in results:
		formatted_results.append(list(map(str, row)))
	
	prompt = f"""
	You are an NFL analyst providing insights with the given data that was formatted from a MySQL query.
	
	Question: {question}
	Data: {formatted_results}
	
	Provide a very brief, direct answer using the data.
	Keep it to 1-2 sentences maximum.
	Only include relevant numbers.
	Use past-tense as these games have already happened.
	"""
	
	response = requests.post(
		OLLAMA_URL,
		json={
			"model": ANALYIS_MODEL,
			"prompt": prompt,
			"stream": False
		}
	)
	
	if response.status_code == 200:
		analysis = response.json().get('response', '')
		return analysis.strip()
	else:
		return f"Error: Failed to analyze results. Status code: {response.status_code}"

# Main function
def main():
	while True:
		question = input("\nEnter your NFL analysis question (or 'quit' to exit): ")
		if question.lower() == 'quit':
			break
			
		print("\nBeginning analysis...")
		
		sql_query = generate_sql_query(question)
		
		results = query_db(sql_query)
		if results:
			analysis = analyze_with_ollama(results, question)
			print("\nAnalysis:")
			print(analysis)
		else:
			print("\nNo results found or error in query execution.")

if __name__ == "__main__":
	main()
