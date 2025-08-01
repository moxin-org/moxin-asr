import os
import pathlib
import shutil
import sys
import tempfile
import time
import urllib.request
from urllib.parse import urlparse, parse_qs, unquote

from huggingface_hub import hf_hub_download, HfFileSystem

CHUNK_SIZE = 4 * 4 * 100 * 1024
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'


def download_model_from_huggingface(output_dir: pathlib.Path | str, repo: str, filename: str):
    download_file_from_huggingface(output_dir, repo, filename)


def download_file_from_huggingface(output_dir: pathlib.Path | str, repo: str, filename: str):
    if isinstance(output_dir, str):
        output_dir = pathlib.Path(output_dir)

    if check_file_exists_on_huggingface(output_dir, repo, filename):
        return

    hf_hub_download(
        repo_id=repo,
        filename=filename,
        local_dir=f'{output_dir}',
        cache_dir=f'{output_dir}'
    )


def check_file_exists_on_huggingface(output_dir: pathlib.Path | str, repo: str, file: str):
    fs = HfFileSystem()
    remote_files = fs.ls(f'{repo}/{file}')
    if not remote_files:
        return False

    if isinstance(output_dir, str):
        output_dir = pathlib.Path(output_dir)

    local_file = output_dir / file
    if not local_file.exists():
        return False

    remote_file = remote_files[0]
    remote_file_size = remote_file.get('size')
    local_file_size = local_file.stat().st_size
    if remote_file_size == local_file_size:
        return True
    return False


def download_lora_from_huggingface(base_dir: pathlib.Path | str, repo: str, filename: str):
    download_file_from_huggingface(base_dir, repo, filename)


def download_civitai_file(url: str, output_path: str, token: str = ''):
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': USER_AGENT,
    }

    # Disable automatic redirect handling
    class NoRedirection(urllib.request.HTTPErrorProcessor):
        def http_response(self, request, response):
            return response

        https_response = http_response

    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(NoRedirection)
    response = opener.open(request)

    if response.status in [301, 302, 303, 307, 308]:
        redirect_url = response.getheader('Location')

        # Extract filename from the redirect URL
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        content_disposition = query_params.get('response-content-disposition', [None])[0]

        if content_disposition:
            filename = unquote(content_disposition.split('filename=')[1].strip('"'))
        else:
            raise Exception('Unable to determine filename')

        response = urllib.request.urlopen(redirect_url)
    elif response.status == 404:
        raise Exception('File not found')
    else:
        raise Exception('No redirect found, something went wrong')

    total_size = response.getheader('Content-Length')

    if total_size is not None:
        total_size = int(total_size)

    # output_file = os.path.join(output_path, filename)

    temporary_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
    with temporary_file as f:
        downloaded = 0
        start_time = time.time()

        while True:
            chunk_start_time = time.time()
            buffer = response.read(CHUNK_SIZE)
            chunk_end_time = time.time()

            if not buffer:
                break

            downloaded += len(buffer)
            f.write(buffer)
            chunk_time = chunk_end_time - chunk_start_time

            if chunk_time > 0:
                speed = len(buffer) / chunk_time / (1024 ** 2)  # Speed in MB/s

            if total_size is not None:
                progress = downloaded / total_size
                sys.stdout.write(f'\rDownloading: {filename} [{progress * 100:.2f}%] - {speed:.2f} MB/s')
                sys.stdout.flush()

    shutil.move(temporary_file.name, output_path)

    end_time = time.time()
    time_taken = end_time - start_time
    hours, remainder = divmod(time_taken, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        time_str = f'{int(hours)}h {int(minutes)}m {int(seconds)}s'
    elif minutes > 0:
        time_str = f'{int(minutes)}m {int(seconds)}s'
    else:
        time_str = f'{int(seconds)}s'

    sys.stdout.write('\n')
    print(f'Download completed. File saved as: {filename}')
    print(f'Downloaded in {time_str}')


def download_lora_from_civitai(base_dir: pathlib.Path, filename: str, uri: str):
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
    civitai_token = os.environ.get('CIVITAI_TOKEN', '0412348365e9a632d16687abf37e23a2')
    output_file = base_dir / filename
    download_civitai_file(uri, f'{output_file}', civitai_token)
