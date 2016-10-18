from lxml import html

import dateparser
import json
import requests
import time

headers = {
    'human': 'Jackie Kazil',
    'human_twitter': '@jackiekazil',
    'human_email': 'jackiekazil@gmail.com',
    'notes': 'If this causes you issues, please contact me. I am pulling data \
              to analyze it for funsies; possibly will write a blog post.'
}


def convert_datetime(x):
    # example: 'Oct. 2, 2016, 10:13 p.m.'
    x = dateparser.parse(x)
    x = x.strftime('%Y-%m-%dT%H:%M:%S')
    return x


def grab_data(url):

    request = requests.get(url, headers=headers)

    tree = html.fromstring(request.content)

    questions = tree.xpath('//div[2]/p[1]/strong/a/text()')
    q_paths = tree.xpath('//div[2]/p[1]/strong/a/@href')
    vote_count = tree.xpath('//div[1]/div[1]/span/text()')
    submitters = tree.xpath('//div[3]/strong/text()')

    idea_infos = [x.strip('\n').strip() for x in tree.xpath('//div[3]/text()')]
    ignore_list = ['', 'Submitted by:', 'Issue area:']
    idea_dates = [x for x in idea_infos if x not in ignore_list]
    idea_dates = [convert_datetime(x) for x in idea_dates]

    issue_areas = tree.xpath('//div[3]/a/strong/text()')
    issue_paths = tree.xpath('//div[3]/a/@href')

    zip_data = zip(questions, q_paths, vote_count, submitters, idea_dates,
                   issue_areas, issue_paths)

    records = []

    for a, b, c, d, e, f, g in zip_data:
        submit_info = [x.strip() for x in d.split('from')]

        submitter = submit_info[0]
        if len(submit_info) > 1:
            location = submit_info[1]
        else:
            location = None

        record = {
            'question': a,
            'question_path': b,
            'vote_count': int(c),
            'submitters': submitter,
            'submitter_location': location,
            'submission_date': e,
            'issue_area': f,
            'issue_path': g,
        }

        records.append(record)

    return records


if __name__ == '__main__':
    base = 'https://presidentialopenquestions.com/?sort=%2Bvotes&page='
    vote_count = 0
    page_count = 0
    records = []
    first_pass_flag = False

    while True:

        page_count += 1
        page = '%s' % str(page_count)
        url = base + page
        print(url)

        page_records = grab_data(url)
        records += page_records
        print('Success!')

        time.sleep(1)

        # Once cycled through once back to fewest vote, finish
        if page_records[0]['vote_count'] == 2:
            first_pass_flag = True if first_pass_flag == False else True
        if first_pass_flag and page_records[0]['vote_count'] == 1:
            break

    print(len(records))

    with open('data/data_out.json', 'w') as outfile:
        json.dump(records, outfile)
