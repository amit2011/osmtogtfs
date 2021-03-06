"""osmtogtfs web app"""
import os
import pathlib
import tempfile
import urllib.parse
import urllib.request

import requests
import validators
from flask import Flask, request, send_file, render_template, flash, abort
from werkzeug.utils import secure_filename

from osmtogtfs.cli import main


app = Flask(__name__)
application = app

app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['SECRET_KEY'] = 'super secret string'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method != 'POST':
        return render_template('index.html')

    uploaded_filepath = \
        save_file(request.files['file']) if 'file' in request.files else None

    url = request.form.get('url')

    if not url and not uploaded_filepath:
        flash('Provide a URL or upload a file.')
        return render_template('index.html')

    if not uploaded_filepath and not validators.url(url):
        flash('Not a valid URL.')
        return render_template('index.html')

    filename = uploaded_filepath or dl_osm(url)
    zipfile = create_zipfeed(filename, bool(request.form.get('dummy')))

    return send_file(
        zipfile,
        attachment_filename=pathlib.Path(zipfile).name,
        as_attachment=True)


def save_file(file):
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath


def create_zipfeed(filename, dummy=False):
    zipfile = '{}.zip'.format(filename)
    print('Writing GTFS feed to %s' % zipfile)
    main(filename, '.', zipfile, dummy)
    return zipfile


@app.route('/o2g', methods=['GET'])
def o2g():
    area = request.args.get('area')
    bbox = request.args.get('bbox')
    url = request.args.get('url')

    if area or bbox:
        filepath = dl_osm_from_overpass(area, bbox)
    elif url and validators.url(url):
        filepath = dl_osm_from_url(url)
    else:
        abort(400)

    zipfile = create_zipfeed(
        filepath,
        bool(request.args.get('dummy')))

    return send_file(
        zipfile,
        mimetype='application/zip')


def dl_osm_from_overpass(area, bbox):
    if not area and not bbox:
        raise Exception('At lease area or bbox must be given.')

    overpass_query = build_overpass_query(area, bbox)
    overpass_api = "http://overpass-api.de/api/interpreter"

    filename = tempfile.mktemp(suffix='_overpass.osm')
    resp = requests.post(overpass_api, data=overpass_query)
    if resp.ok:
        with open(filename, 'w') as osm:
            osm.write(resp.content.decode('utf-8'))
        return filename
    else:
        resp.raise_for_status()

    raise Exception("Can't download data form overpass api.")


def build_overpass_query(area, bbox):
    template = """
    {bbox}
    {area}
    (
      rel
        [!"deleted"]
        ["type"="route"]
        ["route"~"tram|subway|bus|ex-bus|light_rail|rail|railway"]
        {area_limit};
    );
    (._; >;);
    out;
    """
    bbox_fmt = ''
    area_fmt = ''
    area_limit_fmt = ''

    if bbox:
        south, west, north, east = bbox.split(',')
        bbox_fmt ='[bbox:{},{},{},{}];'.format(south, west, north, east)

    if area:
        area_fmt ='area["name"="{}"];'.format(area)
        area_limit_fmt ='(area._)'

    return template.format(bbox=bbox_fmt, area=area_fmt, area_limit=area_limit_fmt)


# def dl_bbox(south, west, north, east):
#     bbox_query = """
#     """
#     return requests.post("http://overpass-api.de/api/interpreter")


# def dl_area(name):
#     area_query = """
#     [bbox:47.9485, 7.7066, 48.1161, 8.0049];
#     area["name"="Freiburg"];
#     (
#       rel
#         [!"deleted"]
#         ["type"="route"]
#         ["route"~"tram|subway|bus|ex-bus|light_rail|rail|railway"]
#         (area._);
#     );
#     (._; >;);
#     out;
#     """
#     pass


def dl_osm_from_url(url):
    filename = tempfile.mktemp(suffix=pathlib.Path(url).name)
    local_filename, headers =\
        urllib.request.urlretrieve(url, filename=filename)
    print(local_filename, headers)
    return local_filename


if __name__ == '__main__':
    app.run('0.0.0.0', int(os.getenv('PORT', 3000)), debug=True)
