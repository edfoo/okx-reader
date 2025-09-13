from nicegui import ui
import requests
import hmac
import hashlib
import base64
from datetime import datetime, timezone
import asyncio
import os

# Define the columns for the table based on the screenshot and API fields
columns = [
    {'name': 'instId', 'label': 'Symbol', 'field': 'instId', 'sortable': True},
    {'name': 'size', 'label': 'Size', 'field': 'size', 'sortable': True},
    {'name': 'markPx', 'label': 'Mark Price', 'field': 'markPx', 'sortable': True},
    {'name': 'entryPx', 'label': 'Entry Price', 'field': 'entryPx', 'sortable': True},
    {'name': 'liqPx', 'label': 'Est Liq Price', 'field': 'liqPx', 'sortable': True},
    {'name': 'bePx', 'label': 'Breakeven Price', 'field': 'bePx', 'sortable': True},
    {'name': 'upl', 'label': 'Floating PnL', 'field': 'upl', 'sortable': True},
    {'name': 'mgnRatio', 'label': 'Maintenance Margin Ratio', 'field': 'mgnRatio', 'sortable': True},
    {'name': 'margin', 'label': 'Margin', 'field': 'margin', 'sortable': True},
    {'name': 'lever', 'label': 'Leverage', 'field': 'lever', 'sortable': True},
    {'name': 'mgnMode', 'label': 'Mode', 'field': 'mgnMode', 'sortable': True},
    {'name': 'adl', 'label': 'ADI', 'field': 'adl', 'sortable': True},
]

# UI elements
ui.label('OKX Positions Viewer')
refresh_sec = ui.number('Refresh every (seconds)', value=120, min=1)
start_button = ui.button('Update Refresh Rate')
table = ui.table(columns=columns, rows=[], row_key='instId').style('width: 100%; font-weight: bold;')
table.add_slot('body-cell-upl', '''
<q-td key="upl" :props="props">
    <span :class="parseFloat(props.value.split(' ')[0]) > 0 ? 'text-green' : 'text-negative'">{{ props.value }}</span>
</q-td>
''')

chart = ui.echart({
    'title': {'text': 'Floating PnL Graph'},
    'xAxis': {'type': 'category', 'data': []},
    'yAxis': {'type': 'value', 'title': {'text': 'PnL (USD)'}},
    'series': [{'type': 'bar', 'name': 'PnL', 'data': []}],
})

log_text = ui.textarea('Debug Logs').props('readonly').style('width: 100%; height: 200px;')

def fetch_positions(api_key, secret, passphrase):
    base_url = 'https://www.okx.com'
    request_path = '/api/v5/account/positions'
    params = {'instType': 'SWAP'}
    query = '?' + '&'.join(f"{k}={v}" for k, v in params.items())
    full_path = request_path + query
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    method = 'GET'
    body = ''
    prehash = timestamp + method + full_path + body
    sign = base64.b64encode(hmac.new(secret.encode('utf-8'), prehash.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    resp = requests.get(base_url + full_path, headers=headers)
    return resp.json()

def format_upl(upl_str, upl_ratio_str):
    try:
        upl_val = float(upl_str)
        formatted_upl = f"{round(upl_val, 4):.4f}"
        formatted_ratio = f"{float(upl_ratio_str):.4f}"
        return f"{formatted_upl} ({formatted_ratio}%)"
    except:
        return f"{upl_str} ({upl_ratio_str}%)"

def format_number(val):
    try:
        num = float(val)
        return f"{round(num, 4):.4f}"
    except:
        return str(val)

async def update_table():
    ak = os.getenv('OKX_API_KEY')
    sk = os.getenv('OKX_SECRET')
    pp = os.getenv('OKX_PASSPHRASE')
    rs = refresh_sec.value
    if not ak or not sk or not pp:
        log_text.value += f"[{datetime.now().strftime('%H:%M:%S')}] Error: Missing environment variables.\n"
        log_text.update()
        ui.notify('Please set OKX_API_KEY, OKX_SECRET, and OKX_PASSPHRASE environment variables.')
        return
    try:
        data = fetch_positions(ak, sk, pp)
        log_text.value += f"[{datetime.now().strftime('%H:%M:%S')}] Fetching positions...\n"
        log_text.update()
        if data['code'] == '0':
            positions = data['data']
            rows = []
            categories = []
            pnl_data = []
            for p in positions:
                if p['instType'] != 'SWAP':
                    continue
                size = f"{p.get('notionalUsd', p['pos'])} USD" if p.get('notionalUsd') else f"{p['pos']} {p.get('ccy', '')}"
                upl_value = float(p['upl']) if p['upl'] else 0
                formatted_upl = format_upl(p['upl'], p['uplRatio'])
                row = {
                    'instId': p['instId'],
                    'size': size,
                    'markPx': format_number(p['markPx']),
                    'entryPx': format_number(p['avgPx']),
                    'liqPx': format_number(p['liqPx']),
                    'bePx': format_number(p.get('bePx', '')),
                    'upl': formatted_upl,
                    'mgnRatio': format_number(p['mgnRatio']),
                    'margin': format_number(p['margin']),
                    'lever': format_number(p['lever']),
                    'mgnMode': p['mgnMode'],
                    'adl': format_number(p.get('adl', '')),
                }
                rows.append(row)
                categories.append(p['instId'])
                pnl_data.append(upl_value)
            table.rows = rows
            table.update()
            chart.options['xAxis']['data'] = categories
            chart.options['series'][0]['data'] = pnl_data
            chart.update()
            log_text.value += f"[{datetime.now().strftime('%H:%M:%S')}] Positions updated successfully.\n"
            log_text.update()
        else:
            log_text.value += f"[{datetime.now().strftime('%H:%M:%S')}] Error: {data['msg']}\n"
            log_text.update()
            ui.notify(f"Error: {data['msg']}")
    except Exception as e:
        log_text.value += f"[{datetime.now().strftime('%H:%M:%S')}] Exception: {str(e)}\n"
        log_text.update()
        ui.notify(f"Exception: {str(e)}")

async def start_refresh():
    while True:
        await update_table()
        await asyncio.sleep(refresh_sec.value)

def on_start():
    asyncio.create_task(start_refresh())

start_button.on('click', on_start)

ui.run()