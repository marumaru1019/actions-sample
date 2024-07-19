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

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def get_project_items(project_id):
    query = """
    query($project_id: ID!) {
      node(id: $project_id) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              id
              content {
                ... on Issue {
                  id
                  number
                  title
                  body
                  labels(first: 5) {
                    nodes {
                      name
                    }
                  }
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
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
    variables = {"project_id": project_id}
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
    response.raise_for_status()
    data = response.json()
    print("Project items response:", json.dumps(data, indent=2))  # Debug output

    if 'data' in data and 'node' in data['data']:
        items = data['data']['node']['items']['nodes']
        return items
    else:
        print("Error: 'data' key not found in response")
        return []

def get_issue(issue_number):
    url = f"{GITHUB_REST_URL}/repos/{GITHUB_USERNAME}/{REPO_NAME}/issues/{issue_number}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

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

def get_issue_node_id(issue_id):
    query = """
    query($issue_id: ID!) {
      node(id: $issue_id) {
        ... on Issue {
          id
        }
      }
    }
    """
    variables = {"issue_id": issue_id}
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
    response.raise_for_status()
    data = response.json()
    print("Issue node ID response:", json.dumps(data, indent=2))  # Debug output
    if 'data' in data and 'node' in data['data']:
        return data['data']['node']['id']
    else:
        print("Error: 'data' key not found in response")
        return None

def add_issue_to_project(project_id, issue_node_id):
    mutation = """
    mutation($project_id: ID!, $issue_id: ID!) {
      addProjectV2ItemById(input: {projectId: $project_id, contentId: $issue_id}) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "project_id": project_id,
        "issue_id": issue_node_id
    }
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={"query": mutation, "variables": variables})
    response.raise_for_status()
    data = response.json()
    print("Add issue to project response:", json.dumps(data, indent=2))  # Debug output
    return data

def main():
    today = datetime.today().strftime('%Y-%m-%d')

    # Get user projects
    query = """
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 20) {
          nodes {
            id
            title
          }
        }
      }
    }
    """
    variables = {"login": GITHUB_USERNAME}
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
    response.raise_for_status()
    projects = response.json()
    print("Projects response:", json.dumps(projects, indent=2))
    projects = projects['data']['user']['projectsV2']['nodes']

    project = next((project for project in projects if project['id'] == PROJECT_ID), None)
    if not project:
        raise ValueError(f"Project with ID {PROJECT_ID} not found")

    items = get_project_items(PROJECT_ID)
    for item in items:
        date_value = None
        completed_value = None
        for field in item['fieldValues']['nodes']:
            if field.get('field', {}).get('name') == 'Date':
                date_value = field['date']
            elif field.get('field', {}).get('name') == 'Completed':
                completed_value = field['name']

        if date_value == today and completed_value == 'No':
            print(item)
            issue_number = item['content']['number']
            issue = get_issue(issue_number)
            print(issue)
            new_issue = create_issue(
                title=issue['title'],
                body=f"This task was not completed today: {issue['body']}"
            )
            print("New issue created:", json.dumps(new_issue, indent=2))  # Debug output
            new_issue_node_id = get_issue_node_id(new_issue['node_id'])
            print("New issue node ID:", new_issue_node_id)  # Debug output
            add_issue_to_project(PROJECT_ID, new_issue_node_id)

if __name__ == "__main__":
    main()
