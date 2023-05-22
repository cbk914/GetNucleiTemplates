#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: David Espejo (Fortytwo Security)
import requests
import json
import time
import os
import subprocess

def search_github_repos(query_terms):
    base_url = "https://api.github.com"
    token = input("Please enter your GitHub API token (press 'Enter' for unauthenticated): ")
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token.strip():  # If the user provided a token
        headers['Authorization'] = f'token {token}'
    search_url = f"{base_url}/search/repositories"
    search_params = {'q': ' OR '.join(query_terms), 'page': 1}

    found_repos = []

    with open("nuclei.txt", "r") as file:
        existing_repos = set(line.strip() for line in file.readlines())

    while True:
        response = requests.get(search_url, headers=headers, params=search_params)

        if response.status_code != 200:
            print(f"Error with status code: {response.status_code}")
            return

        rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))

        if rate_limit_remaining < 10:  # adjust the number as needed
            reset_time = rate_limit_reset - time.time()
            if reset_time > 0:
                print(f"Approaching rate limit. Sleeping for {reset_time} seconds.")
                time.sleep(reset_time)

        data = response.json()

        for repo in data["items"]:
            # Check if repository contains .yaml or .yml files
            contents_url = f"{base_url}/repos/{repo['full_name']}/contents"
            contents_response = requests.get(contents_url, headers=headers)

            if contents_response.status_code != 200:
                continue

            contents = contents_response.json()
            if any(file['name'].endswith(('.yaml', '.yml')) for file in contents):
                repo_url = repo['html_url']
                if repo_url not in existing_repos:
                    print(f"Found New Nuclei Template Repo: {repo_url}")
                    found_repos.append(repo_url)

        if 'next' not in response.links:
            break

        search_params['page'] += 1

    print(f"\nFound {len(found_repos)} new Nuclei Template repositories.")
    user_input = input("Do you want to download the found repositories? (y/n): ")

    if user_input.lower() == 'y':
        with open("nuclei.txt", "a") as file:
            for repo in found_repos:
                file.write(f"{repo}\n")

        print("Running getnucleitemplates.py...")
        subprocess.run(["python3", "getnucleitemplates.py"])

if __name__ == "__main__":
    search_terms = ["nuclei-templates", "nuclei-scripts", "nuclei-configs"]
    search_github_repos(search_terms)