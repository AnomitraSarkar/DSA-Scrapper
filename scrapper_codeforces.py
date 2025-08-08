import requests
import csv
import time
from collections import Counter

BASE = "https://codeforces.com/api/"

def call(method, **params):
    resp = requests.get(BASE + method, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data["status"] != "OK":
        raise Exception(f"API error on {method}: {data.get('comment')}")
    time.sleep(2)  # Respect rate limit
    return data["result"]

def generate_codeforces_csvs(handle):
    user = call("user.info", handles=handle)[0]
    subs = call("user.status", handle=handle, from_=1, count=10000)
    subs_ok = [s for s in subs if s.get("verdict") == "OK"]
    rating_hist = call("user.rating", handle=handle)

    # overall_stats.csv
    with open("overall_stats.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Handle", "Rating", "Max Rating", "Rank", "Contribution"])
        w.writerow([handle, user.get("rating"), user.get("maxRating"), user.get("rank"), user.get("contribution")])

    # solved_questions.csv
    with open("solved_questions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Title", "Index", "Language", "Timestamp"])
        for s in subs_ok:
            p = s["problem"]
            w.writerow([p.get("name"), p.get("index"), s.get("programmingLanguage"), s.get("creationTimeSeconds")])

    # language_usage.csv
    lang_counts = Counter(s.get("programmingLanguage") for s in subs_ok)
    total = sum(lang_counts.values())
    with open("language_usage.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Language", "Count", "Percentage"])
        for lang, cnt in lang_counts.items():
            w.writerow([lang, cnt, round(100 * cnt / total, 2)])

    # topic_strengths.csv
    tag_counts = Counter(tag for s in subs_ok for tag in s["problem"].get("tags", []))
    with open("topic_strengths.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Tag", "Solved Count"])
        for tag, cnt in tag_counts.items():
            w.writerow([tag, cnt])

    # contest_performance.csv
    with open("contest_performance.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Contest Name", "Rank", "Old Rating", "New Rating"])
        for c in rating_hist:
            w.writerow([c.get("contestName"), c.get("rank"), c.get("oldRating"), c.get("newRating")])

    print("CSV files generated: overall_stats.csv, solved_questions.csv, language_usage.csv, topic_strengths.csv, contest_performance.csv")

if __name__ == "__main__":
    generate_codeforces_csvs("tourist")
