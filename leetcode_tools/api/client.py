#!/usr/bin/env python3
import json
import time
import requests
from typing import Dict, List, Tuple, Optional, Any, Callable
from rich.console import Console
from rich.progress import Progress, TaskProgressColumn, TimeRemainingColumn, BarColumn, TextColumn

console = Console()


class LeetCodeAPIClient:
    """Client for interacting with LeetCode API."""

    def __init__(self, session_token: str = "", csrf_token: str = ""):
        """Initialize the API client with authentication tokens."""
        self.session_token = session_token
        self.csrf_token = csrf_token
        self.base_url = "https://leetcode.com"

    def set_auth_tokens(self, session_token: str, csrf_token: str) -> None:
        """Set the authentication tokens."""
        self.session_token = session_token
        self.csrf_token = csrf_token

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication tokens."""
        return {
            "Content-Type": "application/json",
            "Cookie": f"csrftoken={self.csrf_token}; LEETCODE_SESSION={self.session_token}",
            "Referer": "https://leetcode.com/",
            "Origin": "https://leetcode.com",
            "X-CSRFToken": self.csrf_token
        }

    def verify_auth(self) -> Dict[str, Any]:
        """
        Verify that authentication tokens are valid.

        Returns:
            Dictionary with keys:
                - success: Boolean indicating if verification was successful
                - username: Username if successful, None otherwise
                - message: Error message if not successful
        """
        if not self.session_token or not self.csrf_token:
            return {
                "success": False,
                "username": None,
                "message": "Authentication tokens not set"
            }

        # Try to fetch user profile to verify credentials
        url = f"{self.base_url}/graphql"
        query = """
        query {
            userStatus {
                username
                isSignedIn
            }
        }
        """
        payload = {"query": query}

        try:
            response = requests.post(url, json=payload, headers=self.get_headers())
            data = response.json()

            if response.status_code != 200:
                return {
                    "success": False,
                    "username": None,
                    "message": f"API error: {response.status_code}"
                }

            if "data" in data and data["data"]["userStatus"]["isSignedIn"]:
                return {
                    "success": True,
                    "username": data["data"]["userStatus"]["username"],
                    "message": "Authentication successful"
                }
            else:
                return {
                    "success": False,
                    "username": None,
                    "message": "Authentication failed. Please update your session and CSRF tokens."
                }
        except Exception as e:
            return {
                "success": False,
                "username": None,
                "message": f"Error verifying authentication: {str(e)}"
            }

    def fetch_problems(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Dict]:
        """
        Fetch all problems using GraphQL API with pagination and progress indicators.

        Args:
            progress_callback: Optional callback function to report progress

        Returns:
            List of problem dictionaries
        """
        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
            problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
            ) {
                total: totalNum
                questions: data {
                    questionId
                    frontendQuestionId: questionFrontendId
                    title
                    titleSlug
                    difficulty
                    acRate
                    freqBar
                    isFavor
                    paidOnly: isPaidOnly
                    status
                    likes
                    dislikes
                    topicTags {
                        name
                        id
                        slug
                    }
                    companyTags {
                        name
                        slug
                    }
                    hasSolution
                    hasVideoSolution
                    stats
                }
            }
        }
        """

        url = f"{self.base_url}/graphql/"
        limit = 100  # Number of problems per request
        skip = 0
        problems = []
        total_problems = 0

        # Use custom progress tracking or callback
        task_id = None
        progress_obj = None

        # Create a progress bar if no callback is provided
        if progress_callback is None:
            progress_obj = Progress(
                TextColumn("[bold blue]Fetching problems..."),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                transient=False  # This prevents flickering
            )
            progress_obj.start()
            task_id = progress_obj.add_task("[cyan]Downloading...", total=None)

        try:
            while True:
                variables = {
                    "categorySlug": "",
                    "limit": limit,
                    "skip": skip,
                    "filters": {}
                }

                payload = {"query": query, "variables": variables}

                try:
                    response = requests.post(url, json=payload, headers=self.get_headers())
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    if progress_obj:
                        progress_obj.stop()
                    console.print(f"Error fetching problems: {e}", style="red")
                    return []

                data = response.json()
                if "errors" in data:
                    if progress_obj:
                        progress_obj.stop()
                    console.print(f"GraphQL error: {data['errors']}", style="red")
                    return []

                problemset_data = data.get("data", {}).get("problemsetQuestionList", {})
                if not problemset_data:
                    if progress_obj:
                        progress_obj.stop()
                    console.print("No problem data returned from API", style="red")
                    return []

                if not total_problems:
                    total_problems = problemset_data.get("total", 0)
                    if progress_obj and task_id:
                        progress_obj.update(task_id, total=total_problems)
                    elif progress_callback:
                        progress_callback(0, total_problems)

                batch_problems = problemset_data.get("questions", [])
                problems.extend(batch_problems)

                # Update progress
                if progress_obj and task_id:
                    progress_obj.update(task_id, advance=len(batch_problems))
                elif progress_callback:
                    progress_callback(len(problems), total_problems)

                skip += limit

                # Be nice to the server
                time.sleep(1)  # 1-second delay between requests

                if skip >= total_problems or not batch_problems:
                    break

            return problems

        except Exception as e:
            console.print(f"Unexpected error fetching problems: {e}", style="red")
            return []
        finally:
            if progress_obj:
                progress_obj.stop()

    def get_problem_id(self, problem_input: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the problem ID from input.
        If numeric ID is provided, return it directly.
        If slug is provided, convert to ID.

        Returns:
            Tuple of (problem_id, error_message)
        """
        # If the input is numeric, assume it's already a problem ID
        if problem_input.isdigit():
            return problem_input, None

        # Otherwise, it's likely a slug, so we need to get the ID
        problem_slug = problem_input
        url = f"{self.base_url}/graphql"

        # GraphQL query to get problem details by slug
        query = """
        query questionData($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                titleSlug
                title
            }
        }
        """

        variables = {
            "titleSlug": problem_slug
        }

        payload = {
            "query": query,
            "variables": variables
        }

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload)

            if response.status_code == 200:
                result = response.json()
                question = result.get("data", {}).get("question", {})

                if question:
                    return question.get("questionId"), None

                return None, f"Could not find problem with slug {problem_slug}"
            else:
                return None, f"Failed to get problem details: {response.status_code} - {response.text}"
        except Exception as e:
            return None, f"Error getting problem ID: {e}"

    def add_problem_to_list(self, list_id: str, problem_id: str) -> Tuple[bool, str]:
        """
        Add a problem to a LeetCode list using GraphQL API.

        Args:
            list_id: LeetCode favorite list ID
            problem_id: Problem ID to add

        Returns:
            Tuple of (success, message)
        """
        url = f"{self.base_url}/graphql"

        # GraphQL mutation to add a question to a favorite list
        query = """
        mutation addQuestionToFavorite($favoriteIdHash: String!, $questionId: String!) {
            addQuestionToFavorite(favoriteIdHash: $favoriteIdHash, questionId: $questionId) {
                ok
                error
                favoriteIdHash
                questionId
            }
        }
        """

        variables = {
            "favoriteIdHash": list_id,
            "questionId": problem_id
        }

        payload = {
            "query": query,
            "variables": variables
        }

        try:
            response = requests.post(url, headers=self.get_headers(), json=payload)

            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    return False, f"GraphQL Error: {result['errors']}"
                elif result.get("data", {}).get("addQuestionToFavorite", {}).get("ok"):
                    return True, f"Successfully added problem '{problem_id}' to list {list_id}"
                else:
                    error = result.get("data", {}).get("addQuestionToFavorite", {}).get("error", "Unknown error")
                    return False, f"Failed to add problem: {error}"
            else:
                return False, f"Request failed with status code {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Error adding problem to list: {str(e)}"

    def get_rating_dict(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, float]:
        """
        Fetches the rating dictionary from GitHub.

        Args:
            progress_callback: Optional callback function to report progress

        Returns:
            Dictionary mapping problem slugs to ratings
        """
        url = 'https://raw.githubusercontent.com/zerotrac/leetcode_problem_rating/main/ratings.txt'

        try:
            with console.status("[cyan]Fetching problem ratings from GitHub..."):
                response = requests.get(url)

            if response.status_code != 200:
                console.print(f"Failed to fetch rating dictionary: {response.status_code}", style="red")
                return {}

            lines = response.text.splitlines()
            rating_dict = {}

            # Create a progress bar if no callback is provided
            progress_obj = None
            task_id = None

            if progress_callback is None:
                progress_obj = Progress(
                    TextColumn("[bold blue]Processing ratings..."),
                    BarColumn(),
                    TaskProgressColumn(),
                    transient=False  # This prevents flickering
                )
                progress_obj.start()
                task_id = progress_obj.add_task("[cyan]Parsing...", total=len(lines))

            try:
                for i, line in enumerate(lines):
                    fields = line.split('\t')
                    if len(fields) >= 5:
                        slug = fields[4]
                        try:
                            rating = float(fields[0])
                            rating_dict[slug] = rating
                        except ValueError:
                            pass

                    # Update progress
                    if progress_obj and task_id:
                        progress_obj.update(task_id, advance=1)
                    elif progress_callback:
                        progress_callback(i + 1, len(lines))
            finally:
                if progress_obj:
                    progress_obj.stop()

            console.print(f"Loaded {len(rating_dict)} problem ratings", style="green")
            return rating_dict

        except Exception as e:
            console.print(f"Error fetching ratings: {e}", style="red")
            return {}