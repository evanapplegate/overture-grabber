# overture-grabber
 - Drag a box, get some overture data.
 This repo has a lotta garbage, I was trying to run it on Heroku but immediately exceeded by cheapo $7/mo quotas.
Install gunicorn > run `gunicorn --worker-class gevent overture_grabber:app`
Or install Flask > run `python overture_grabber.py`
