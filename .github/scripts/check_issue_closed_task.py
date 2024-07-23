import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("TOKEN")
GITHUB_USERNAME = os.getenv("USERNAME")
REPO_NAME = os.getenv("REPO_NAME")
PROJECT_ID = os.getenv("PROJECT_ID")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def get_issue(issue_number):
    url = f"{GITHUB_REST_URL}/repos/{GITHUB_USERNAME}/{REPO_NAME}/issues/{issue_number}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_project_item(project_id, issue_id):
    query = """
    query($project_id: ID!, $issue_id: Int!) {
      node(id: $project_id) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              content {
                ... on Issue {
                  id
                  number
                  title
                  body
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    variables = {"project_id": project_id, "issue_id": issue_id}
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
    response.raise_for_status()
    data = response.json()
    items = data['data']['node']['items']['nodes']
    for item in items:
        if item['content']['number'] == issue_id:
            return item
    return None

def create_issue(title, body):
    url = f"{GITHUB_REST_URL}/repos/{GITHUB_USERNAME}/{REPO_NAME}/issues"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    payload = {
        "title": title,
        "body": body
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    issue_number = int(ISSUE_NUMBER)
    issue = get_issue(issue_number)
    print(f"Checking issue: {issue['title']}")

    item = get_project_item(PROJECT_ID, issue_number)
    if not item:
        print(f"Issue {issue_number} not found in project {PROJECT_ID}")
        return

    completed_value = None
    for field in item['fieldValues']['nodes']:
        if field.get('field', {}).get('name') == 'Completed':
            completed_value = field['name']

    if completed_value == 'No':
        new_issue = create_issue(
            title=f"[Reopened] {issue['title']}",
            body=f"This task was not completed: {issue['body']}"
        )
        print(f"New issue created: {new_issue['title']}")

if __name__ == "__main__":
    main()
