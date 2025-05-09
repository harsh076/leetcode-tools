#!/usr/bin/env python3
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..core.database import DatabaseManager
from .scoring import calculate_quality_score

console = Console()


class ProblemSelector:
    """Selects high-quality LeetCode problems based on various metrics."""

    def __init__(self, db_manager: DatabaseManager, rating_brackets_path: Optional[str] = None,
                 topic_weights_path: Optional[str] = None):
        """
        Initialize with database manager and optional paths to config files.

        Args:
            db_manager: DatabaseManager instance for database operations
            rating_brackets_path: Optional path to rating brackets config file
            topic_weights_path: Optional path to topic weights config file
        """
        self.db_manager = db_manager
        self.rating_brackets = self._load_rating_brackets(rating_brackets_path)
        self.topic_weights = self._load_topic_weights(topic_weights_path)

    def _load_rating_brackets(self, file_path: Optional[str]) -> Dict:
        """Load rating brackets from file or use defaults."""
        default_brackets = {
            "1700-1800": {
                "easy_pct": 20, "medium_pct": 70, "hard_pct": 10,
                "medium_acc": [45, 70], "hard_acc": [30, 45],
                "like_ratio": 5.0, "freq_min": 50
            },
            "1800-1900": {
                "easy_pct": 10, "medium_pct": 65, "hard_pct": 25,
                "medium_acc": [35, 60], "hard_acc": [25, 40],
                "like_ratio": 7.0, "freq_min": 60
            },
            "1900-2000": {
                "easy_pct": 5, "medium_pct": 55, "hard_pct": 40,
                "medium_acc": [30, 50], "hard_acc": [20, 35],
                "like_ratio": 10.0, "freq_min": 70
            },
            "2000-2100": {
                "easy_pct": 0, "medium_pct": 50, "hard_pct": 50,
                "medium_acc": [25, 45], "hard_acc": [15, 30],
                "like_ratio": 15.0, "freq_min": 75
            },
            "2100-2200": {
                "easy_pct": 0, "medium_pct": 40, "hard_pct": 60,
                "medium_acc": [20, 40], "hard_acc": [10, 25],
                "like_ratio": 20.0, "freq_min": 80
            },
            "2200-2300": {
                "easy_pct": 0, "medium_pct": 30, "hard_pct": 70,
                "medium_acc": [15, 35], "hard_acc": [5, 20],
                "like_ratio": 25.0, "freq_min": 85
            },
            "2300-2400": {
                "easy_pct": 0, "medium_pct": 20, "hard_pct": 80,
                "medium_acc": [10, 30], "hard_acc": [0, 15],
                "like_ratio": 30.0, "freq_min": 90
            }
        }

        if not file_path or not os.path.exists(file_path):
            return default_brackets

        try:
            with open(file_path, 'r') as f:
                brackets = json.load(f)

                # Convert lists to tuples for consistency
                for bracket in brackets.values():
                    if "medium_acc" in bracket and isinstance(bracket["medium_acc"], list):
                        bracket["medium_acc"] = tuple(bracket["medium_acc"])
                    if "hard_acc" in bracket and isinstance(bracket["hard_acc"], list):
                        bracket["hard_acc"] = tuple(bracket["hard_acc"])

                return brackets
        except Exception as e:
            console.print(f"Error loading rating brackets: {e}", style="red")
            return default_brackets

    def _load_topic_weights(self, file_path: Optional[str]) -> Dict:
        """Load topic weights from file or use defaults."""
        # Default topic weights for senior backend roles
        default_weights = {
            # Core Data Structures - Critical
            "Array": 1.5,
            "Hash Table": 1.5,
            "Linked List": 1.3,
            "Tree": 1.4,
            "Binary Tree": 1.4,
            "Binary Search Tree": 1.3,
            "Heap (Priority Queue)": 1.4,
            "Stack": 1.3,
            "Queue": 1.3,
            "Graph": 1.5,

            # Core Algorithms - Critical
            "Dynamic Programming": 1.5,
            "Binary Search": 1.5,
            "Depth-First Search": 1.5,
            "Breadth-First Search": 1.5,
            "Two Pointers": 1.4,
            "Sliding Window": 1.4,
            "Backtracking": 1.3,
            "Greedy": 1.4,
            "Sorting": 1.3,

            # System Design Related - Very Important for L5+
            "Design": 1.6,
            "Data Stream": 1.5,
            "Iterator": 1.3,
            "Concurrency": 1.5,

            # Advanced Data Structures - Important for L5+
            "Trie": 1.4,
            "Union Find": 1.4,
            "Segment Tree": 1.4,
            "Binary Indexed Tree": 1.4,
            "Monotonic Stack": 1.3,
            "Monotonic Queue": 1.3,

            # Medium & Low Priority Topics (truncated for brevity)
            "String": 1.3,
            "Math": 1.2,
            "Bit Manipulation": 1.2,
        }

        if not file_path or not os.path.exists(file_path):
            return default_weights

        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"Error loading topic weights: {e}", style="red")
            return default_weights

    def get_quality_problems(self, rating_bracket: str, difficulty: str, count: int) -> List[Dict]:
        """Get high-quality problems for a specific rating bracket and difficulty."""
        if rating_bracket not in self.rating_brackets:
            console.print(f"Invalid rating bracket: {rating_bracket}", style="red")
            return []

        bracket_config = self.rating_brackets[rating_bracket]

        # Determine acceptance rate range based on difficulty
        if difficulty == "Easy":
            acc_range = (0, 100)  # No specific constraints for Easy
        elif difficulty == "Medium":
            acc_range = bracket_config["medium_acc"]
        else:  # Hard
            acc_range = bracket_config["hard_acc"]

        # Fetch problems from database based on criteria
        problems = self.db_manager.get_quality_problems(
            difficulty=difficulty,
            acc_range=acc_range,
            freq_min=bracket_config["freq_min"],
            like_ratio_min=bracket_config["like_ratio"],
            count=count * 2  # Fetch more than needed to allow for filtering
        )

        # Calculate quality score for each problem
        for problem in problems:
            problem["quality_score"] = calculate_quality_score(problem, self.topic_weights)

        # Sort by quality score and return top N
        problems.sort(key=lambda x: x["quality_score"], reverse=True)
        return problems[:count]

    def generate_problem_list(self, rating_bracket: str, problem_count: int) -> Dict:
        """Generate a list of problems for a specific rating bracket."""
        if rating_bracket not in self.rating_brackets:
            console.print(f"Invalid rating bracket: {rating_bracket}", style="red")
            return {}

        bracket_config = self.rating_brackets[rating_bracket]

        # Calculate problem counts by difficulty
        easy_count = int(problem_count * bracket_config["easy_pct"] / 100)
        medium_count = int(problem_count * bracket_config["medium_pct"] / 100)
        hard_count = int(problem_count * bracket_config["hard_pct"] / 100)

        # Ensure we have at least the specified total number of problems
        total = easy_count + medium_count + hard_count
        if total < problem_count:
            # Distribute the difference to medium and hard problems
            diff = problem_count - total
            if medium_count > 0:
                medium_count += diff // 2
                hard_count += diff - (diff // 2)
            else:
                hard_count += diff

        # Fetch problems for each difficulty
        easy_problems = self.get_quality_problems(rating_bracket, "Easy", easy_count) if easy_count > 0 else []
        medium_problems = self.get_quality_problems(rating_bracket, "Medium", medium_count) if medium_count > 0 else []
        hard_problems = self.get_quality_problems(rating_bracket, "Hard", hard_count) if hard_count > 0 else []

        return {
            "rating_bracket": rating_bracket,
            "total_count": len(easy_problems) + len(medium_problems) + len(hard_problems),
            "easy": easy_problems,
            "medium": medium_problems,
            "hard": hard_problems
        }

    def display_problem_list(self, problems_by_difficulty: Dict) -> None:
        """Display the generated problem list in a formatted table."""
        if not problems_by_difficulty:
            console.print("No problems to display", style="yellow")
            return

        rating_bracket = problems_by_difficulty["rating_bracket"]
        total_count = problems_by_difficulty["total_count"]

        # Create header
        console.print(Panel.fit(
            f"[bold yellow]LeetCode Problem List for Rating Bracket: {rating_bracket}[/bold yellow]\n"
            f"Total Problems: {total_count}",
            title="LeetCode Quality Problem Selector",
            border_style="green"
        ))

        # Display problems by difficulty
        for difficulty in ["easy", "medium", "hard"]:
            problems = problems_by_difficulty[difficulty]
            if not problems:
                continue

            table = Table(title=f"{difficulty.capitalize()} Problems ({len(problems)})")
            table.add_column("Title", style="cyan")
            table.add_column("Quality Score", style="green", justify="right")
            table.add_column("Frequency", justify="right")
            table.add_column("Acceptance", justify="right")
            table.add_column("Like Ratio", justify="right")
            table.add_column("Topics", style="yellow", width=40)
            table.add_column("Companies", style="magenta", width=40)
            table.add_column("URL", style="blue")

            for problem in problems:
                table.add_row(
                    problem.get("title", "") if "title" in problem else problem.get("title_slug", "").replace("-",
                                                                                                              " ").title(),
                    f"{problem.get('quality_score', 0):.2f}",
                    f"{problem.get('frequency_bar', 'N/A')}",
                    f"{problem.get('acceptance_rate', 'N/A')}%" if problem.get('acceptance_rate') else "N/A",
                    f"{problem.get('like_ratio', 'N/A'):.1f}" if problem.get('like_ratio') else "N/A",
                    problem.get("topics", "")[:30] + ("..." if len(problem.get("topics", "")) > 30 else ""),
                    problem.get("companies", "")[:30] + ("..." if len(problem.get("companies", "")) > 30 else ""),
                    problem.get("url", "")
                )

            console.print(table)
            console.print("\n")

    def save_to_file(self, problems_by_difficulty: Dict, file_path: str) -> None:
        """Save the problem list to a file for later use."""
        try:
            # Check if file_path is empty or None
            if not file_path:
                console.print("Error: Output file path is empty or None", style="red")
                return

            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory:  # Only create directory if there's a directory path
                os.makedirs(directory, exist_ok=True)

            # Check if problems_by_difficulty is valid
            if not problems_by_difficulty or not isinstance(problems_by_difficulty, dict):
                console.print("Error: Invalid problem data", style="red")
                return

            with open(file_path, 'w') as f:
                for difficulty in ["easy", "medium", "hard"]:
                    if difficulty in problems_by_difficulty:
                        for problem in problems_by_difficulty[difficulty]:
                            if "title_slug" in problem:
                                f.write(f"{problem['title_slug']}\n")

            console.print(f"✅ Saved {problems_by_difficulty['total_count']} problems to {file_path}", style="green")
        except Exception as e:
            console.print(f"Error saving problems to file: {e}", style="red")