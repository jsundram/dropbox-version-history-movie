import click
import datetime
import json
import os
import re
import requests
import shlex
import time


def parse_curl(curl_command):
    headers, cookies = {}, {}

    # Split the curl command into parts
    curl_parts = shlex.split(curl_command)

    # Extract headers and cookies
    for i, part in enumerate(curl_parts):
        if part == '-H':
            header = curl_parts[i + 1]
            if header.lower().startswith('cookie:'):
                cookie = header.split(': ', 1)[1]
                cookies = dict([p.split('=') for p in cookie.split('; ')])
            elif ': ' in header:
                key, value = header.split(': ', 1)
                headers[key.lower()] = value

    return headers, cookies


@click.command()
@click.option('-c', '--example-curl-file', type=click.File('r'), required=True,
    help="A file containing a pasted curl command. See About.md for how to get this.")
@click.option('-v', '--versions-json', type=click.File('r'), required=True,
    help="A file containing the json output from running console_script.js")
@click.option('-o', '--outdir', type=click.Path(writable=True), required=True,
    help="output directory to store all the snapshots in.")
@click.option('-m', '--metadata-file', type=click.File('w'), required=True,
    help="output json file containing filepaths and dates for all the retrieved versions.")
def main(example_curl_file, versions_json, outdir, metadata_file):
    start = time.time()
    # Get the headers and cookies from a sample curl command captured by the user.
    headers, cookies = parse_curl(example_curl_file.read())

    # Load the JSON file
    versions = json.load(versions_json)

    # Create the 'versions' directory if it doesn't exist
    os.makedirs(outdir, exist_ok=True)

    def parse_timestamp(entry):
        return datetime.datetime.fromisoformat(entry['timestamp'])

    # Download each file
    files, n = [], len(versions)
    for ix, entry in enumerate(sorted(versions, key=parse_timestamp), 1):
        timestamp = entry['timestamp']
        url = entry['url']
        file_path = os.path.join(outdir, f'preview_{ix:03}.png')

        print(f"{ix:03} / {n}. Downloading {url} as {file_path} ...")
        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            files.append((file_path, timestamp))
        else:
            print(f"FAILED to download {url} (status code {response.status_code})")

    json.dump(files, metadata_file, indent=4)

    m = len(files)
    print(f"{n} / {m} Previews downloaded to {outdir}.")
    print(f"\nMetadata  written to {metadata_file.name}")
    print(f"Elapsed time: {time.time() - start:.2f} seconds")


if __name__ == '__main__':
    main()
