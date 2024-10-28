import requests
from github import Github
import os

# Constants
IP_DENY_URL = 'https://www.ipdeny.com/ipblocks/data/aggregated/ng-aggregated.zone'
REPO_NAME = 'ripeart/CountryBlock'  # Ensure this matches your repository name
FILE_PATH = 'ip_blocks/ng_aggregated.zone.txt'  # Corrected file path
BRANCH = 'main'  # Ensure this matches the branch you are using
COMMIT_MESSAGE = 'Auto-update IP block list for Nigeria'

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def fetch_ip_blocks(url):
    """
    Fetches the IP block data from the provided URL.
    Returns the content as a string.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP blocks: {e}")
        return None

def update_github_file(repo_name, file_path, content, commit_message, token, branch):
    """
    Updates or creates a file in the specified GitHub repository.
    """
    github = Github(token)
    try:
        repo = github.get_repo(repo_name)
        print(f"Connected to repository: {repo_name}")

        # Check if the file already exists
        try:
            file_contents = repo.get_contents(file_path, ref=branch)

            # If content is the same, no need to update
            if file_contents.decoded_content.decode() == content:
                print(f"No changes detected in {file_path}. Skipping update.")
                return

            # Update the existing file
            repo.update_file(
                file_contents.path,
                commit_message,
                content,
                file_contents.sha,
                branch=branch
            )
            print(f"Successfully updated {file_path} in {repo_name} on branch {branch}")

        except Exception as e:
            if '404' in str(e):
                print(f"File {file_path} not found. Attempting to create it.")

                # Create the directory structure if missing
                create_directories(repo, file_path, branch)

                # Create the new file
                repo.create_file(
                    file_path,
                    commit_message,
                    content,
                    branch=branch
                )
                print(f"Successfully created {file_path} in {repo_name} on branch {branch}")

            else:
                print(f"Error updating file: {e}")

    except Exception as e:
        print(f"Error accessing repository {repo_name} or creating file: {e}")

def create_directories(repo, file_path, branch):
    """
    Create missing directories in the repository.
    """
    directories = file_path.split('/')[:-1]
    for i in range(1, len(directories) + 1):
        path = '/'.join(directories[:i]) + '/.gitkeep'
        try:
            repo.get_contents(path, ref=branch)
        except:
            try:
                repo.create_file(
                    path,
                    f"Create directory {path}",
                    '',
                    branch=branch
                )
                print(f"Created directory {path}")
            except Exception as e:
                print(f"Error creating directory {path}: {e}")

def main():
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN not found in environment variables.")
        return

    try:
        # Fetch the latest IP block list from IPdeny
        ip_blocks = fetch_ip_blocks(IP_DENY_URL)

        if ip_blocks:
            # Update the file in the GitHub repository
            update_github_file(REPO_NAME, FILE_PATH, ip_blocks, COMMIT_MESSAGE, GITHUB_TOKEN, BRANCH)
        else:
            print("No IP blocks fetched. Exiting.")

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
