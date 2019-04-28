from flask import Flask, jsonify, abort
import requests
from functools import reduce
import re
app = Flask(__name__)


def _request(org, repo, endpoint=""):
    url = f'https://api.github.com/repos/{org}/{repo}'
    if endpoint:
        url += f'/{endpoint}'
    app.logger.info(f'url is {url}')
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return data, response.headers
    abort(response.status_code, f'github says: {response.text}')

def get_repo_info(org, repo, field=''):
    """ return info from repo document
        field could be as "owner.login"
    """
    data, _ = _request(org, repo)
    if field:
        return reduce(lambda x, y: x[y], field.split("."), data)
    return data


def get_prs_count(org, repo):

    data, headers = _request(org, repo, 'pulls')
    if 'Link' in headers:
        pages = re.findall('page=(\d+)', headers['Link'])
        app.logger.info(f'pages: {pages}')
        last_page_num = int(pages[1])
        # get data from last page
        last_page_data, _ = _request(org, repo, f'pulls?page={last_page_num}')
        # number or PRs: 30 per page + amount from last page
        pr_count = (last_page_num - 1) * 30 + len(last_page_data)
        app.logger.info(f'count of PRs: {pr_count}')
        return pr_count

    else:
        return len(data)


@app.route('/<org>/<repo>', methods=['GET'])
def get_issues(org, repo):
    total_issues = get_repo_info(org, repo, 'open_issues_count')
    prs_count = get_prs_count(org, repo)
    opened_issues = total_issues - prs_count
    return jsonify({'opened_issues': opened_issues, 'pr_count': prs_count})


if __name__ == '__main__':
    app.run(debug=True)
