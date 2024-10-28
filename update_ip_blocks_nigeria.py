import requests
from github import Github
import os

# Constants
IP_DENY_URL = 'https://www.ipdeny.com/ipblocks/data/aggregated/ng-aggregated.zone'
REPO_NAME = 'ripeart/CountryBlock'  # Replace with your GitHub username and repository
FILE_PATH = 'ip_blocks/ng_aggregated.zone'  # Replace with the file path in your repository
COMMIT_MESSAGE = 'Auto-update IP block list for Nigeria'

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def fetch_ip_blocks(url):
    """
    Fetches the IP block data from the provided URL.
    Returns the content as a string.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch IP blocks: {response.status_code}")

def update_github_file(repo_name, file_path, content, commit_message, token):
    """
    Updates or creates a file in the specified GitHub repository.
    """
    github = Github(token)
    repo = github.get_repo(repo_name)

    try:
        # Try to get the file's current content
        file_contents = repo.get_contents(file_path)

        # Update the existing file
        repo.update_file(
            file_contents.path,
            commit_message,
            content,
            file_contents.sha
        )
        print(f"Successfully updated {file_path} in {repo_name}")
        
    except Exception as e:
        if '404' in str(e):  # If the file doesn't exist, create a new file
            repo.create_file(
                file_path,
                commit_message,
                content
            )
            print(f"Successfully created {file_path} in {repo_name}")
        else:
            print(f"Error updating file: {e}")

def main():
    try:
        # Fetch the latest IP block list from IPdeny
        ip_blocks = fetch_ip_blocks(IP_DENY_URL)

        # Update the file in the GitHub repository
        update_github_file(REPO_NAME, FILE_PATH, ip_blocks, COMMIT_MESSAGE, GITHUB_TOKEN)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
