from sanic import Sanic, response
from sanic.exceptions import ServerError

from utils import get_monefy_info, write_monefy_info

app = Sanic('Monefy-parser')


@app.route('/')
def handle_request(request):
    return response.text('Hello world!')


@app.get("/get-monefy-info")
async def get_monefy_stat(request):
    monefy_stats = get_monefy_info()
    return response.json(monefy_stats)


@app.get("/write-monefy-info")
async def write_monefy_stat(request):
    write_result = write_monefy_info()
    return response.text(write_result)

@app.get('/verify')
async def verify(request):
    '''Respond to the webhook verification (GET request) by echoing back the challenge parameter.'''

    resp = request.args.get('challenge')
    return response.text(
        resp,
        headers={'Content-Type': 'text/plain','X-Content-Type-Options': 'nosniff'},
        status=200
    )


@app.post('/verify')
async def webhook(request):
    '''Receive a list of changed user IDs from Dropbox and process each.'''

    # Make sure this is a valid request from Dropbox
    signature = request.headers.get('X-Dropbox-Signature')
    if not signature:
        raise ServerError("403", status_code=403)

    write_monefy_info()
    return response.text('webhook handled', status=200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, auto_reload=True, debug=True)
