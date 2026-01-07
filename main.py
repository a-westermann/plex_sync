import configparser
import os
from configparser import DuplicateOptionError
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


def upload_dir(local, remote):
    for name in os.listdir(local):
        local_path = os.path.join(local_dir, name)
        remote_path = remote.rstrip('/') + '/' + name
        if os.path.isdir(local_path):  # is a directory
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
                sftp.put(local_path, remote_path)
                print(f'uploaded {remote_path}')


if __name__ == '__main__':
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, port=port, username=username, password=password, timeout=10)
    print('ssh connected')
    sftp = ssh.open_sftp()
    print('sftp open')
    upload_dir(local_dir, remote_dir)

    sftp.close()
    ssh.close()
