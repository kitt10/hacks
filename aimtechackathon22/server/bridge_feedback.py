from requests import post, HTTPError
from json import dumps, JSONDecodeError
import sys


URI_BASE = ''
EP_DIALOG = URI_BASE+'/dialog/'


def post_(ep, body):
    
    try:
        response = post(ep, body)

        if response.status_code == 200:
            try:
                return response.json()
            except JSONDecodeError:
                print('E: Response is not of JSON format.')
                return {}
        else:
            print('E: Not available, try again. Status code:', response.status_code)
            return {}

    except HTTPError as http_err:
        print('E: HTTP error occurred:', http_err)


if __name__ == '__main__':

    text = sys.argv[1].lower()

    for variant in ('ano', 'yes', 'ok', 'super', 'dobře', 'správně', 'výborně', 'paráda'):
        if text in variant or variant in text:
            text = 'ok'
            break

    for variant in ('ne', 'nene', 'špatně', 'vůbec', 'ani náhodou'):
        if text in variant or variant in text:
            text = 'no'
            break

    text = text if text in ('ok', 'no') else 'no'

    body = {
        'feedback': text,
        'device': 'voice'
    }

    answer = post(EP_DIALOG, dumps(body)).json()['answer']
    
    print(answer)