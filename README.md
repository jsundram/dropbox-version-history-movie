# README

This repository uses dropbox as a source of file history, with the aim of showing how a file has changed over the course of time.
It's particularly interesting for data visualizations or designed assets.

## Getting snapshots of the file's version history
### `get_versions.py`
If you have fewer than 100 versions of a file, and your file is a .pdf or a .png, you can use `get_versions.py`.
You'll need a dropbox api token, which you can get by creating an app [here](https://www.dropbox.com/developers/apps), then going to the "Permissions" tab and clicking "Generate Access Token". The token expires after a day or so.

```
Usage: get_versions.py [OPTIONS]

Options:
  -t, --token_file FILENAME     A file containing your dropbox access token;
                                see above for how to get one.  [required]
  -f, --file_path PATH          Path to the file, relative to your dropbox
                                root. Should begin with a slash (/).
                                [required]
  -o, --outdir PATH             output directory to store all the snapshots
                                in.  [required]
  -m, --metadata-file FILENAME  output json file containing filepaths and
                                dates for all the retrieved versions.
                                [required]
```

### `console_script.js` and `console_dl.py`
If you have more than 100 versions of a file or your filetype isn't supported by get_versions.py, we will have to pull previews out of your web browser:

1. Log in to Dropbox and navigate to the desired file, then view its version history.
2. Open the developer console and paste in the contents of `console_script.js`. This will take some time to load all the versions and open a preview for each one. It will record the timestamp and preview url for each version, and copy a json object to your clipboard.
3. When the json object has been copied to your clipboard, paste it into a file called `versions.json`.
4. On the version history page you opened, with developer tools still open, open the Network tab and then click to open one of the previews. Filter to show requests that to `p.png`. Click it, and then click "Copy | Copy as cURL"
5. Paste the cURL into a file called `example_curl.sh`.
6. `uv run console_dl.py` 
    * This will extract the relevant parameters from `example_curl.sh` and download the files in `versions.json`.

```
Usage: console_dl.py [OPTIONS]

Options:
  -c, --example_curl_file FILENAME
                                  A file containing a pasted curl command. See
                                  above for how to get this.  [required]
  -v, --versions_json FILENAME    A file containing the json output from
                                  running console_script.js  [required]
  -o, --outdir PATH               output directory to store all the snapshots
                                  in.  [required]
  -m, --metadata-file FILENAME    output json file containing filepaths and
                                  dates for all the retrieved versions.
                                  [required]
```
## Making a movie
`uv run make_movie.py` and point it to your versions.json file.

```
Usage: make_movie.py [OPTIONS]

Options:
  -m, --metadata-file FILENAME  json file containing filepaths and dates for
                                all the retrieved versions.  [required]
  -o, --output-file FILE        output filename for the generated movie.
                                [required]
  -f, --fps INTEGER             frames per second that the generated movie
                                will play back at.
  --help                        Show this message and exit.
```
