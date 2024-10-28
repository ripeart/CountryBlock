import requests
from github import Github
import os

# Constants
IP_DENY_URL = 'https://www.ipdeny.com/ipblocks/data/aggregated/ng-aggregated.zone'
REPO_NAME = 'ripeart/CountryBlock'  # Ensure this is correct
FILE_PATH = 'ip_blocks/ng_aggregated.zone'  # Adjust to the correct file path
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

def update_github_file(repo_name, file_path, content, commit_message, token):
    """
    Updates or creates a file in the specified GitHub repository.
    """
    github = Github(token)
    repo = github.get_repo(repo_name)

    try:
        file_contents = repo.get_contents(file_path)

        # Check if the content is the same as the existing file
        if file_contents.decoded_content.decode() == content:
            print(f"No changes detected in {file_path}. Skipping update.")
            return

        # Update the existing file
        repo.update_file(
            file_contents.path,
            commit_message,
            content,
            file_contents.sha
        )
        print(f"Successfully updated {file_path} in {repo_name}")

    except Exception as e:
        if '404' in str(e):  # If the file or directory doesn't exist
            try:
                # Create missing directories by creating an empty file first
                directories = file_path.split('/')[:-1]
                for i in range(1, len(directories) + 1):
                    path = '/'.join(directories[:i]) + '/.gitkeep'
                    if not repo.get_contents(path, ref='main'):
                        repo.create_file(path, 'Create missing directory', '')
                
                # Now create the file
                repo.create_file(
                    file_path,
                    commit_message,
                    content
                )
                print(f"Successfully created {file_path} in {repo_name}")
            except Exception as create_error:
                print(f"Error creating file or directory: {create_error}")
        else:
            print(f"Error updating file: {e}")

def main():
    try:
        # Fetch the latest IP block list from IPdeny
        ip_blocks = fetch_ip_blocks(IP_DENY_URL)

        if ip_blocks:
            # Update the file in the GitHub repository
            update_github_file(REPO_NAME, FILE_PATH, ip_blocks, COMMIT_MESSAGE, GITHUB_TOKEN)
        else:
            print("No IP blocks fetched. Exiting.")

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
