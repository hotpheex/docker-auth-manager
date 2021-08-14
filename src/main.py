from json import load, dumps
from json.decoder import JSONDecodeError
import logging
from datetime import datetime
from os import getenv

from requests import get, head, RequestException
from apscheduler.schedulers.blocking import BlockingScheduler

DOCKER_AUTH_URL = 'https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull'
DOCKER_RATE_LIM_URL = 'https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest'
DOCKER_MAX_LIMIT = 200

class Auths:
    def __init__(self, docker_creds):
        creds = docker_creds.split(',')
        if not creds:
            logging.critical('No docker credentials were found')
            raise SystemExit()
        self.auths = dict.fromkeys(creds, 0)
        self.check_remaining()
        logging.info(f'Loaded {len(self.auths.keys())} docker credentials')

    def check_remaining(self):
        for auth in self.auths.keys():
            self.auths[auth] = check_remaining_pulls(auth)

    def select_fresh_auth(self):
        for auth, remaining in sorted(self.auths.items(), key=lambda item: item[1], reverse=True):
            if remaining > 1:
                return auth
        logging.error('No fresh credentials with any remaining docker pulls')
        return None

    def print_auths(self):
        print(self.auths)

def read_env_vars():
    config = {
        "DOCKER_CREDS": getenv('DOCKER_CREDS'),
        "DOCKER_CONFIG_PATH": getenv('DOCKER_CONFIG_PATH', '/.docker/config'),
        "REFRESH_THRESHOLD": getenv('REFRESH_THRESHOLD', 50),
        "SCHEDULE_MINS": getenv('SCHEDULE_MINS', 10)
    }

    missing = [var for var, value in config.items() if not value]
    if missing:
        logging.critical(f'Missing required environment variables {missing}')
        raise SystemExit()

    return config

def read_current_auth(file_path):
    try:
        with open(file_path, 'r') as fh:
            docker_config = load(fh)
        set_auth = docker_config['auths']['https://index.docker.io/v1/']['auth']
        return set_auth
    except (FileNotFoundError, JSONDecodeError):
        with open(file_path, 'w') as fh:
            fh.write(dumps({"auths": {"https://index.docker.io/v1/": {"auth": ""}}}, indent=4))
        return None

def update_current_auth(file_path, new_auth):
    try:
        with open(file_path, 'r+') as fh:
            docker_config = load(fh)
            docker_config['auths']['https://index.docker.io/v1/']['auth'] = new_auth
            fh.seek(0)
            fh.write(dumps(docker_config, indent=4))
            fh.truncate()
    except (FileNotFoundError, JSONDecodeError):
        with open(file_path, 'w') as fh:
            fh.write(dumps({"auths": {"https://index.docker.io/v1/": {"auth": new_auth}}}, indent=4))

def check_remaining_pulls(basic_auth):
    try:
        response = get(DOCKER_AUTH_URL, headers={'Authorization': f'Basic {basic_auth}'})
        jwt_token = response.json()['token']
        response = head(DOCKER_RATE_LIM_URL, headers={'Authorization': f'Bearer {jwt_token}'})
        remaining = int(response.headers['ratelimit-remaining'].split(';')[0])
        return remaining
    except RequestException as err:
        logging.error(err)
    except KeyError as err:
        logging.error(f'ERROR ({basic_auth}): {response.json()}')

def rotate_docker_creds(auths, docker_config_file):
    fresh_creds = auths.select_fresh_auth()
    if fresh_creds:
        update_current_auth(docker_config_file, fresh_creds)
        logging.info(f'Credential refreshed ({fresh_creds[0:6]}...)')
    else:
        logging.info('No fresh credential available to use')

def update_current_auth_schedule(auths, docker_config_file, refresh_threshold):
    current_auth = read_current_auth(docker_config_file)
    if current_auth:
        current_remaining = check_remaining_pulls(current_auth)
        if current_remaining <= refresh_threshold:
            logging.info(f'Current credential below threshold ({current_remaining})')
            rotate_docker_creds(auths, docker_config_file)
        else:
            logging.info(f'Current credential above threshold ({current_remaining})')
    else:
        rotate_docker_creds(auths, docker_config_file)

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    logging.getLogger('apscheduler').setLevel(logging.WARN)

    config = read_env_vars()

    auths = Auths(config['DOCKER_CREDS'])

    scheduler = BlockingScheduler()
    scheduler.add_job(
        update_current_auth_schedule,
        'interval',
        minutes=config['SCHEDULE_MINS'],
        args=(auths, config['DOCKER_CONFIG_PATH'], config['REFRESH_THRESHOLD']),
        next_run_time=datetime.now()
    )
    logging.info(f'Scheduled to run every {config["SCHEDULE_MINS"]} mins')
    scheduler.start()

if __name__ == '__main__':
    main()
