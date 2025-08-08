import requests
import csv
from collections import Counter

LEETCODE_URL = "https://leetcode.com/graphql"

def graphql_query(query, variables=None):
    resp = requests.post(LEETCODE_URL, json={"query": query, "variables": variables or {}})
    resp.raise_for_status()
    return resp.json()

def fetch_overall_stats(username):
    query = """
    query($username: String!) {
      matchedUser(username: $username) {
        submitStatsGlobal {
          acSubmissionNum { difficulty count submissions }
          totalSubmissionNum { difficulty count submissions }
        }
      }
    }
    """
    return graphql_query(query, {"username": username})["data"]["matchedUser"]["submitStatsGlobal"]

def fetch_recent_languages(username, limit=200):
    query = """
    query($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        lang
      }
    }
    """
    subs = graphql_query(query, {"username": username, "limit": limit})["data"]["recentAcSubmissionList"]
    langs = [s["lang"] for s in subs]
    return Counter(langs)

def fetch_topic_strengths(username, limit=200):
    recent_query = """
    query($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        titleSlug
      }
    }
    """
    recent_subs = graphql_query(recent_query, {"username": username, "limit": limit})["data"]["recentAcSubmissionList"]

    topic_counter = Counter()

    details_query = """
    query($slug: String!) {
      question(titleSlug: $slug) {
        difficulty
        topicTags { name }
      }
    }
    """
    for sub in recent_subs:
        details = graphql_query(details_query, {"slug": sub["titleSlug"]})["data"]["question"]
        for tag in details["topicTags"]:
            topic_counter[(tag["name"], details["difficulty"])] += 1

    return topic_counter

def fetch_contest_performance(username):
    query = """
    query($username: String!) {
      userContestRankingHistory(username: $username) {
        contest { title }
        ranking
        rating
        attended
        trendDirection
        problemsSolved
      }
    }
    """
    return graphql_query(query, {"username": username})["data"]["userContestRankingHistory"]

def save_overall_stats(stats, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Difficulty", "Solved Count", "Total Submissions", "Acceptance Rate (%)"])
        for s in stats["acSubmissionNum"]:
            total_subs = next(item["submissions"] for item in stats["totalSubmissionNum"] if item["difficulty"] == s["difficulty"])
            acc_rate = (s["count"] / total_subs * 100) if total_subs else 0
            writer.writerow([s["difficulty"], s["count"], total_subs, round(acc_rate, 2)])

def save_language_usage(lang_counter, filename):
    total = sum(lang_counter.values())
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Language", "Count", "Usage (%)"])
        for lang, count in lang_counter.items():
            writer.writerow([lang, count, round(count / total * 100, 2)])

def save_topic_strengths(topic_counter, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Topic", "Difficulty", "Solved Count"])
        for (topic, diff), count in topic_counter.items():
            writer.writerow([topic, diff, count])

def save_contest_performance(contests, filename):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Contest Title", "Rank", "Rating", "Problems Solved", "Trend"])
        for c in contests:
            if c["attended"]:
                writer.writerow([c["contest"]["title"], c["ranking"], c["rating"], c["problemsSolved"], c["trendDirection"]])

def scrape_solved_questions(username, csv_file):
    url = LEETCODE_URL

    # Query recent accepted submissions (change limit if needed)
    recent_submissions_query = """
    query recentAcSubmissions($username: String!) {
      recentAcSubmissionList(username: $username, limit: 50) {
        id
        title
        titleSlug
        timestamp
        lang
      }
    }
    """

    # Query problem details (difficulty, etc.)
    problem_details_query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        difficulty
        topicTags {
          name
        }
      }
    }
    """

    # Step 1: Get list of recent solved questions
    submissions_resp = requests.post(url, json={"query": recent_submissions_query, "variables": {"username": username}})
    submissions_data = submissions_resp.json()["data"]["recentAcSubmissionList"]

    solved_questions = []

    for sub in submissions_data:
        # Step 2: Get details for each problem
        details_resp = requests.post(url, json={"query": problem_details_query, "variables": {"titleSlug": sub["titleSlug"]}})
        details_data = details_resp.json()["data"]["question"]

        solved_questions.append({
            "Title": sub["title"],
            "Difficulty": details_data["difficulty"],
            "Language": sub["lang"],
            "Tags": ", ".join(tag["name"] for tag in details_data["topicTags"]),
            "Submission Time": sub["timestamp"]
        })

    # Step 3: Save to CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Difficulty", "Language", "Tags", "Submission Time"])
        writer.writeheader()
        writer.writerows(solved_questions)

    print(f"Saved {len(solved_questions)} solved question entries to {csv_file}")


def generate_profile_insights(username):
    # 1. Overall stats
    stats = fetch_overall_stats(username)
    save_overall_stats(stats, "overall_stats.csv")

    # 2. Language usage
    langs = fetch_recent_languages(username)
    save_language_usage(langs, "language_usage.csv")

    # 3. Topic strengths
    topics = fetch_topic_strengths(username)
    save_topic_strengths(topics, "topic_strengths.csv")

    # 4. Contest performance
    contests = fetch_contest_performance(username)
    save_contest_performance(contests, "contest_performance.csv")
    
    scrape_solved_questions(username, "solved_questions.csv")

    print("CSV files generated: overall_stats.csv, language_usage.csv, topic_strengths.csv, contest_performance.csv")

if __name__ == "__main__":
    generate_profile_insights("AnomitraSarkar")
