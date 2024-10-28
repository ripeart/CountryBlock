import requests
from github import Github
import os
import ipaddress

# Constants
IP_DENY_URL = 'https://www.ipdeny.com/ipblocks/data/aggregated/ng-aggregated.zone'
REPO_NAME = 'ripeart/CountryBlock'
FILE_PATH = 'ip_blocks/ng_aggregated_regex.txt'
BRANCH = 'main'
COMMIT_MESSAGE = 'Auto-update IP block list for Nigeria (regex, split)'

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def cidr_to_regex(cidr):
    """
    Converts a CIDR notation IP to a regex pattern.
    """
    try:
        # Convert CIDR to a list of IP addresses
        network = ipaddress.ip_network(cidr, strict=False)
        start_ip = network[0]
        end_ip = network[-1]

        # Create regex from start and end IPs
        start_regex = start_ip.exploded.replace('.', r'\.')
        end_regex = end_ip.exploded.replace('.', r'\.')
        return f"{start_regex}|{end_regex}"

    except ValueError as e:
        print(f"Error converting CIDR {cidr} to regex: {e}")
        return None

def fetch_ip_blocks(url):
    """
    Fetches the IP block data from the provided URL and converts it to regex patterns.
    Splits the regex into rows of 1,000 characters or less.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError if the status is not 200
        
        # Split the IP blocks and convert each to regex
        ip_blocks = response.text.strip().splitlines()
        regex_patterns = [cidr_to_regex(block) for block in ip_blocks if cidr_to_regex(block)]

        # Join all regex patterns into one string
        combined_regex = '|'.join(regex_patterns)

        # Split combined regex into rows of 1,000 characters or fewer
        regex_rows = []
        while len(combined_regex) > 0:
            row = combined_regex[:1000]
            
            # Ensure row ends cleanly without splitting in the middle of a pattern
            if '|' in row and combined_regex[1000] != '|':
                last_pipe = row.rfind('|')
                row = row[:last_pipe]

            regex_rows.append(row)
            combined_regex = combined_regex[len(row):]

        return regex_rows

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

        # Join content rows with newline characters
        file_content = '\n'.join(content)

        # Check if the file exists
        try:
            file_contents = repo.get_contents(file_path, ref=branch)

            # Check if content is the same as the existing file
            if file_contents.decoded_content.decode() == file_content:
                print(f"No changes detected in {file_path}. Skipping update.")
                return

            # Update the existing file
            repo.update_file(
                file_contents.path,
                commit_message,
                file_content,
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
                    file_content,
                    branch=branch
                )
                print(f"Successfully created {file_path} in {repo_name} on branch {branch}")

            else:
                print(f"Error updating file: {e}")

    except Exception as e:
        print(f"Error accessing repository {repo_name} or creating file: {e}")

def main():
    try:
        # Fetch the latest IP block list and convert it to regex
        ip_blocks_regex = fetch_ip_blocks(IP_DENY_URL)

        if ip_blocks_regex:
            # Update the file in the GitHub repository with regex content
            update_github_file(REPO_NAME, FILE_PATH, ip_blocks_regex, COMMIT_MESSAGE, GITHUB_TOKEN, BRANCH)
        else:
            print("No IP blocks fetched or converted to regex. Exiting.")

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
