import configparser
import json
import base64


def main():
    config = configparser.ConfigParser()
    # decode config from base64 stdin

    conf_str = base64.b64decode(input()).decode("utf-8")
    config.read_string(conf_str)
    conf = config["debates"]

    refresh_token = json.loads(conf["token"])["refresh_token"]

    out = {
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "refresh_token": refresh_token,
    }

    print(json.dumps(out))


if __name__ == "__main__":
    main()
