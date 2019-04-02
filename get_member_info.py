from src import maker_admin
import argparse

def main():
    parser = argparse.ArgumentParser("")

    parser.add_argument("token", help="Token for logging in to Makeradmin")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).")
    parser.add_argument("tagid", type=int, help="The ID of the tag")

    ns = parser.parse_args()
    client = maker_admin.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)
    r = client.is_logged_in()
    print("Logged in: ", r)

    r = client.get_tag_info(ns.tagid)
    print("Key info: ", r)


if __name__ == "__main__":
    main()
