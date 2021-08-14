# Docker Auth Manager

[Docker Download Rate Limits](https://www.docker.com/increase-rate-limits) are annoying.
`The rate limits of 100 container image requests per six hours for anonymous usage, and 200 container image requests per six hours for free Docker accounts are now in effect.`

* Takes a list of valid Docker account logins
* Checks currently set credentials in docker `config.json` file for number of remaining downloads on a schedule
* If the remaning downloads fall below a threshold, rotates the credentials with one with the highest remaining downloads

## Formatting credentials
For each docker login, generate the basic auth string with (replace `<username>`/`<password>`):
```
echo '<username>:<password>' | base64
```

## Options
| Environment Variable  | Default Value     | Description                                                                                          |
| --------------------- | ----------------- | ---------------------------------------------------------------------------------------------------- |
| `DOCKER_CREDS`        |                   | Comma seperated list of basic auth strings                                                           |
| `DOCKER_CONFIG_PATH`  | `/.docker/config` | Path to the docker `config.json` file                                                                |
| `REFRESH_THRESHOLD`   | 50                | The minimum threshold of remaining downloads for the set of credentials before triggering a rotation |
| `SCHEDULE_MINS`       | 10                | How often to check the current set of creds' remaining downloads                                     |

### Examples
Run with default settings:
```
docker run -d -v "${HOME}/.docker/config.json:/.docker/config" \
    -e DOCKER_CREDS="dXNlcm5hbWUxOnBhc3N3b3JkMQo=,VVNFUk5BTUU6UEFTU1dPUkQK,dVNlUm5BbUU6cEFzU3dPckQK" \
        hotpheex/docker-auth-manager
```

Set configurable options:
```
docker run -d -v "${HOME}/.docker/config.json:/.docker/config" \
    -e DOCKER_CREDS="dXNlcm5hbWUxOnBhc3N3b3JkMQo=,VVNFUk5BTUU6UEFTU1dPUkQK,dVNlUm5BbUU6cEFzU3dPckQK" \
    -e REFRESH_THRESHOLD=100 \
    -e SCHEDULE_MINS=5 \
        hotpheex/docker-auth-manager
```
