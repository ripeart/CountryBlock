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
        response.raise_for_status()  # Raises HTTPError if the status is not 200
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

        # Check if the file exists
        try:
            file_contents = repo.get_contents(file_path, ref=branch)

            # Check if content is the same as the existing file
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
            if '404' in str(e):  # File or directory not found
                print(f"File {file_path} not found. Attempting to create it.")
                
                # Create missing directories by creating .gitkeep files first
                directories = file_path.split('/')[:-1]
                for i in range(1, len(directories) + 1):
                    path = '/'.join(directories[:i]) + '/.gitkeep'
                    try:
                        repo.get_contents(path, ref=branch)
                    except:
                        repo.create_file(
                            path,
                            f"Create directory {path}",
                            '',
                            branch=branch
                        )

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

def main():
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
