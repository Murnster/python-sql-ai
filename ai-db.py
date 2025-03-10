import mysql.connector
import requests
import json

# Database connection settings
DB_CONFIG = {
	"host": "localhost",
	"user": "root",
	"password": "root",
	"database": "nfl_games"
}

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi4"  # You can change this to another model

DB_SCHEMA_TABLE_DESC = {
	"games": "This table represents NFL games played between a team and an opponent with data including scores, locations, and dates.",
	"game_stats": "This table represents game statistics for a specific team for an NFL game including rushing yards, passing yards, and turnovers. There are two rows for each game, one for each team.",
}

DB_SCHEMA_DESCRIPTION_STATS = {
	"season": "Year number of the NFL season",
	"event_date": "Date of the game",
	"nano": "Unique identifier for the game",
	"market": "Team City Name, Ex. Philadelphia",
	"name": "Team Name, Ex. Eagles",
	"alias": "Team Alias, Ex. PHI",
	"rush_att": "Number of rushing attempts",
	"rush_yds": "Total rushing yards",
	"rush_tds": "Number of rushing touchdowns",
	"pass_cmp": "Number of completed passes",
	"pass_att": "Number of pass attempts",
	"pass_cmp_pct": "Pass completion percentage",
	"pass_yds": "Total passing yards",
	"pass_tds": "Number of passing touchdowns",
	"pass_int": "Number of interceptions thrown",
	"passer_rating": "Passer rating",
	"net_pass_yds": "Net passing yards",
	"total_yds": "Total yards gained",
	"times_sacked": "Number of times the quarterback was sacked",
	"yds_sacked_for": "Total yards lost due to sacks",
	"fumbles": "Number of fumbles",
	"fumbles_lost": "Number of fumbles lost",
	"turnovers": "Total number of turnovers",
	"penalties": "Number of penalties",
	"penalty_yds": "Total penalty yards",
	"first_downs": "Number of first downs",
	"third_down_conv": "Number of third down conversions",
	"third_down_att": "Number of third down attempts",
	"third_down_conv_pct": "Third down conversion percentage",
	"fourth_down_conv": "Number of fourth down conversions",
	"fourth_down_att": "Number of fourth down attempts",
	"fourth_down_conv_pct": "Fourth down conversion percentage",
	"time_of_possession": "Time of possession",
	"boxscore_stats_link": "Link to the boxscore stats"
}

DB_SCHEMA_DESCRIPTION_GAMES = {
	"status": "Current game status. Ex. closed",
	"season": "Year number of the NFL season",
	"week": "Week number in the NFL season",
	"week_day": "Day of the week the game was played",
	"event_date": "Date of the game",
	"tm_nano": "Unique identifier for the team",
	"tm_market": "Home Team City Name, Ex. Philadelphia",
	"tm_name": "Home Team Name, Ex. Eagles",
	"tm_alias": "Home Team Alias, Ex. PHI",
	"tm_alt_market": "Alternative Home Team City Name formatted like philadelphia-eagles",
	"tm_alt_alias": "Alternative Home Team Alias formatted like phi",
	"opp_nano": "Unique identifier for the opponent team",
	"opp_market": "Away Team City Name, Ex. Kansas City",
	"opp_name": "Away Team Name, Ex. Chiefs",
	"opp_alias": "Away Team Alias, Ex. KC",
	"opp_alt_market": "Alternative Away Team City Name formatted like kansas-city-chiefs",
	"opp_alt_alias": "Alternative Away Team Alias formatted like kan",
	"tm_location": "An H representing home team",
	"opp_location": "An A representing away team",
	"tm_score": "Score of the home team",
	"opp_score": "Score of the away team",
	"boxscore_stats_link": "Link to the boxscore stats"
}

# Function to connect to MySQL
def connect_to_db():
	return mysql.connector.connect(**DB_CONFIG)

# Function to get the database schema
def get_db_schema():
	conn = connect_to_db()
	cursor = conn.cursor()
	
	# Fetch table names
	cursor.execute("SHOW TABLES;")
	tables = [table[0] for table in cursor.fetchall()]
	
	schema_info = {}
	
	# Fetch column details for each table
	for table in tables:
		cursor.execute(f"DESCRIBE {table};")
		columns = cursor.fetchall()
		
		schema_info[table] = {}
		schema_info[table]["description"] = DB_SCHEMA_TABLE_DESC.get(table, "No description available")
		
		if table == "games":
			schema_info[table]["data"] = [{"name": col[0], "type": col[1], "description": DB_SCHEMA_DESCRIPTION_GAMES.get(col[0], "No description for this column")} for col in columns]
		elif table == "game_stats":
			schema_info[table]["data"] = [{"name": col[0], "type": col[1], "description": DB_SCHEMA_DESCRIPTION_STATS.get(col[0], "No description for this column")} for col in columns]
		
	cursor.close()
	conn.close()
	
	return json.dumps(schema_info, indent=2)

# Function to generate an SQL query using Ollama
def generate_sql_query(question, schema):
	schema_data = json.loads(schema)
	
	# Create a more SQL-focused schema representation
	sql_schema = "Database Schema:\n\n"
	
	# Add table descriptions
	for table, info in schema_data.items():
		sql_schema += f"{table} table: {info['description']}\nColumns:\n"
		for col in info['data']:
			sql_schema += f"  - {col['name']} ({col['type']}): {col['description']}\n"
		sql_schema += "\n"
	
	print(sql_schema)
	
	prompt = f"""
	You are an NFL data expert writing MySQL queries. Using this schema:
	{sql_schema}
	
	Generate a MySQL query to answer: "{question}"
	
	Important guidelines:
	1. For simple counts or game info, use the games table alone
	2. Only use JOINs when you need specific statistics from game_stats
	3. When using game_stats, remember:
	- Home team stats: JOIN game_stats AS home_stats ON games.tm_nano = home_stats.nano
	- Away team stats: JOIN game_stats AS away_stats ON games.opp_nano = away_stats.nano
	4. Use the season column directly, not YEAR(event_date)
	5. Always use table aliases in JOINs
	
	Return only the SQL query without explanation.
	"""
	
	# print prompt
	print("Sending prompt to Ollama...\n")
	response = requests.post(
		OLLAMA_URL,
		json={
			"model": OLLAMA_MODEL,
			"prompt": prompt,
			"stream": False
		}
	)
	
	if response.status_code == 200:
		# Extract the response text
		query = response.json().get('response', '')
		# Clean up the query by removing extra whitespace and newlines
		query = query.strip()
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
	
	print(f"Executing query: {query}")
	
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
def analyze_with_ollama(results, schema, question):
	formatted_results = []

	for row in results:
		formatted_results.append(list(map(str, row)))
	
	prompt = f"""
	You are an NFL analyst providing quick insights.
	
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
			"model": OLLAMA_MODEL,
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
			
		print("\nAnalyzing...")
		schema = get_db_schema()
		sql_query = generate_sql_query(question, schema)
		
		print("\nExecuting query...")
		results = query_db(sql_query)
		if results:
			analysis = analyze_with_ollama(results, schema, question)
			print("\nAnalysis:")
			print(analysis)
		else:
			print("\nNo results found or error in query execution.")

if __name__ == "__main__":
	main()
