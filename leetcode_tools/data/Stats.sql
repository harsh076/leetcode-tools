-- LeetCode Problem Quality Score Query with Adjustable Weights
-- Designed for Google L5+ Backend Engineer Preparation

-- Configuration Section: Adjust weights here
WITH config AS (
    SELECT
        -- Main score component weights (should sum to 100)

        55 AS weight_rating,           -- Weight for problem rating
        10 AS weight_like_ratio,       -- Weight for like/dislike ratio
        10 AS weight_frequency,        -- Weight for problem frequency
        7 AS weight_acceptance,        -- Weight for acceptance rate
        8 AS weight_company,           -- Weight for company tags
        8 AS weight_topic,             -- Weight for topic relevance
        2 AS weight_difficulty,        -- Weight for problem difficulty

        -- Frequency thresholds
        90 AS max_frequency,           -- Maximum frequency to consider (for normalization)

        -- Acceptance rate optimal ranges by difficulty
        50 AS easy_acc_min,            -- Easy: Optimal min acceptance
        70 AS easy_acc_max,            -- Easy: Optimal max acceptance

        35 AS medium_acc_min,          -- Medium: Optimal min acceptance
        60 AS medium_acc_max,          -- Medium: Optimal max acceptance

        25 AS hard_acc_min,            -- Hard: Optimal min acceptance
        45 AS hard_acc_max,            -- Hard: Optimal max acceptance

        -- Like ratio parameters
        10 AS max_like_ratio,          -- Maximum like ratio to consider (for normalization)

        -- Rating parameters
        1500 AS target_rating,         -- Target rating (problems closer to this get higher score)
        85 AS rating_scale,           -- Scale factor for rating difference

        -- Difficulty bonus points
        0 AS easy_bonus,               -- Bonus points for Easy problems
        0 AS medium_bonus,             -- Bonus points for Medium problems
        0 AS hard_bonus,              -- Bonus points for Hard problems

        -- Company tag bonus parameters
        1.0 AS google_bonus,           -- Bonus multiplier for Google problems (not points)
        0.7 AS other_faang_bonus,      -- Multiplier per other FAANG company tag

        -- Topic weights (adjust based on your focus areas)
        1.5 AS weight_critical_ds,     -- Weight for critical data structures
        1.5 AS weight_critical_algo,   -- Weight for critical algorithms
        1.4 AS weight_important_ds,    -- Weight for important data structures
        1.4 AS weight_important_algo,  -- Weight for important algorithms
        1.4 AS weight_advanced_ds,     -- Weight for advanced data structures
        1.3 AS weight_medium_topics,   -- Weight for medium-priority topics
        1.3 AS weight_system_design,   -- Weight for system design topics
        1.2 AS weight_low_topics,      -- Weight for low-priority topics
        1.0 AS weight_other_topics     -- Weight for other topics
),

-- Topic weights mapping
topic_weights AS (
    SELECT
        t.id,
        t.name,
        CASE
            -- Critical Data Structures
            WHEN t.name IN ('Array', 'Hash Table', 'Graph')
                THEN (SELECT weight_critical_ds FROM config)

            -- Important Data Structures
            WHEN t.name IN ('Linked List', 'Tree', 'Binary Tree', 'Binary Search Tree',
                           'Heap (Priority Queue)', 'Stack', 'Queue')
                THEN (SELECT weight_important_ds FROM config)

            -- Critical Algorithms
            WHEN t.name IN ('Dynamic Programming', 'Binary Search', 'Depth-First Search',
                           'Breadth-First Search')
                THEN (SELECT weight_critical_algo FROM config)

            -- Important Algorithms
            WHEN t.name IN ('Two Pointers', 'Sliding Window', 'Greedy', 'Backtracking', 'Sorting')
                THEN (SELECT weight_important_algo FROM config)

            -- System Design Related
            WHEN t.name IN ('Design', 'Data Stream', 'Concurrency')
                THEN (SELECT weight_system_design FROM config)
            WHEN t.name = 'Iterator'
                THEN (SELECT weight_medium_topics FROM config)

            -- Advanced Data Structures
            WHEN t.name IN ('Trie', 'Union Find', 'Segment Tree', 'Binary Indexed Tree',
                           'Monotonic Stack', 'Monotonic Queue')
                THEN (SELECT weight_advanced_ds FROM config)

            -- Medium Priority Topics
            WHEN t.name = 'String'
                THEN (SELECT weight_medium_topics FROM config)

            -- Low Priority Topics
            WHEN t.name IN ('Math', 'Bit Manipulation')
                THEN (SELECT weight_low_topics FROM config)

            -- Other Topics
            ELSE (SELECT weight_other_topics FROM config)
        END AS weight
    FROM topics t
),

-- Pre-calculate component scores for each problem to avoid GROUP BY issues
problem_scores AS (
    SELECT
        p.id,
        p.title,
        p.title_slug,
        p.url,
        p.difficulty,
        p.acceptance_rate,
        p.frequency_bar,
        CASE WHEN p.dislikes > 0 THEN ROUND(p.likes/p.dislikes, 2) ELSE p.likes END AS like_ratio,
        p.rating,

        -- 1. Frequency score
        ROUND(COALESCE(LEAST(p.frequency_bar, c.max_frequency) / c.max_frequency * c.weight_frequency,
               c.weight_frequency * 0.375), 2) AS freq_score,

        -- 2. Acceptance rate score
        ROUND(CASE
            WHEN p.difficulty = 'Easy' THEN
                CASE
                    WHEN p.acceptance_rate BETWEEN c.easy_acc_min AND c.easy_acc_max THEN c.weight_acceptance
                    WHEN p.acceptance_rate < c.easy_acc_min THEN (p.acceptance_rate / c.easy_acc_min) * c.weight_acceptance
                    ELSE GREATEST(0, (90 - p.acceptance_rate) / 20) * c.weight_acceptance
                END
            WHEN p.difficulty = 'Medium' THEN
                CASE
                    WHEN p.acceptance_rate BETWEEN c.medium_acc_min AND c.medium_acc_max THEN c.weight_acceptance
                    WHEN p.acceptance_rate < c.medium_acc_min THEN (p.acceptance_rate / c.medium_acc_min) * c.weight_acceptance
                    ELSE GREATEST(0, (80 - p.acceptance_rate) / 20) * c.weight_acceptance
                END
            ELSE -- Hard
                CASE
                    WHEN p.acceptance_rate BETWEEN c.hard_acc_min AND c.hard_acc_max THEN c.weight_acceptance
                    WHEN p.acceptance_rate < c.hard_acc_min THEN (p.acceptance_rate / c.hard_acc_min) * c.weight_acceptance
                    ELSE GREATEST(0, (70 - p.acceptance_rate) / 20) * c.weight_acceptance
                END
        END, 2) AS acc_score,

        -- 3. Like ratio score
        ROUND(LEAST(CASE WHEN p.dislikes > 0 THEN p.likes/p.dislikes ELSE p.likes END, c.max_like_ratio)
              / c.max_like_ratio * c.weight_like_ratio, 2) AS like_score,

        -- 5. Rating score using Gaussian distribution
        ROUND(c.weight_rating *
              EXP(-(POW(p.rating - c.target_rating, 2) / (2 * POW(c.rating_scale, 2)))), 2) AS rating_score,

        -- 6. Difficulty bonus
        CASE
            WHEN p.difficulty = 'Easy' THEN c.easy_bonus
            WHEN p.difficulty = 'Medium' THEN c.medium_bonus
            ELSE c.hard_bonus -- Hard
        END AS diff_bonus,

        -- Store config values needed for final calculation
        c.weight_topic,
        (SELECT MAX(weight_critical_ds) FROM config) AS max_topic_weight
    FROM
        problems p
    CROSS JOIN
        config c
    WHERE
        (p.status IS NULL OR p.status != 'ac')
),

-- Pre-calculate topic scores
topic_scores AS (
    SELECT
        pt.problem_id,
        AVG(tw.weight) AS avg_topic_weight
    FROM
        problem_topics pt
    JOIN
        topic_weights tw ON pt.topic_id = tw.id
    GROUP BY
        pt.problem_id
),

-- Pre-calculate company scores
company_scores AS (
    SELECT
        pc.problem_id,
        (SELECT weight_company FROM config) *
        CASE
            WHEN COUNT(*) > 0 AND MAX(CASE WHEN c.name = 'Google' THEN 1 ELSE 0 END) = 1
                THEN (SELECT google_bonus FROM config)
            WHEN COUNT(*) > 0
                THEN LEAST(COUNT(*) * (SELECT other_faang_bonus FROM config), 0.8)
            ELSE 0
        END AS company_score
    FROM
        problem_companies pc
    JOIN
        companies c ON pc.company_id = c.id
    WHERE
        c.name IN ('Google', 'Facebook', 'Amazon', 'Apple', 'Microsoft', 'Netflix')
    GROUP BY
        pc.problem_id
)

-- Main Query
SELECT
    ps.id,
    ps.title,
    ps.title_slug,
    ps.url,
    ps.difficulty,
    ps.acceptance_rate,
    ps.frequency_bar,
    ps.like_ratio,
    ps.rating,

    -- Component scores
    ps.freq_score,
    ps.acc_score,
    ps.like_score,
    ROUND(COALESCE(ts.avg_topic_weight / ps.max_topic_weight * ps.weight_topic, ps.weight_topic * 0.667), 2) AS topic_score,
    ps.rating_score,
    ps.diff_bonus,
    COALESCE(cs.company_score, 0) AS company_score,

    -- Total quality score
    (
        ps.freq_score +
        ps.acc_score +
        ps.like_score +
        ROUND(COALESCE(ts.avg_topic_weight / ps.max_topic_weight * ps.weight_topic, ps.weight_topic * 0.667), 2) +
        ps.rating_score +
        ps.diff_bonus +
        COALESCE(cs.company_score, 0)
    ) AS quality_score,

    -- Additional reference fields
    (SELECT GROUP_CONCAT(DISTINCT t.name ORDER BY tw.weight DESC SEPARATOR ', ')
     FROM problem_topics pt
     JOIN topics t ON pt.topic_id = t.id
     JOIN topic_weights tw ON t.id = tw.id
     WHERE pt.problem_id = ps.id) AS topics,

    (SELECT GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ')
     FROM problem_companies pc
     JOIN companies c ON pc.company_id = c.id
     WHERE pc.problem_id = ps.id) AS companies

FROM
    problem_scores ps
LEFT JOIN
    topic_scores ts ON ps.id = ts.problem_id
LEFT JOIN
    company_scores cs ON ps.id = cs.problem_id
WHERE
    (ps.freq_score +
    ps.acc_score +
    ps.like_score +
    ROUND(COALESCE(ts.avg_topic_weight / ps.max_topic_weight * ps.weight_topic, ps.weight_topic * 0.667), 2) +
    ps.rating_score +
    ps.diff_bonus +
    COALESCE(cs.company_score, 0)) > 50
ORDER BY
    quality_score DESC;