import configparser
import os
import paramiko


config = configparser.ConfigParser()
config.read('config')
config = config['DEFAULT']

host = config['host']
port = int(config['port'])
username = config['user']
password = config['password']
local_dir = config['local_dir']
remote_dir = config['remote_dir']
x_plex_token = config['xplextoken']

blacklist = {
    '.parts'
}

made_changes = False

def ensure_remote_dir(remote_path: str):
    """
    Ensure that the directory for remote_path exists.
    remote_path can be either a dir or a full file path.
    """
    # Get the directory part (for a file path)
    if '.' in remote_path.rsplit('/', 1)[-1]:
        remote_dir_path = remote_path.rsplit('/', 1)[0]
    else:
        remote_dir_path = remote_path

    # Walk down the path, creating as needed
    parts = remote_dir_path.strip('/').split('/')
    cur = ''
    for part in parts:
        cur = f'{cur}/{part}' if cur else f'/{part}'
        try:
            sftp.stat(cur)
        except IOError:
            sftp.mkdir(cur)


def upload_dir(local, remote):
    for name in os.listdir(local):
        local_path = os.path.join(local, name)
        remote_path = remote.rstrip('/') + '/' + name

        ext = os.path.splitext(name)[1].lower()  # check if the file type isn't wanted
        if ext in blacklist:
            continue

        if os.path.isdir(local_path):  # is a directory
            ensure_remote_dir(remote_path)
            upload_dir(local_path, remote_path)
        else:
            upload = False

            try:
                attrs = sftp.stat(remote_path)
                remote_size = attrs.st_size
                local_size = os.path.getsize(local_path)

                if remote_size != local_size:
                    upload = True
            except IOError:  # file does not exist
                upload = True

            if upload:
                global made_changes
                made_changes = True
                print(f'coppying... {local_path}')
                ensure_remote_dir(remote_path)
                sftp.put(local_path, remote_path, confirm=False)
                print(f'uploaded {remote_path}')
            else:
                print(f'skipping {remote_path}')


def scan_libs():
    import requests

    url = f"http://{host}:32400"
    token = x_plex_token
    url = f"{url}/library/sections/all/refresh"
    r = requests.get(url, params={"X-Plex-Token": token}, timeout=10)
    r.raise_for_status()


if __name__ == '__main__':
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, password=password, timeout=10)
    print('ssh connected')
    # sftp = ssh.open_sftp()
    transport = ssh.get_transport()

    # Bump up the speeds for transfer
    sftp = paramiko.SFTPClient.from_transport(
        transport,
        window_size=16 * 1024 * 1024,
        max_packet_size=256 * 1024,
    )
    print('sftp open')
    ensure_remote_dir(remote_dir)
    upload_dir(local_dir, remote_dir)

    if made_changes:
        print('Made changes. Scanning libraries...')
        scan_libs()
        print('Lib scan complete')

    sftp.close()
    ssh.close()
