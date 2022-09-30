#!/usr/bin/env python3

import os
from twilio.rest import Client
import requests
import json
from apscheduler.schedulers.blocking import BlockingScheduler
import os

# DECATHLON_CART_ID = os.getenv('DECATHLON_CART_ID')
DECATHLON_REFRESH_TOKEN = os.getenv('DECATHLON_REFRESH_TOKEN')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
TWILIO_TO_NUMBER = os.getenv('TWILIO_TO_NUMBER')
POSTAL_CODE = os.getenv('POSTAL_CODE')

sched = BlockingScheduler()

def make_twilio_call():
    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        url='http://demo.twilio.com/docs/classic.mp3',
        to=TWILIO_TO_NUMBER,
        from_=TWILIO_FROM_NUMBER
    )
    print(call.sid)

def get_decathlon_access_token():
    url = 'https://www.decathlon.in/api/refresh-token'
    data = {
        'refresh_token': DECATHLON_REFRESH_TOKEN
    }
    headers = {
        'content-type': 'application/json'
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token

    return None

def decathlon_add_to_cart(model_id, item_id, access_token):
    data = {
        "postalCode":POSTAL_CODE,
        "cartItems":[
            {
                "itemCode": item_id,
                "lineType": "DELIVERY",
                "modelCode": model_id,
                "quantity": 1,
                "analytics": {"shoppingToolType":"Perso-Reco","shoppingToolValue":"Category_Products_Page-Our Bestsellers-8603864","shoppingToolSubValue":"NA"}
            }
        ],
        "token": access_token
    }

    url = 'https://www.decathlon.in/api/cart/add'
    headers = {
        'content-type': 'application/json'
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f'add to cart status_code: {response.status_code}')
    print('add to cart response json: ', response.json())

@sched.scheduled_job('interval', seconds=30)
def main():
    print('running main now')
    # with open('mtb_st_20.json', 'r') as f:
    with open('riverside_120.json', 'r') as f:
        data = json.load(f)

    url = 'https://www.decathlon.in/api/product/stocks'
    headers = {
        'content-type': 'application/json'
    }
    response = requests.post(url, data=json.dumps(data.get('stocksRequestPayload')), headers=headers)
    print(f'stocks status_code: {response.status_code}')
    response_json = response.json()
    print(response_json)

    if response.status_code == 200:
        if response_json['status'] == True:
            print('product available - adding to cart now!')
            decathlon_access_token = get_decathlon_access_token()
            model_id = data.get('modelId')
            item_ids = data.get('itemIds')

            for item_id in item_ids:
                print(f'attempting to add item {item_id} to cart')
                decathlon_add_to_cart(model_id, item_id, decathlon_access_token)

            print('added to cart - making a call now')
            make_twilio_call()
        else:
            print('product unavailable')
    else:
        raise ValueError('something went wrong')


if __name__ == '__main__':
    # main()
    sched.start()
