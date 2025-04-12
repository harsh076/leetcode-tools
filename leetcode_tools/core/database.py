#!/usr/bin/env python3
import json
import mysql.connector
from mysql.connector import pooling
from typing import Dict, List, Optional, Tuple, Any
from rich.console import Console

console = Console()


class DatabaseManager:
    """Database manager for LeetCode problems."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with database configuration."""
        self.config = config
        self.conn = None
        self.cursor = None
        self.pool = None

        # Setup connection pooling
        try:
            pool_config = self.config.copy()
            pool_config['pool_name'] = 'leetcode_pool'
            pool_config['pool_size'] = 5
            self.pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
        except mysql.connector.Error as e:
            console.print(f"Error creating connection pool: {e}", style="red")
            self.pool = None

    def connect(self) -> bool:
        """Connect to the database."""
        try:
            if self.pool:
                self.conn = self.pool.get_connection()
            else:
                self.conn = mysql.connector.connect(**self.config)

            self.cursor = self.conn.cursor(dictionary=True)
            console.print("Connected to database successfully", style="green")
            return True
        except mysql.connector.Error as e:
            console.print(f"Database connection error: {e}", style="red")
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        console.print("Database connection closed", style="green")

    def create_tables(self) -> bool:
        """Create the necessary database tables."""
        if not self.cursor:
            if not self.connect():
                return False

        # Create the main problems table
        create_problems = """
        CREATE TABLE IF NOT EXISTS problems (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_id VARCHAR(20) UNIQUE NOT NULL,
            frontend_question_id VARCHAR(20) NOT NULL,
            acceptance_rate DECIMAL(5,2) NOT NULL,
            difficulty ENUM('Easy', 'Medium', 'Hard') NOT NULL,
            frequency_bar DECIMAL(5,2),
            rating DECIMAL(6,2),
            status ENUM('ac', 'notac') DEFAULT NULL,
            likes INT DEFAULT 0,
            dislikes INT DEFAULT 0,
            title VARCHAR(255) NOT NULL,
            title_slug VARCHAR(255) NOT NULL,
            url VARCHAR(255) NOT NULL,
            has_solution BOOLEAN NOT NULL DEFAULT FALSE,
            has_video_solution BOOLEAN DEFAULT FALSE,
            is_favor BOOLEAN DEFAULT FALSE,
            paid_only BOOLEAN DEFAULT FALSE,
            total_accepted INT NOT NULL,
            total_submission INT NOT NULL,
            ac_rate_percentage DECIMAL(5,2) NOT NULL
        )
        """

        # Create the topics table
        create_topics = """
        CREATE TABLE IF NOT EXISTS topics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            topic_id VARCHAR(50) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            UNIQUE KEY (topic_id)
        )
        """

        # Create the problem_topics relation table
        create_problem_topics = """
        CREATE TABLE IF NOT EXISTS problem_topics (
            problem_id INT NOT NULL,
            topic_id INT NOT NULL,
            PRIMARY KEY (problem_id, topic_id),
            FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
        """

        try:
            self.cursor.execute(create_problems)
            self.cursor.execute(create_topics)
            self.cursor.execute(create_problem_topics)
            return True
        except mysql.connector.Error as e:
            console.print(f"Error creating tables: {e}", style="red")
            return False

    def get_problem_id(self, question_id: str) -> Optional[int]:
        """Get the problem ID by question_id"""
        if not self.cursor:
            if not self.connect():
                return None

        query = "SELECT id FROM problems WHERE question_id = %s"
        try:
            self.cursor.execute(query, (question_id,))
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except mysql.connector.Error as e:
            console.print(f"Error getting problem ID: {e}", style="red")
            return None

    def get_topic_id(self, topic_id: str) -> Optional[int]:
        """Get the topic ID by topic_id"""
        if not self.cursor:
            if not self.connect():
                return None

        query = "SELECT id FROM topics WHERE topic_id = %s"
        try:
            self.cursor.execute(query, (topic_id,))
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except mysql.connector.Error as e:
            console.print(f"Error getting topic ID: {e}", style="red")
            return None

    def update_problem(self, problem: Dict[str, Any]) -> bool:
        """Update a single problem in the database."""
        if not self.cursor:
            if not self.connect():
                return False

        # SQL for problems table
        problem_sql = """
        INSERT INTO problems (
            question_id, frontend_question_id, acceptance_rate, difficulty, frequency_bar, 
            rating, status, likes, dislikes, title, title_slug, url, has_solution, 
            has_video_solution, is_favor, paid_only, total_accepted, 
            total_submission, ac_rate_percentage
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            frontend_question_id = VALUES(frontend_question_id),
            acceptance_rate = VALUES(acceptance_rate),
            difficulty = VALUES(difficulty),
            frequency_bar = VALUES(frequency_bar),
            rating = VALUES(rating),
            status = VALUES(status),
            likes = VALUES(likes),
            dislikes = VALUES(dislikes),
            title = VALUES(title),
            title_slug = VALUES(title_slug),
            url = VALUES(url),
            has_solution = VALUES(has_solution),
            has_video_solution = VALUES(has_video_solution),
            is_favor = VALUES(is_favor),
            paid_only = VALUES(paid_only),
            total_accepted = VALUES(total_accepted),
            total_submission = VALUES(total_submission),
            ac_rate_percentage = VALUES(ac_rate_percentage)
        """

        # SQL for topics table
        topic_sql = """
        INSERT IGNORE INTO topics (name, topic_id, slug)
        VALUES (%s, %s, %s)
        """

        # SQL for problem_topics table
        problem_topic_sql = """
        INSERT IGNORE INTO problem_topics (problem_id, topic_id)
        VALUES (%s, %s)
        """

        try:
            # Parse the stats JSON string if it's a string
            stats = problem.get("stats", "{}")
            if isinstance(stats, str):
                try:
                    stats = json.loads(stats)
                except json.JSONDecodeError:
                    stats = {}

            # Extract stats fields with safe defaults
            total_accepted = int(stats.get("totalAcceptedRaw", 0))
            total_submission = int(stats.get("totalSubmissionRaw", 0))

            # Handle ac_rate parsing
            ac_rate_percentage = problem.get("acRate", 0)
            if isinstance(ac_rate_percentage, str):
                ac_rate_percentage = ac_rate_percentage.strip('%')
                try:
                    ac_rate_percentage = float(ac_rate_percentage)
                except ValueError:
                    ac_rate_percentage = 0.0

            # Prepare problem data with safe defaults
            problem_data = (
                problem.get("questionId", ""),
                problem.get("frontendQuestionId", ""),
                float(problem.get("acRate", 0)),
                problem.get("difficulty", "Medium"),
                problem.get("freqBar", 0),
                float(problem.get("rating", 0.0)),
                problem.get("status", None),
                int(problem.get("likes", 0)),
                int(problem.get("dislikes", 0)),
                problem.get("title", ""),
                problem.get("titleSlug", ""),
                f"https://leetcode.com/problems/{problem.get('titleSlug', '')}/description/",
                bool(problem.get("hasSolution", False)),
                bool(problem.get("hasVideoSolution", False)),
                bool(problem.get("isFavor", False)),
                bool(problem.get("paidOnly", False)),
                total_accepted,
                total_submission,
                float(ac_rate_percentage)
            )

            self.cursor.execute(problem_sql, problem_data)
            problem_id = self.cursor.lastrowid or self.get_problem_id(problem.get("questionId", ""))

            if not problem_id:
                console.print(f"Warning: Couldn't get problem ID for {problem.get('title', '')}", style="yellow")
                return False

            # Handle topic tags
            if "topicTags" in problem and problem["topicTags"]:
                # Insert topics
                for topic in problem["topicTags"]:
                    if not all(k in topic for k in ["name", "id", "slug"]):
                        continue

                    topic_data = (
                        topic["name"],
                        topic["id"],
                        topic["slug"]
                    )
                    self.cursor.execute(topic_sql, topic_data)
                    topic_id = self.cursor.lastrowid or self.get_topic_id(topic["id"])

                    if topic_id:
                        # Link problem with topic
                        self.cursor.execute(problem_topic_sql, (problem_id, topic_id))

            self.conn.commit()
            return True

        except mysql.connector.Error as e:
            console.print(f"Error updating problem {problem.get('title')}: {e}", style="red")
            self.conn.rollback()
            return False

    def get_quality_problems(self, difficulty: str, acc_range: Tuple[int, int],
                             freq_min: int, like_ratio_min: float, count: int) -> List[Dict]:
        """
        Get high-quality problems for a specific difficulty level and criteria.

        Args:
            difficulty: "Easy", "Medium", or "Hard"
            acc_range: Tuple of (min, max) acceptance rate percentage
            freq_min: Minimum frequency bar
            like_ratio_min: Minimum likes to dislikes ratio
            count: Maximum number of problems to return

        Returns:
            List of problem dictionaries that match the criteria
        """
        if not self.cursor:
            if not self.connect():
                return []

        query = """
        SELECT 
            p.id, p.title_slug, p.url, p.status, p.acceptance_rate, p.frequency_bar,
            ROUND(p.likes/NULLIF(p.dislikes, 0), 2) AS like_ratio,
            GROUP_CONCAT(t.name SEPARATOR ', ') AS topics,
            p.likes, p.dislikes, p.rating, p.title
        FROM 
            problems p
        JOIN 
            problem_topics pt ON p.id = pt.problem_id
        JOIN 
            topics t ON pt.topic_id = t.id
        WHERE 
            p.difficulty = %s
            AND (p.status IS NULL OR p.status != 'ac')
            AND p.acceptance_rate BETWEEN %s AND %s
            AND p.frequency_bar >= %s
            AND p.likes/NULLIF(p.dislikes, 0) >= %s
        GROUP BY 
            p.id
        ORDER BY 
            p.frequency_bar DESC, p.acceptance_rate DESC
        """

        params = (
            difficulty,
            acc_range[0],
            acc_range[1],
            freq_min,
            like_ratio_min
        )

        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            console.print(f"Error fetching problems: {e}", style="red")
            return []