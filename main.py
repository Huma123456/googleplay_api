import argparse
import logging
import os

import requests

import googleplay_api.config as play_conf
from googleplay_api.googleplay import GooglePlayAPI

emulated_device = play_conf.get_option("device")
play_store = None


def get_message(path):
    print(play_store.freeRequest(path))


def get_details(package):
    details, pages = play_store.details(package, True)
    print(details)
    for page in pages.values():
        print(page)


def get_bulk_details(packages):
    print(play_store.bulkDetails(packages, True, True))


def search(query):
    print(play_store.getPages(play_store.search(query)))


def list_category(cat, subcat):
    if not cat and not subcat:
        print(play_store.browse())
    else:
        print(play_store.getPages(play_store.list(cat=cat, ctr=subcat)))


def get_similar(package):
    print(play_store.getPages(play_store.listSimilar(package)))


def get_latest_versioncode(package):
    """
    Gets the version code of latest available apk

    :param package: app's package, e.g. com.android.chrome
    :return: version code of latest available apk
    """
    # noinspection PyPep8Naming
    detailsResponse = play_store.details(package)
    return detailsResponse.docV2.details.appDetails.versionCode


def download_apk(package, version_code, output_path):
    """
    :param package: app's package, e.g. com.android.chrome
    :param version_code: which version of the app you want to download
    :param output_path: where to save the apk file
    """
    if not version_code:
        version_code = get_latest_versioncode(package)
        print("Latest Version Code: {0}".format(version_code))
    data = play_store.download(package, version_code, progressBar=False)
    if not data:
        print("Error downloading apk.")
        return
    # warning: we must emulate an ATOMIC write to avoid unfinished files.
    # To do so, we use the os.rename() function that should always be atomic under
    # certain conditions (https://linux.die.net/man/2/rename)
    with open(output_path + ".temp", "wb") as f:
        f.write(data)
    os.rename(output_path + ".temp", output_path)


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Unofficial PlayStore python interface', add_help=True
    )
    parser.add_argument('--request', action="store", dest='request_path',
                        help='Do a generic request, useful for deugging')
    parser.add_argument('--details', action="store", dest='package_to_detail', help='Shows various details for the '
                                                                                    'given package')
    parser.add_argument('--search', action="store", dest='query', help='Search the playstore')
    parser.add_argument('--similar', action="store", dest='package_similar', help='Shows various packages similar '
                                                                                  'to the given package')
    parser.add_argument('--bulk-details', action="store", dest='packages_to_detail', nargs='+', type=str,
                        help='Shows details for a list of packages')
    list_group = parser.add_argument_group()
    list_group.add_argument('--list', action="store_true", dest='list',
                            help='List the categories avilable on playstore. If --category is specified, lists the '
                                 'subcategories of the specified category. If --subcategory is also specified, lists '
                                 'the app in the subcategory.')
    list_group.add_argument('--category', action="store", dest='cat',
                            help='Specify a certain category (e.g. GAME_ARCADE)')
    list_group.add_argument('--subcategory', action="store", dest='subcat',
                            help='Specify a certain subcategory (e.g. apps_topselling_free)')
    group = parser.add_argument_group()
    group.add_argument('--download', action="store", dest='package_to_download', help='Download the apk with given '
                                                                                      'package name')
    group.add_argument('-o', action="store", dest='output_folder', help='(optional) Where to '
                                                                        'save the downloaded apk')
    group.add_argument('--version', action="store", dest='version_code', help='(optional) Version Code of the apk'
                                                                              'to download (default: latest)')
    parser.add_argument('--remote-token', action="store", dest='token_url', help='If the authentication token should be'
                                                                                 ' retrieved from a remote server')
    group_proxy = parser.add_argument_group()
    group_proxy.add_argument('--http-proxy', action="store", dest='http_proxy', help='http proxy, ONLY used for'
                                                                                     'Play Store requests!')
    group_proxy.add_argument('--https-proxy', action="store", dest='https_proxy', help='https proxy, ONLY used for'
                                                                                       'Play Store requests!')

    results = parser.parse_args()

    proxies = None
    if results.http_proxy:
        if proxies is None:
            proxies = {}
        proxies["http"] = results.http_proxy
    if results.https_proxy:
        if proxies is None:
            proxies = {}
        proxies["https"] = results.https_proxy
    global play_store
    play_store = GooglePlayAPI(throttle=True, proxies=proxies)
    token = None
    if results.token_url:
        response = requests.get(results.token_url)
        token = response.text
        print("Using auth token: {0}".format(token))
    play_store.login(authSubToken=token)

    if results.request_path:
        get_message(results.request_path)
        return

    if results.package_to_detail:
        get_details(results.package_to_detail)
        return

    if results.query:
        search(results.query)
        return

    if results.packages_to_detail:
        get_bulk_details(results.packages_to_detail)
        return

    if results.package_similar:
        get_similar(results.package_similar)
        return

    if results.list:
        list_category(results.cat, results.subcat)
        return

    if results.package_to_download:
        package = results.package_to_download
        version = results.version_code
        output_folder = results.output_folder
        if output_folder:
            os.path.join(output_folder, package + ".apk")
        else:
            output_folder = package + ".apk"
        download_apk(results.package_to_download, version, output_folder)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
