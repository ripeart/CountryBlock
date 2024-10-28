import requests
from github import Github
import os
import ipaddress

# Constants
IP_DENY_URL = 'https://www.ipdeny.com/ipblocks/data/aggregated/ng-aggregated.zone'
REPO_NAME = 'ripeart/CountryBlock'
FILE_PATH = 'ip_blocks/ng_aggregated_regex.txt'
IP_FILE_PATH = 'ip_blocks/nigeria_ips.txt'
BRANCH = 'main'
COMMIT_MESSAGE_REGEX = 'Auto-update IP block list for Nigeria (regex, split)'
COMMIT_MESSAGE_IPS = 'Auto-update IP block list for Nigeria (IPs)'

# Get GitHub token from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def cidr_to_ips(cidr):
    """
    Converts a CIDR notation IP range to a list of individual IPs.
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return [str(ip) for ip in network.hosts()]  # Only list usable IPs, not network/broadcast
    except ValueError as e:
        print(f"Error converting CIDR {cidr} to IPs: {e}")
        return []

def cidr_to_regex(cidr):
    """
    Converts a CIDR notation IP range to a regex pattern that matches all IPs within that range.
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        start_ip = network.network_address
        end_ip = network.broadcast_address
        
        start_octets = start_ip.exploded.split('.')
        end_octets = end_ip.exploded.split('.')

        regex_parts = []

        for i in range(4):
            if start_octets[i] == end_octets[i]:
                regex_parts.append(start_octets[i])  # Fixed octet
            else:
                regex_parts.append(f"[{start_octets[i]}-{end_octets[i]}]")  # Range of octets

        regex_pattern = r'\b' + r'\.'.join(regex_parts) + r'\b'
        return regex_pattern

    except ValueError as e:
        print(f"Error converting CIDR {cidr} to regex: {e}")
        return None

def fetch_ip_blocks(url):
    """
    Fetches the IP block data from the provided URL, converts it to regex patterns,
    and returns both the regex patterns and individual IPs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        ip_blocks = response.text.strip().splitlines()
        
        regex_patterns = [cidr_to_regex(block) for block in ip_blocks if cidr_to_regex(block)]
        ip_list = [ip for block in ip_blocks for ip in cidr_to_ips(block)]

        return regex_patterns, ip_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP blocks: {e}")
        return None, None

def update_github_file(repo_name, file_path, content, commit_message, token, branch):
    """
    Updates or creates a file in the specified GitHub repository.
    """
    github = Github(token)
    try:
        repo = github.get_repo(repo_name)
        print(f"Connected to repository: {repo_name}")

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
        # Fetch the latest IP block list and convert it to regex and IPs
        ip_blocks_regex, ip_list = fetch_ip_blocks(IP_DENY_URL)

        if ip_blocks_regex:
            # Update the file in the GitHub repository with regex content
            update_github_file(REPO_NAME, FILE_PATH, ip_blocks_regex, COMMIT_MESSAGE_REGEX, GITHUB_TOKEN, BRANCH)

        if ip_list:
            # Update the file in the GitHub repository with individual IPs
            update_github_file(REPO_NAME, IP_FILE_PATH, ip_list, COMMIT_MESSAGE_IPS, GITHUB_TOKEN, BRANCH)
        else:
            print("No IP blocks fetched or converted. Exiting.")

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
