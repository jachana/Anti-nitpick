import os
import requests
from github import Github

def get_pr_diff(repo, pr_number):
    pr = repo.get_pull(pr_number)
    diff_url = pr.diff_url
    response = requests.get(diff_url)
    response.raise_for_status()
    return response.text

def get_comment_diff(repo, comment_id):
    comment = repo.get_issue_comment(comment_id)
    if not comment.pull_request_url:
        return None
    pr = repo.get_pull(int(comment.pull_request_url.split('/')[-1]))
    files = pr.get_files()
    diffs = []
    for file in files:
        if file.filename in comment.body:
            diffs.append(file.patch)
    return "\n".join(diffs)

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
    comment_id = int(os.environ["GITHUB_EVENT_COMMENT_ID"])

    g = Github(github_token)
    repo = g.get_repo(repo_name)

    diff = get_comment_diff(repo, comment_id)
    if diff:
        suggestion = generate_code_suggestion(diff, openai_api_key)
        pr_number = int(os.environ["GITHUB_REF"].split("/")[2])
        add_comment_to_pr(repo, pr_number, suggestion)
    else:
        print("No diff found in comment")
