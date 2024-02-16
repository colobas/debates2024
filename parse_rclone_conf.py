import sys
import configparser
import json
import base64


def main():
    config = configparser.ConfigParser()
    # decode config from base64 stdin

    stdin = input()
    conf_str = base64.b64decode(stdin).decode("utf-8")
    config.read_string(conf_str)
    conf = config["debates"]

    try:
        refresh_token = json.loads(conf["token"])["refresh_token"]
    except (KeyError, json.decoder.JSONDecodeError):
        print("Failed to decode.")
        print("stdin was:\n", stdin)
        sys.exit(1)

    out = {
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "refresh_token": refresh_token,
    }

    print(json.dumps(out))


if __name__ == "__main__":
    main()
