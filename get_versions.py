import click
import json
import os
import shutil

import dropbox
from pdf2image import convert_from_path


def pdf_to_png(pdf, png):
    converted = convert_from_path(pdf, dpi=200)[0]
    converted.save(png)


def copy(name1, name2):
    shutil.copyfile(name1, name2)


def download_previews(dbx, file_path, output_dir, convert):
    os.makedirs(output_dir, exist_ok=True)

    # The current version of the dropbox api is limited to 100 revisions.
    revisions = dbx.files_list_revisions(file_path, limit=100).entries
    print(f"Found {len(revisions)} versions. If you were expecting more, see README.md")

    files = []
    # Revisions are delivered in reverse chronological order, (newest first),
    # so we traverse in reverse to number them properly.
    for i, rev in enumerate(reversed(revisions)):
        rev_file = os.path.join(output_dir, f"version_{index:03}{ext}")
        png_file = rev_file.replace(ext, ".png")
        if not os.path.exists(rev_file):
            metadata = dbx.files_download_to_file(rev_file, path=file_path, rev=rev.rev)

        if not os.path.exists(png_file):
            convert(rev_file, png_file)

        files.append((png_file, rev.server_modified.isoformat()))

    return files


@click.command()
@click.option('-t', '--token-file', type=click.File('r'), required=True, default=".token",
    help="A file containing your dropbox access token; see README.md for how to get one.")
@click.option('-f', '--file-path', type=click.Path(exists=False), required=True,
    help="Path to the file, relative to your dropbox root. Should begin with a slash (/).")
@click.option('-o', '--outdir', type=click.Path(writable=True), required=True,
    help="output directory to store all the snapshots in.")
@click.option('-m', '--metadata-file', type=click.File('w'), required=True,
    help="output json file containing filepaths and dates for all the retrieved versions.")
def main(token_file, file_path, outdir, metadata_file):
    converters = {
        ".pdf": pdf_to_png,
        ".png": copy,
        # TODO: support other file types
    }

    ext = os.path.splitext(file_path)[1]
    try:
        convert = converters[ext]
    except KeyError:
        supported = ', '.join(sorted(converters.keys()))
        raise ValueError(f"Unsupported File Type. Must be one of: {supported}")

    token = token_file.read().strip()
    dbx = dropbox.Dropbox(token)

    versions = download_previews(dbx, file_path, outdir, convert)

    json.dump(versions, metadata_json, indent=4)


if __name__ == "__main__":
    main()
