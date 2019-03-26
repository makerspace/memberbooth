from src import maker_admin
import argparse

def main():
    parser = argparse.ArgumentParser("")

    parser.add_argument("token", help="Token for logging in to Makeradmin")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).")

    ns = parser.parse_args()
    client = maker_admin.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)
    print(client.is_logged_in())


if __name__ == "__main__":
    main()
