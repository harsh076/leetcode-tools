# LeetCode Tools

A modular collection of tools for LeetCode problem management with a focus on selecting high-quality problems for interview preparation.

## Features

- **Fetch Problems**: Download problem data from LeetCode
- **Quality Selection**: Select problems based on SQL-defined quality metrics like acceptance rate, frequency, and like ratio
- **Custom SQL**: Use customizable SQL queries to select problems matching your criteria
- **Add to Lists**: Add selected problems to your LeetCode lists
- **Database Storage**: Store problem data locally for fast access

## Prerequisites

### MySQL Database

This tool requires a MySQL database to store and query LeetCode problems. Make sure you have MySQL installed and running on your system:

- **macOS**:
  ```bash
  brew install mysql
  brew services start mysql
  ```

- **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install mysql-server
  sudo systemctl start mysql
  ```

- **Windows**:
  Download and install from [MySQL official site](https://dev.mysql.com/downloads/installer/)

After installation, create a database for LeetCode problems:
```sql
CREATE DATABASE leetcode;
```

You'll need to provide these database credentials when setting up the tool.

## Package Structure

```
leetcode_tools/
├── __init__.py              # Package initialization
├── api/                     # API interaction module
│   ├── __init__.py
│   └── client.py            # LeetCode API client
├── cli/                     # Command-line interface module
│   ├── __init__.py
│   ├── commands.py          # Command implementations
│   ├── main.py              # Entry points
│   └── parser.py            # CLI argument parsing
├── core/                    # Core functionality module
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── database.py          # Database operations
│   └── file.py              # File operations
├── data/                    # Default data files
│   ├── __init__.py
│   ├── Stats.sql            # Default SQL script for problem selection
│   ├── rating_brackets.json # Rating brackets configuration
│   └── topic_weights.json   # Topic weights configuration
└── selector/                # Problem selection module
    ├── __init__.py
    ├── engine.py            # Selection engine
    └── scoring.py           # Problem quality scoring
```

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/leetcode-tools.git
cd leetcode-tools

# Install in development mode
pip install -e .
```

### PyPI

```bash
# Not yet available on PyPI
# pip install leetcode-tools
```

## Configuration

The first time you run any command, a default configuration will be created in your user config directory:
- Linux: `~/.config/leetcode-tools/`
- macOS: `~/Library/Application Support/leetcode-tools/`
- Windows: `C:\Users\<username>\AppData\Local\leetcode-tools\`

### Authentication

Before using the tools, you need to set up your authentication:

1. Get your LeetCode session and CSRF tokens:
   - Log in to LeetCode in your browser
   - Open developer tools (F12)
   - Go to Application/Storage tab
   - Find cookies named "LEETCODE_SESSION" and "csrftoken"

2. Configure authentication:
   ```bash
   leetcode-cli login --session=YOUR_SESSION --csrf=YOUR_CSRF
   ```

### Database Setup

Configure the MySQL database connection:
```bash
leetcode-cli configure-db --host=localhost --user=root --password=yourpassword --database=leetcode
```

## Usage

### Command-line Interfaces

The package provides two main command-line tools:

#### leetcode-cli

General-purpose CLI for all operations:

```bash
# Show help
leetcode-cli help

# Fetch all problems from LeetCode
leetcode-cli fetch

# Update your local database
leetcode-cli update-db

# Select high-quality problems using SQL query
leetcode-cli select-problems [--sql-script=custom.sql] [--count=N] [--output-file=problems.txt] [--list-id=YOUR_LIST_ID]

# Add problems to a LeetCode list
leetcode-cli add-to-list YOUR_LIST_ID --problems-file=problems.txt

# Show current configuration
leetcode-cli config --show

# Set a configuration value
leetcode-cli config --set data_dir /path/to/data
```

#### leetcode-selector

Specialized CLI for problem selection:

```bash
# Select problems using the default SQL query
leetcode-selector 

# Use custom SQL script
leetcode-selector --sql-script=custom.sql

# Save problem slugs to a file
leetcode-selector --output-file=problems.txt

# Add problems directly to a LeetCode list
leetcode-selector --list-id=YOUR_LIST_ID
```

### Custom SQL Queries

The tool uses a SQL query to select high-quality problems. You can customize the selection criteria by:

1. Edit the default SQL script located in your data directory (typically `~/.config/leetcode-tools/Stats.sql`)
2. Provide your own SQL script with the `--sql-script` parameter

The default SQL query assigns a quality score based on:
- Problem rating
- Like/dislike ratio
- Problem frequency
- Acceptance rate
- Company tags (Google problems get bonus points)
- Topic weights
- Difficulty level

You can modify the weights and criteria to match your preparation needs.

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Make sure MySQL is running
   - Verify user credentials and permissions
   - Check that the database exists: `mysql -e "SHOW DATABASES;"`

2. **Authentication Errors**:
   - Ensure your LeetCode session is still valid
   - Refresh cookies by logging out and back in to LeetCode

3. **Import Errors**:
   - If you encounter a "module object is not callable" error, reinstall the package:
     ```bash
     pip uninstall leetcode-tools
     pip install -e .
     ```

## Programmatic Usage

The package can also be used programmatically:

```python
from leetcode_tools.core import ConfigManager, DatabaseManager
from leetcode_tools.api import LeetCodeAPIClient

# Initialize components
config_manager = ConfigManager()
db_manager = DatabaseManager(config_manager.get_db_config())
db_manager.connect()

# Execute custom SQL query
sql_query = """
SELECT id, title, title_slug, difficulty, url
FROM problems
WHERE difficulty = 'Hard' AND status IS NULL
ORDER BY frequency_bar DESC
LIMIT 10
"""
db_manager.cursor.execute(sql_query)
problems = db_manager.cursor.fetchall()

# Process results
for problem in problems:
    print(f"{problem['title']} ({problem['difficulty']}): {problem['url']}")

# Clean up
db_manager.close()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.