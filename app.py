import pathlib
import sys

cur = pathlib.Path(__file__).resolve().parent
sys.path.append('{}/'.format(cur.parent))

import json, os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest, OrdersGetRequest
from typing import Optional

app = FastAPI()

load_dotenv(dotenv_path=".env")
load_dotenv()

client_id = os.environ['client_id']
client_secret = os.environ['client_secret']

environment = SandboxEnvironment(client_id=client_id,
                                 client_secret=client_secret)
client = PayPalHttpClient(environment)

config = {
    "return_url": "http://0.0.0.0:8000/paypal/success",
    "cancel_url": "http://0.0.0.0.8000/paypal/cancel"
}


@app.get("/paypal/create")
def create_order(value: str = '100.00', currency_code: str = 'USD'):
    request = OrdersCreateRequest()
    request.prefer('return=representation')
    request.request_body({
        "intent":
        "CAPTURE",
        #用於處理付款後的網頁跳轉
        "application_context": {
            'return_url': config['return_url'],
            'cancel_url': config['cancel_url']
        },
        "purchase_units": [{
            "amount": {
                "currency_code": currency_code,
                "value": value
            }
        }]
    })

    try:
        response = client.execute(request)
        print(f'Success to Create Order. ID: {response.result.id}')
        for link in response.result.links:
            if link.rel == "approve":
                return {
                    'order_id': response.result.id,
                    'order_link': link.href
                }
        return {'order_id': None, 'order_link': None}
    except IOError as ioe:
        print(f'Failed to Create Order: {ioe}')
        return {'order_id': None, 'order_link': None}
    except Exception as e:
        print(f'Other Error: {e}')
        return {'order_id': None, 'order_link': None}


@app.get("/paypal/status")
def get_order_status(order_id: str):
    request = OrdersGetRequest(order_id)
    try:
        response = client.execute(request)
        return response.result.status
    except IOError as ioe:
        print(f'Failed to get order status: {ioe}')
        return None
    except Exception as e:
        print(f'Other Errors: {e}')
        return None


async def get_order_id(token: Optional[str] = None):
    if not token:
        raise HTTPException(status_code=400, detail="No order ID provided")
    return token


@app.get("/paypal/success")
async def paypal_success(order_id: str = Depends(get_order_id)):
    try:
        request = OrdersCaptureRequest(order_id)
        response = client.execute(request)

        if response.result.status == "COMPLETED":
            return JSONResponse(content={
                "message": "Payment successful",
                "order_id": order_id
            })
        else:
            raise HTTPException(
                status_code=400,
                detail=
                f"Payment not completed. Status: {response.result.status}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/paypal/cancel")
async def paypal_cancel(request: Request,
                        order_id: str = Depends(get_order_id)):
    try:
        order_request = OrdersGetRequest(order_id)
        response = client.execute(order_request)

        if response.result.status == "CREATED":
            return JSONResponse(content={
                "message": "Order cancelled successfully",
                "order_id": order_id
            })
        elif response.result.status in ["COMPLETED", "APPROVED"]:
            return JSONResponse(content={
                "message":
                "Order already processed, please initiate a refund if needed",
                "order_id": order_id
            },
                                status_code=409)
        else:
            return JSONResponse(content={
                "message":
                f"Order in {response.result.status} status, manual review required",
                "order_id": order_id
            },
                                status_code=202)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/paypal/webhook")
async def paypal_webhook(request: Request):
    try:
        payload = await request.json()
        event_type = payload['event_type']

        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            order_id = payload['resource']['id']
            print(f"Payment completed for order {order_id}")
            return {"status": "success"}

        elif event_type == "PAYMENT.CAPTURE.DENIED":
            print("Payment denied")
            return {"status": "payment denied"}
        return {"status": "unhandled event"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except KeyError as e:
        raise HTTPException(status_code=400,
                            detail=f"Missing key in payload: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    html_content = """
    <html>
        <head>
            <title>Paypal</title>
        </head>
        <body>
            Welcome to the PayPal integration API. <br>
            Check <a href="/docs">the link</a> for more details.
        </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=os.environ['host'], port=int(os.environ['port']))
