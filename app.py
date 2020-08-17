#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_migrate import Migrate
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default = False)
    seeking_description = db.Column(db.String(500))

    artists = db.relationship('Artist', secondary = 'Shows',
        backref=db.backref('pages', lazy=True))

    def __repr__(self):
      return f'<Venue {self.id} {self.name} located at {self.city} {self.state}'
    
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default = False)

    def __repr(self):
      return f'<Artist {self.id} {self.name} located at {self.city} {self.state}'

# An association table connect Artist and Venue models
Shows = db.Table('Shows',
  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id')),
  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id')),
  db.Column('start_time', db.DateTime))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.all()
  # Select distinct state and city pairs
  areas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  data = []

  for area in areas:
      data.append({
        "city": area[0],
        "state": area[1],
        "venues": []
      })
  
  for venue in venues:
    
    shows = db.session.query(Shows).filter(Shows.c.venue_id == venue.id).all()
    num_upcoming_shows = 0

    # Compare the show time with current time
    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1

    for area in data:
      if (venue.city == area['city']) and (venue.state == area['state']):
        area['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": num_upcoming_shows
        })
    
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Implement search on artists with partial string search.  (case-insensitive)
  search_term = request.form.get('search_term', '')
  results = Venue.query.filter(Venue.name.ilike('%' + search_term + '%'))
  data = []

  for result in results: 
    shows = db.session.query(Shows).filter(Shows.c.venue_id == result.id).all()
    num_upcoming_shows = 0

  # Compare the show time with current time
    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1

    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": num_upcoming_shows
    })

  response = {
    "count": results.count(),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # Shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id)
  shows = db.session.query(Shows).filter(Shows.c.venue_id == venue_id).all()
  all_shows = []
  past_shows = []
  upcoming_shows = []

  for show in shows:
    artists = Artist.query.filter(Artist.id == show.artist_id).all()
    for artist in artists:
      show_info = {
        "artist_id" : artist.id,
        "artist_name": artist.name,
        "atrist_image_link": artist.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
      }

    if show.start_time >= datetime.now():
      upcoming_shows.append(show_info)
    else:
      past_shows.append(show_info)
      
  data = {
    "id": venue.id,
    "name": venue.name,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link":venue.facebook_link,
    "seeking_talent":venue.seeking_talent,
    "seeking_description":venue.seeking_description,
    "image_link":venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count":len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    new_venue = Venue(
      name = request.form.get('name'),
      city = request.form.get('city'),
      state = request.form.get('state'),
      address = request.form.get('address'),
      phone = request.form.get('phone'),
      facebook_link = request.form.get('facebook_link'),
      image_link = request.form.get('image_link'),
      website = request.form.get('website'),
      seeking_talent = request.form.get('seeking_talent'),
      seeking_description = request.form.get('seeking_description')
    )
    db.session.add(new_venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occured, Venue ' + request.form['name'] + ' cannot be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occured, Venue' + request.form['name'] + 'cannot be deleted.')
  else:
    flash('Venue' + request.form['name']+ 'was successfullt deleted!')
  return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # replace with real data returned from querying the database
  data = []
  artists = Artist.query.all()
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. (case-insensitive)
  search_term = request.form.get('search_term', '')
  results = Artist.query.filter(Artist.name.ilike("%" + search_term + "%"))
  data = []
  
  for result in results:
    shows = db.session.query(Shows).filter(Shows.c.artist_id == result.id).all()
    num_upcoming_shows = 0

    for show in shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1

    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": num_upcoming_shows
    })

  response = {
    "count": results.count(),
    "data" : data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # replace with real venue data from the venues table, using venue_id

  artist = Artist.query.get(artist_id)
  shows = db.session.query(Shows).filter(Shows.c.artist_id == artist_id).all()
  all_shows = []
  past_shows = []
  upcoming_shows = []

  for show in shows:
    venues = Venue.query.filter(Venue.id == show.venue_id).all()
    for venue in venues:
      show_info = {
        "venue_id" : venue.id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
      }

    if show.start_time >= datetime.now():
      upcoming_shows.append(show_info)
    else:
      past_shows.append(show_info)
      
  data = {
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link":artist.facebook_link,
    "seeking_venue":artist.seeking_venue,
    "image_link":artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count":len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get(artist_id)
  form = ArtistForm(
    name=artist.name,
    city=artist.city,
    state=artist.state,
    genres=artist.genres,
    phone=artist.phone,
    facebook_link=artist.facebook_link,
    website=artist.website,
    image_link=artist.image_link,
    seeking_venue=artist.seeking_venue
  )

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get(artist_id)
    
    # update artist info from form
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.genres = request.form.get('genres')
    artist.phone = request.form.get('phone')
    artist.facebook_link = request.form.get('facebook_link')
    artist.website = request.form.get('website')
    artist.image_link = request.form.get('image_link')
    artist.seeking_venue = request.form.get('seeking_venue')
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occur, update failed.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # Populate form with values from venue with ID <venue_id>
  venue = Venue.query.get(venue_id)
  form = VenueForm(
    id = venue.id,
    name = venue.name,
    genres = venue.genres,
    address = venue.address,
    city = venue.city,
    state = venue.state,
    phone = venue.phone,
    website = venue.website,
    facebook_link = venue.facebook_link,
    seeking_talent = venue.seeking_talent,
    seeking_description  = venue.seeking_description,
    image_link =  venue.image_link
  )
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # Take values from the form submitted, and update existing 
  # venue record with ID <venue_id> using the new attributes

  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form.get('name')
    venue.genres = request.form.get('genres')
    venue.address = request.form.get('address')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.website = request.form.get('website')
    venue.facebook_link = request.form.get('facebook_link')
    venue.seeking_talent = request.form.get('seeking_talent')
    venue.seeking_description = request.form.get('seeking_description')
    venue.image_link = request.form.get('iamge_link')

    db.session.commit()

  except:
    db.session.rollback()
    flash('An error occur, fail to update venue infomation. Please try again.')

  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    new_artist = Artist(
      # Populate values from the form
      name = request.form.get('name'),
      city = request.form.get('city'),
      state = request.form.get('state'),
      genres = request.form.get('genres'),
      phone = request.form.get('phone'),
      facebook_link = request.form.get('facebook_link'),
      website = request.form.get('website'),
      image_link = request.form.get('image_link'),
      seeking_venue = request.form.get('seeking_venue')
    )
    # If db insert successful, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    db.session.add(new_artist)
    db.session.commit()
  except:
  # On unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occur, fail to update venue infomation. Please try again.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = db.session.query(Shows).all()
  for show in shows:
    artist_info = Artist.query.get(show.venue_id)
    venue_info = Venue.query.get(show.venue_id)
    data.append({
      "venue_id": show.venue_id,
      "venue_name": venue_info.name,
      "artist_id": show.artist_id,
      "artist_name": artist_info.name,
      "artist_image_link": artist_info.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    insert_statement = Shows.insert().values(
      artist_id = request.form.get('artist_id'),
      venue_id = request.form.get('venue_id'),
      start_time = request.form.get('start_time')
    )
    db.session.execute(insert_statement)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
