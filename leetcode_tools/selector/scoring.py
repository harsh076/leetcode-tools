#!/usr/bin/env python3
from typing import Dict, List, Any


def calculate_quality_score(problem: Dict[str, Any], topic_weights: Dict[str, float]) -> float:
    """
    Calculate a quality score based on multiple factors:
    1. Frequency (higher is better)
    2. Acceptance rate (balanced is better)
    3. Like/dislike ratio (higher is better)
    4. Topic importance
    5. Rating (small weight)
    """
    # Extract problem attributes with safe handling of NULL values
    frequency = float(problem.get("frequency_bar", 0)) if problem.get("frequency_bar") is not None else 0
    acceptance = float(problem.get("acceptance_rate", 0)) if problem.get("acceptance_rate") is not None else 0
    likes = int(problem.get("likes", 0)) if problem.get("likes") is not None else 0
    dislikes = int(problem.get("dislikes", 1)) if problem.get("dislikes") is not None else 1  # Avoid division by zero
    like_ratio = likes / dislikes if dislikes > 0 else 0
    difficulty = problem.get("difficulty", "Medium")
    rating = float(problem.get("rating", 0)) if problem.get("rating") is not None else 0
    topics = problem.get("topics", "").split(', ') if problem.get("topics") else []

    # Base score starts with frequency (normalized to 0-100)
    # Higher frequency is better (based on the actual distribution where most problems are under 80)
    freq_score = min(frequency, 80) / 80 * 40  # Max 40 points for frequency

    # Acceptance rate score (optimal range depends on difficulty)
    acc_score = 0
    if difficulty == "Easy":
        # For easy problems, 50-70% acceptance is optimal
        if 50 <= acceptance <= 70:
            acc_score = 20
        elif acceptance < 50:
            acc_score = (acceptance / 50) * 20
        else:  # > 70%
            acc_score = max(0, (90 - acceptance) / 20) * 20
    elif difficulty == "Medium":
        # For medium problems, 40-60% acceptance is optimal
        if 40 <= acceptance <= 60:
            acc_score = 20
        elif acceptance < 40:
            acc_score = (acceptance / 40) * 20
        else:  # > 60%
            acc_score = max(0, (80 - acceptance) / 20) * 20
    else:  # Hard
        # For hard problems, 30-50% acceptance is optimal
        if 30 <= acceptance <= 50:
            acc_score = 20
        elif acceptance < 30:
            acc_score = (acceptance / 30) * 20
        else:  # > 50%
            acc_score = max(0, (70 - acceptance) / 20) * 20

    # Like/dislike ratio score (max 20 points)
    # Based on the distribution data, most problems have ratio < 50
    # Higher ratio is better, capped at 30
    like_score = min(like_ratio, 30) / 30 * 20

    # Topic weight score (max 15 points)
    topic_score = 0
    if topics:
        total_weight = 0
        for topic in topics:
            total_weight += topic_weights.get(topic, 1.0)
        avg_weight = total_weight / len(topics)
        topic_score = min(avg_weight, 1.3) / 1.3 * 15

    # Rating score (small weight - max 5 points)
    # We use the reverse of normalized rating so that a rating closer to the lower bound
    # of the bracket gets a higher score (challenging but not too hard)
    rating_score = 0
    if rating > 0:
        # Normalize rating to 0-5 points, with small weight
        rating_score = min(5, max(0, 5 - abs(rating - 2000) / 200))

    target_companies = ["google", "amazon", "facebook", "microsoft", "apple"]
    companies = problem.get("companies", "").split(', ') if problem.get("companies") else []

    # Company score (max 10 points)
    company_score = 0
    if companies:
        # Give points for each target company tag
        for company in companies:
            company_lower = company.lower()
            if any(target.lower() in company_lower for target in target_companies):
                company_score += 2  # 2 points per target company

        company_score = min(company_score, 10)  # Cap at 10 points

    # Add company_score to total_score
    total_score = freq_score + acc_score + like_score + topic_score + rating_score + company_score

    return total_score