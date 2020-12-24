#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime 

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

migrate = Migrate(app, db)


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venu = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String())


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    image_link = db.Column(db.String(500))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    start_time = db.Column(db.DateTime(), nullable=False)


class City(db.Model):
    __tablename__ = 'City'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    state = db.Column(db.String(120))
    venues = db.relationship('Venue', backref='City')

class ArtistGenres(db.Model):
    __tablename__ = 'ArtistGenres'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    name = db.Column(db.String)


class VenueGenres(db.Model):
    __tablename__ = 'VenueGenres'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    name = db.Column(db.String)    


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value
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
  cities = db.session.query(City).all() 
  return render_template('pages/venues.html', cities=cities)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
  count = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).count()

  return render_template('pages/search_venues.html', result=result, count=count, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter(Venue.id == venue_id).first()
  genres = VenueGenres.query.filter(VenueGenres.venue_id == venue_id).all()
  city = City.query.filter(City.id == venue.city_id).first()

  past_shows_count = Show.query.filter(Show.venue_id == venue_id, Show.start_time <= datetime.datetime.now()).count()
  upcoming_shows_count = Show.query.filter(Show.venue_id == venue_id, Show.start_time > datetime.datetime.now()).count()

  past_shows = Show.query.join(Artist, Show.artist_id == Artist.id).add_entity(Artist).filter(Show.venue_id == venue_id, Show.start_time <= datetime.datetime.now()).all()
  upcoming_shows = Show.query.join(Artist, Show.artist_id == Artist.id).add_entity(Artist).filter(Show.venue_id == venue_id, Show.start_time > datetime.datetime.now()).all()
    
  return render_template('pages/show_venue.html', venue=venue, genres=genres, city=city, shows=shows,past_shows=past_shows, past_shows_count=past_shows_count, upcoming_shows=upcoming_shows, upcoming_shows_count=upcoming_shows_count)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  cities = db.session.query(City).all() 

  return render_template('forms/new_venue.html', form=form, cities=cities)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False      
    venueName = '' # Declaring the variable outside, in order to show it in the Flash message in case of an error 

    try:
      venueName = request.form['name']
      venue=Venue(name=venueName, city_id=request.form['city_id'], address=request.form['address'], phone=request.form['phone'], facebook_link=request.form['facebook_link'], website_link=request.form['website_link'], image_link=request.form['image_link'])

      db.session.add(venue)
      db.session.commit()

      venueName = venue.name

      genres = name=request.form.getlist('genres')

      # Looping through the genres to insert them into thier table
      for genre in genres:  
        venueGenres = VenueGenres(venue_id=venue.id, name=genre)
        db.session.add(venueGenres)
        db.session.commit()        

    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
      flash('An error occurred. Venue: ' + venueName + ' could not be listed.', 'error')
    else:
      flash('Venue: ' + venueName + ' was successfully listed!')
    
    return render_template('pages/home.html')

@app.route('/venues/delete/<venue_id>', methods=['GET'])
def delete_venue(venue_id):
    error = False
    venueName = ''

    try:      
      venue = Venue.query.filter(Venue.id == venue_id).first()

      venueName = venue.name

      genres = VenueGenres.query.filter(VenueGenres.venue_id == venue_id).all()
      
      # Deleting the genres first to prevent and forien key constraints
      for genre in genres: 
        db.session.delete(genre)
        db.session.commit()     

      db.session.delete(venue)
      db.session.commit()      
        
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
      flash('An error occurred whilte deleting the venue', 'error')
    else:
      flash('Venue: ' + venueName + ' was successfully deleted!')
    
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
  count = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).count()

  return render_template('pages/search_artists.html', result=result, count=count, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).first()
  genres = ArtistGenres.query.filter(ArtistGenres.artist_id == artist_id).all()
  city = City.query.filter(City.id == artist.city_id).first()

  past_shows_count = Show.query.filter(Show.artist_id == artist_id, Show.start_time <= datetime.datetime.now()).count()
  upcoming_shows_count = Show.query.filter(Show.artist_id == artist_id, Show.start_time > datetime.datetime.now()).count()

  past_shows = Show.query.join(Venue, Show.venue_id == Venue.id).add_entity(Venue).filter(Show.artist_id == artist_id, Show.start_time <= datetime.datetime.now()).all()
  upcoming_shows = Show.query.join(Venue, Show.venue_id == Venue.id).add_entity(Venue).filter(Show.artist_id == artist_id, Show.start_time > datetime.datetime.now()).all()
    
  return render_template('pages/show_artist.html', artist=artist, genres=genres, city=city, shows=shows,past_shows=past_shows, past_shows_count=past_shows_count, upcoming_shows=upcoming_shows, upcoming_shows_count=upcoming_shows_count)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  cities = db.session.query(City).all()   
  artist = Artist.query.filter(Artist.id == artist_id).first()

  return render_template('forms/edit_artist.html', form=form, artist=artist, cities=cities)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  artistName = ''

  try:
    artistName = request.form['name']
    artist = Artist.query.filter(Artist.id == artist_id).first()
    artist.name = artistName
    artist.city_id=request.form['city_id']
    artist.phone=request.form['phone']
    artist.facebook_link=request.form['facebook_link']

    db.session.commit()

    genres = ArtistGenres.query.filter(ArtistGenres.artist_id == artist_id).all()

    #Deleting the old genres, in order to insert the new ones
    for genre in genres:
      db.session.delete(genre)
      db.session.commit()     

    genres = name=request.form.getlist('genres')

    for genre in genres:
      artistGenres = ArtistGenres(artist_id=artist.id, name=genre)
      db.session.add(artistGenres)
      db.session.commit()        

  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()

  if error:
    flash('An error occurred. Artist: ' + artistName + ' could not be updated.', 'error')
  else:
    flash('Artist: ' + artistName + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  cities = db.session.query(City).all()  
  venue = Venue.query.filter(Venue.id == venue_id).first()

  return render_template('forms/edit_venue.html', form=form, venue=venue, cities=cities)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  venueName = ''

  try:
    venueName = request.form['name']
    venue = Venue.query.filter(Venue.id == venue_id).first()
    venue.name = venueName
    venue.city_id=request.form['city_id']
    venue.address=request.form['address']
    venue.phone=request.form['phone']
    venue.facebook_link=request.form['facebook_link']

    db.session.commit()

    genres = VenueGenres.query.filter(VenueGenres.venue_id == venue_id).all()

    for genre in genres:
      db.session.delete(genre)
      db.session.commit()     

    genres = name=request.form.getlist('genres')

    for genre in genres:
      venueGenres = VenueGenres(venue_id=venue.id, name=genre)
      db.session.add(venueGenres)
      db.session.commit()        

  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()

  if error:
    flash('An error occurred. Venue: ' + venueName + ' could not be updated.', 'error')
  else:
    flash('Venue: ' + venueName + ' was successfully updated!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  cities = db.session.query(City).all() 

  return render_template('forms/new_artist.html', form=form, cities=cities)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    artistName = ''

    try:
      artistName = request.form['name']
      artist=Artist(name=artistName, city_id=request.form['city_id'], phone=request.form['phone'], facebook_link=request.form['facebook_link'])
   
      db.session.add(artist)  
      db.session.commit()
  
      artistName = artist.name

      genres = name=request.form.getlist('genres')
      
      for genre in genres:
        artistGenres = ArtistGenres(artist_id=artist.id, name=genre)
        db.session.add(artistGenres)
        db.session.commit()       

    except:
        db.session.rollback()
        error = True
        flash(sys.exc_info())
    finally:
        db.session.close()

    if error:
      flash('An error occurred. Artist: ' + artistName + ' could not be listed.', 'error')
    else:
      flash('Artist: ' + artistName + ' was successfully listed!')
    
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = Show.query.join(Artist, Show.artist_id == Artist.id).add_entity(Artist).join(Venue, Show.venue_id == Venue.id).add_entity(Venue).all()   
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/search', methods=['POST'])
def search_shows():
  search_term = request.form.get('search_term', '')
  result = Show.query.join(Artist, Show.artist_id == Artist.id).add_entity(Artist).join(Venue, Show.venue_id == Venue.id).add_entity(Venue).filter(Artist.name.ilike('%' + search_term + '%') | Venue.name.ilike('%' + search_term + '%')).all() 
  count = Show.query.join(Artist, Show.artist_id == Artist.id).add_entity(Artist).join(Venue, Show.venue_id == Venue.id).add_entity(Venue).filter(Artist.name.ilike('%' + search_term + '%') | Venue.name.ilike('%' + search_term + '%')).count()

  return render_template('pages/search_shows.html', result=result, count=count, search_term=search_term)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  errorMessage = ''
  try:
    show = Show(artist_id=request.form['artist_id'], venue_id=request.form['venue_id'], start_time=request.form['start_time'])

    db.session.add(show)
    db.session.commit()

  except:
      db.session.rollback()
      error = True
      
      if(Artist.query.filter(Artist.id == request.form['artist_id']).count() == 0):
        errorMessage = 'The artist you have entered was not found.'
      elif(Venue.query.filter(Venue.id == request.form['venue_id']).count() == 0):
        errorMessage = 'The venue you have entered was not found.'
      else:
        errorMessage = 'An error occurred, the show could not be listed.'
  finally:
      db.session.close()

  if error:
    flash(errorMessage, 'error')
  else:
    flash('Show was successfully listed!')
  
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
