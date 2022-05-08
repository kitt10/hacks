from requests import post
from json import dumps


URI_BASE = ''
EP_DIALOG = URI_BASE+'/dialog/'


if __name__ == '__main__':
    while True:
        inp = input('> ')
        print(f'Sent: {inp}')

        is_feedback = inp == 'ok' or inp == 'no'
        key = 'feedback' if is_feedback else 'message'
        
        body = {
            key: inp,
            'device': 'console'
        }

        ans = post(EP_DIALOG, dumps(body)).json()['answer']
        print(f'>> {ans}')