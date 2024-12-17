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
    comment = repo.get_issues_comments(comment_id)
    if not comment.pull_request_url:
        return None
    pr = repo.get_pull(int(comment.pull_request_url.split('/')[-1]))
    files = pr.get_files()
    diffs = []
    for file in files:
        if file.filename in comment.body:
            diffs.append(file.patch)
    return "\n".join(diffs)

import anthropic

def generate_code_suggestion(diff, anthropic_api_key):
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    prompt = f"""Suggest code changes based on this diff:\n{diff}"""
    message = client.messages.create(
        model="claude-3.5-haiku-20240229",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    return message.content[0].text

def add_comment_to_pr(repo, pr_number, comment):
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment)

if __name__ == "__main__":
    github_token = os.environ["GITHUB_TOKEN"]
    anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
    repo_name = os.environ["GITHUB_REPOSITORY"]
    comment_id = int(os.environ["GITHUB_EVENT_COMMENT_ID"])

    g = Github(github_token)
    repo = g.get_repo(repo_name)

    diff = get_comment_diff(repo, comment_id)
    if diff:
        suggestion = generate_code_suggestion(diff, anthropic_api_key)
        pr_number = int(os.environ["GITHUB_REF"].split("/")[2])
        add_comment_to_pr(repo, pr_number, suggestion)
    else:
        print("No diff found in comment")
