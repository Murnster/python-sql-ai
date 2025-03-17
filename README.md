# MySQL AI with Python and Ollama

## Description
This WIP project is a simple python script that connects to a DB and an Ollama instance to generate
an SQL query, fetch results from DB, and return the results. Accuracy depends on LLM!

## Features
- Uses an LLM through Ollama to generate an SQL query with a constructed prompt with the DB schema
- Analyzes results to output in a human readable response
- Supports NFL statistics queries

## Example Usage
```bash
Enter your NFL analysis question (or 'quit' to exit): How many games did the Patriots win in the 2024 NFL season?

Beginning analysis...

Generated query: SELECT COUNT(*) FROM games WHERE nfl_team_name_winner = 'Patriots' AND season = 2024;

Executing query...
Sending results to Ollama for analysis...

Analysis:
The Patriots won 4 games in the 2024 NFL season.
```

## Prerequisites
- Python 3.8+
- MySQL Server
- Ollama installed and running
- Required Python packages (see Installation)

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/mysql-ai-script.git
cd mysql-ai-script

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

## Database Setup
1. Create a MySQL database named `nfl_games`
2. Run the schema creation script:
```bash
mysql -u username -p nfl_games < tables.sql
```
3. Populate data using either:
   - [nfl_data_py](https://github.com/nflverse/nfl_data_py)
   - [nflscraPy](https://github.com/blnkpagelabs/nflscraPy)

## Usage
```bash
# Start Ollama (if not running)
systemctl start ollama

# Run the script
python mysql-ai.py
```

Example queries:
- "How many games did the Eagles win in 2023?"
- "What was the average rushing yards for the Chiefs in 2024?"
- "Show me all games where the Bills scored over 30 points"

## Configuration
The script can be configured through environment variables:
- `DB_HOST`: MySQL host (default: localhost)
- `DB_USER`: Database username
- `DB_PASS`: Database password
- `DB_NAME`: Database name (default: nfl_games)
- `OLLAMA_MODEL`: LLM model to use (default: qwen2.5-coder:14b)

## Contact
Developed by [Ryan Murney](https://ryanmurney.ca)

## Acknowledgments
- NFL data providers: nfl_data_py and nflscraPy

## Project Status
Currently a WIP side project for fun:
- Query complexity is limited by whichever LLM you use and or database complexity, can halluciante massively