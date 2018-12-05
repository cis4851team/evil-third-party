from flask import Flask, Markup, make_response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import parse_qs
from flask_heroku import Heroku
import uuid
import sys
import datetime
app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'CIS 4851'
heroku = Heroku(app)
db = SQLAlchemy(app)

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


class UrlTuple(db.Model):
    __tablename__ = "url_tuples"
    id = db.Column(db.Integer, primary_key=True)
    cookie_id = db.Column(db.Text())
    url = db.Column(db.Text())
    timestamp = db.Column(db.Text())

    def __init__(self, cookie_id, url, timestamp):
        self.cookie_id = cookie_id
        self.url = url
        self.timestamp = timestamp


class FingerprintTuple(db.Model):
    __tablename__ = "fingerprint_tuples"
    id = db.Column(db.Integer, primary_key=True)
    cookie_id = db.Column(db.Text())
    fingerprint_hash = db.Column(db.Text())
    timestamp = db.Column(db.Text())

    def __init__(self, cookie_id, fingerprint_hash, timestamp):
        self.cookie_id = cookie_id
        self.fingerprint_hash = fingerprint_hash
        self.timestamp = timestamp


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
        pid = uuid.uuid4().hex
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
        matched_fingerprints = FingerprintTuple.query.filter_by(cookie_id = cookie_id).with_entities(FingerprintTuple.fingerprint_hash)
        [print(f'{pid} > Found linked fingerprint {f} for cookie id {cookie_id}') for f in matched_fingerprints]

        # linked_fingerprint_tuples = filter(
        #     lambda fingerprint_tuple: fingerprint_tuple[0] == cookie_id,
        #     fingerprint_tuples
        # )
        # linked_fingerprints = list(map(
        #     lambda fingerprint_tuple: fingerprint_tuple[1],
        #     linked_fingerprint_tuples
        # ))

        # grab the cookies that are linked to the fingerprints found above
        matched_cookies = FingerprintTuple.query.filter(FingerprintTuple.fingerprint_hash.in_(matched_fingerprints)).with_entities(FingerprintTuple.cookie_id)
        [print(f'{pid} > Found linked cookie {c}') for c in matched_cookies]
        # linked_cookie_tuples = filter(
        #     lambda fingerprint_tuple: fingerprint_tuple[1] in linked_fingerprints,
        #     fingerprint_tuples
        # )
        # linked_cookies = list(map(
        #     lambda fingerprint_tuple: fingerprint_tuple[0],
        #     linked_cookie_tuples
        # ))

        # grab the urls that are linked to the cookies
        matched_urls = UrlTuple.query.filter(UrlTuple.cookie_id.in_(matched_cookies)).with_entities(UrlTuple.url)
        [print(f'{pid} > Found linked url {u}') for u in matched_urls]
        # linked_url_tuples = filter(lambda url_tuple: url_tuple[0] in linked_cookies, url_tuples)
        # linked_urls = list(map(lambda url_tuple: url_tuple[1], linked_url_tuples))

        def parse_url(url_db):
            url = str(url_db)
            print(f'{pid} > Parsing linked url: {url}')
            split = url.split('?')
            if len(split) <= 1:
                return {}
            query_string = split[1]
            return parse_qs(query_string)
        parsed_urls = list(map(parse_url, matched_urls))

        combined_dict = {}

        for parsed_url in parsed_urls:
            print(f'{pid} > Parsed url contents for {parsed_url}')
            print('[%s]' % ', '.join(map(str, parsed_url)))
            for key, values in parsed_url.items():
                if 'name' in key:
                    if 'name' in combined_dict:
                        combined_dict['name'].append(values)
                    else:
                        combined_dict['name'] = values
                else:
                    if key in combined_dict:
                        for value in values:
                            combined_dict[key].append(value)
                    else:
                        combined_dict[key] = values

        names = combined_dict.get('name', [''])

        print(f'{pid} > Extracted names from urls: {names}')
        
        name = names[0]

        print(f'{pid} > Returning message: Gotcha, {name}')

        response = make_response(create_advertisement(f'Gotcha, {name}'))
        return response
        
    # this tuple will be used to track the user on the first-party site
    # and grab PII leaked from the URL
    url_tuple = (cookie_id, url, timestamp)
    url_tuples.append(url_tuple)
    write_url_tuple_to_db(cookie_id, url, timestamp)

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
    write_fingerprint_tuple_to_db(cookie_id, fingerprint, timestamp)
    
    return response

def write_fingerprint_tuple_to_db(cookie_id, fingerprint, timestamp):
    db_data = FingerprintTuple(cookie_id, fingerprint, timestamp)
    log_data = db_data.__dict__.copy()
    del log_data["_sa_instance_state"]
    try:
        db.session.add(db_data)
        db.session.commit()
    except Exception as e:
        print("\n FAILED entry: {}\n".format(jsonify(log_data)))
        print(e)
        sys.stdout.flush()
    return

def write_url_tuple_to_db(cookie_id, url, timestamp):
    db_data = UrlTuple(cookie_id, url, timestamp)
    log_data = db_data.__dict__.copy()
    del log_data["_sa_instance_state"]
    try:
        db.session.add(db_data)
        db.session.commit()
    except Exception as e:
        print("\n FAILED entry: {}\n".format(jsonify(log_data)))
        print(e)
        sys.stdout.flush()
    return

@app.route('/reset')
def reset():
    fingerprint_tuples.clear()
    url_tuples.clear()
    try:
        num_records_deleted = db.session.query(UrlTuple).delete()
        print(f'{num_records_deleted} records deleted from url_tuples table')
        num_records_deleted = db.session.query(FingerprintTuple).delete()
        print(f'{num_records_deleted} records deleted from fingerprint_tuples table')
        db.session.commit()
    except:
        print(f'Error when resetting tables: {sys.exc_info()[0]}')
        print(sys.exc_info()[1])
        db.session.rollback()
        return 'error - check logs'
    return 'success'

@app.route('/url-tuples')
def get_url_tuples():
    try:
        return jsonify(db.session.query(UrlTuple).query().all())
    except:
        print(f'Error when resetting tables: {sys.exc_info()[0]}')
        print(sys.exc_info()[1])
        db.session.rollback()
        return 'error - check logs'

@app.route('/fingerprint-tuples')
def get_fingerprint_tuples():
    try:
        return jsonify(db.session.query(FingerprintTuple).query().all())
    except:
        print(f'Error when resetting tables: {sys.exc_info()[0]}')
        print(sys.exc_info()[1])
        db.session.rollback()
        return 'error - check logs'
