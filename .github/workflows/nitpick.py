import os
import requests
from github import Github

def get_pr_diff(repo, pr_number):
    pr = repo.get_pull(pr_number)
    diff_url = pr.diff_url
    response = requests.get(diff_url)
    response.raise_for_status()
    return response.text

def generate_code_suggestion(diff, openai_api_key):
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f"Suggest code changes based on this diff:\n{diff}",
            }
        ],
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def add_comment_to_pr(repo, pr_number, comment):
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment)

if __name__ == "__main__":
    github_token = os.environ["GITHUB_TOKEN"]
    openai_api_key = os.environ["OPENAI_API_KEY"]
    repo_name = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ["GITHUB_REF"].split("/")[2])

    g = Github(github_token)
    repo = g.get_repo(repo_name)

    diff = get_pr_diff(repo, pr_number)
    suggestion = generate_code_suggestion(diff, openai_api_key)
    add_comment_to_pr(repo, pr_number, suggestion)
