#!/usr/bin/env python3
import json
import csv
import os
from typing import Dict, List, Any, Optional
from rich.console import Console

console = Console()


class FileManager:
    """Manages file operations for LeetCode problems."""

    @staticmethod
    def save_to_json(data: Any, filepath: str) -> bool:
        """Save data to a JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            console.print(f"Saved data to {filepath}", style="green")
            return True
        except Exception as e:
            console.print(f"Error saving to JSON file: {e}", style="red")
            return False

    @staticmethod
    def load_from_json(filepath: str) -> Optional[Any]:
        """Load data from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"Error loading from JSON file: {e}", style="red")
            return None

    @staticmethod
    def convert_problems_to_csv(problems: List[Dict], csv_file: str) -> bool:
        """Convert problems data to CSV with additional fields."""
        # Define CSV headers with new fields
        headers = [
            "questionId", "frontendQuestionId", "title", "titleSlug", "difficulty",
            "acRate", "totalSubmissions", "likes", "dislikes", "topicTags",
            "isFavor", "paidOnly", "status", "hasSolution", "hasVideoSolution", "freqBar"
        ]

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)

            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for problem in problems:
                    # Parse stats if needed
                    stats = {}
                    if "stats" in problem and problem["stats"]:
                        try:
                            if isinstance(problem["stats"], str):
                                stats = json.loads(problem["stats"])
                            else:
                                stats = problem["stats"]
                        except json.JSONDecodeError:
                            stats = {}

                    # Extract topic tags
                    topic_tags = ", ".join(tag["name"] for tag in problem.get("topicTags", []) if "name" in tag)

                    # Create the row with defaults for missing fields
                    row = {
                        "questionId": problem.get("questionId", "N/A"),
                        "frontendQuestionId": problem.get("frontendQuestionId", "N/A"),
                        "title": problem.get("title", "N/A"),
                        "titleSlug": problem.get("titleSlug", "N/A"),
                        "difficulty": problem.get("difficulty", "N/A"),
                        "acRate": problem.get("acRate", "N/A"),
                        "totalSubmissions": stats.get("totalSubmissionRaw", "N/A"),
                        "likes": problem.get("likes", "N/A"),
                        "dislikes": problem.get("dislikes", "N/A"),
                        "topicTags": topic_tags,
                        "isFavor": problem.get("isFavor", False),
                        "paidOnly": problem.get("paidOnly", False),
                        "status": problem.get("status", "N/A"),
                        "hasSolution": problem.get("hasSolution", False),
                        "hasVideoSolution": problem.get("hasVideoSolution", False),
                        "freqBar": problem.get("freqBar", "N/A")
                    }
                    writer.writerow(row)

            console.print(f"Converted problems to {csv_file}", style="green")
            return True
        except Exception as e:
            console.print(f"Error converting to CSV: {e}", style="red")
            return False

    @staticmethod
    def load_problem_slugs(filepath: str) -> List[str]:
        """Load problem slugs or IDs from a file."""
        try:
            with open(filepath, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            console.print(f"Error loading problems from file: {e}", style="red")
            return []

    @staticmethod
    def save_problem_slugs(problems: List[Dict], filepath: str) -> bool:
        """Save problem slugs to a file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w') as f:
                for problem in problems:
                    if "titleSlug" in problem:
                        f.write(f"{problem['titleSlug']}\n")

            console.print(f"Saved {len(problems)} problem slugs to {filepath}", style="green")
            return True
        except Exception as e:
            console.print(f"Error saving problem slugs: {e}", style="red")
            return False