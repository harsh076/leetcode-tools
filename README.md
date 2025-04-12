# LeetCode Tools

A modular collection of tools for LeetCode problem management with a focus on selecting high-quality problems for interview preparation.

## Features

- **Fetch Problems**: Download problem data from LeetCode
- **Quality Selection**: Select problems based on quality metrics like acceptance rate, frequency, and like ratio
- **Rating-Based**: Target problems matching your current rating level
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

# Select high-quality problems for rating bracket 1900-2000
leetcode-cli select-problems 1900-2000 100 --output=problems.txt --display

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
# Select problems for rating bracket 2000-2100
leetcode-selector 2000-2100 50 --output=problems.txt --display

# Use custom rating brackets and topic weights
leetcode-selector 1900-2000 100 --output=problems.txt --rating-brackets=custom_brackets.json --topic-weights=custom_weights.json
```

### Rating Brackets

The default rating brackets are configured for different skill levels:

| Bracket | Easy % | Medium % | Hard % | Focus Areas |
|---------|--------|----------|--------|-------------|
| 1700-1800 | 20 | 70 | 10 | Fundamentals |
| 1800-1900 | 10 | 65 | 25 | Medium-level |
| 1900-2000 | 5 | 55 | 40 | Advanced algorithms |
| 2000-2100 | 0 | 50 | 50 | Hard problems |
| 2100-2200 | 0 | 40 | 60 | System design |
| 2200-2300 | 0 | 30 | 70 | Advanced topics |
| 2300-2400 | 0 | 20 | 80 | Expert level |

You can customize the brackets by creating your own JSON file and specifying it with `--rating-brackets`.

### Topic Weights

Topics are weighted based on their importance for senior backend roles:

- Critical topics (weight 1.5-1.6): Graph, Dynamic Programming, Binary Search, Design
- Important topics (weight 1.3-1.4): Trees, Arrays, Hash Tables, Heap
- Medium importance (weight 1.2): Math, Matrix, Bit Manipulation
- Lower importance (weight 0.8-1.1): Shell, Database, Game Theory

You can customize the weights by creating your own JSON file and specifying it with `--topic-weights`.

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
from leetcode_tools.selector import ProblemSelector

# Initialize components
config_manager = ConfigManager()
db_manager = DatabaseManager(config_manager.get_db_config())
db_manager.connect()

# Select problems
selector = ProblemSelector(db_manager)
problems = selector.generate_problem_list("1900-2000", 100)

# Display and save
selector.display_problem_list(problems)
selector.save_to_file(problems, "problems.txt")

# Clean up
db_manager.close()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.