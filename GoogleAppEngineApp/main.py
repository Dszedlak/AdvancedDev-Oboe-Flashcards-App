#Imports Here for various Libraries and modules
from flask import Flask, render_template, request, redirect, url_for
from google.cloud import datastore
from datetime import datetime, timedelta
import pytz
from google.auth.transport import requests
from flask_bootstrap import Bootstrap
import google.oauth2.id_token
import html
from random import random, choices
#End of imports block

firebase_request_adapter = requests.Request()

app = Flask(__name__) #Initiate Flask
Bootstrap(app) #Initiatee Bootstrap
db = datastore.Client() #Initiate datastore client instance

@app.route('/', methods=['GET', 'POST'])
def home():
	id_token = request.cookies.get("token") #gets value of current id_token
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter) #gets user data from id_token
	decks = fetch_decks(claims['sub'])
	
	if request.method =='POST':
		current_deck_name=html.escape(request.form['deck_name']) #HTML escape used for escaping illegal characters 
		new_deck_name = html.escape(request.form['new_deck_name'])
		ancestor = db.key('User', claims['sub'], 'Deck', current_deck_name)
		deck = db.get(ancestor) #query datastore for current deck and replace previous deckname with new deck name
		deck['deck_name']=new_deck_name
		db.put(deck)
		return redirect(url_for('home'))
		
	return render_template('home.html', user_data=claims, decks=decks)
	
#Login
@app.route('/login', methods=['GET']) 
def login():
    return render_template('login.html')
	
#returns HTML template with contents explaining the functionality of Oboe
@app.route('/about', methods=['GET']) 
def about():
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
	decks = fetch_decks(claims['sub'])
	return render_template('about.html',user_data=claims)

#returns HTML template with a list of useful resources
@app.route('/usefulRecources', methods=['GET'])
def useful_recources():
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
	decks = fetch_decks(claims['sub'])
	return render_template('usefulRecources.html', user_data=claims)
	
#Returns a HTML template for adding decks
@app.route('/addDeck', methods=['GET', 'POST'])
def add_deck():
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
	decks = fetch_decks(claims['sub'])
	tmp_time = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
	tomorrow = tmp_time + timedelta(days=1)#Make the end of the revision day tomorrow at midnight
	if request.method =='POST': 
		deck = html.escape(request.form['add_deck'])
		new_deck = datastore.Entity(key=db.key('User', claims['sub'], 'Deck', deck))
		new_deck.update ({ #Create new deck entity with the following contents
		'deck_name':deck,
		'new_cards':10,
		'repetitions':150,
		'repetitions_today':0,
		'end_of_day':tomorrow
		})
		db.put(new_deck)
		return redirect(url_for('add'))

	return render_template('addDeck.html', user_data=claims)

#Returns HTML template for renaming decks
@app.route('/maxReps', methods=['GET', 'POST'])
def max_reps():
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
	if request.method =='POST':
		current_deck_name=html.escape(request.form['reps_deck'])
		new_reps = html.escape(request.form['new_repetitions'])
		ancestor = db.key('User', claims['sub'], 'Deck', current_deck_name)
		deck = db.get(ancestor)
		deck['repetitions']=new_reps #replaces current repetitions with new repetitions value
		db.put(deck) #updates the entity with new value
	return redirect(url_for('home'))

#Returns HTML template for for deleting decks
@app.route('/delete', methods=['GET', 'POST'])
def delete_deck():
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
	if request.method =='POST': 
		current_deck_name=request.form['delete_deck']
		cards = fetch_cards(claims['sub'], current_deck_name)
		index_range = len(cards)
		ancestor = db.key('User', claims['sub'], 'Deck', current_deck_name)
		deck = db.get(ancestor)
		db.delete(deck.key) #delete deck that matches the above condition
		for i in range(index_range):
			db.delete(cards[i].key)#delete all cards associated with this deck
	
	return redirect(url_for('home'))

#Returns HTML template for for adding cards to a deck
@app.route('/add', methods=['GET', 'POST'])
def add(): 
    id_token = request.cookies.get("token")
    claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
    decks = fetch_decks(claims['sub'])
    if request.method == 'POST': #gets values from HTML input and stores them locally
        deck_name = html.escape(request.form['deck_name'])
        kanji = html.escape(request.form['kanji'])
        kana = html.escape(request.form['kana'])
        romaji = html.escape(request.form['romaji'])
        card_meaning = html.escape(request.form['card_meaning'])
        sentence_example = html.escape(request.form['sentence_example'])
        tags = html.escape(request.form['tags'])
        deck_key = db.key('User', claims['sub'], 'Deck', deck_name)
        new_card = datastore.Entity(key=db.key('Card', parent=deck_key))
        new_card.update ({ #creates new card entity with the below values
            'kanji':kanji, 
            'kana': kana,
            'romaji':romaji,
            'card_meaning':card_meaning,
            'sentence_example':sentence_example,
            'tags':tags,
            'interval':0.1,
			'last_revision':datetime.now(pytz.utc)
        })
        db.put(new_card)   
    return render_template('add.html', user_data=claims, decks=decks)
  
#Returns HTML template for for studying cards
@app.route('/study',methods=['GET', 'POST'])
def study():
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)	
	deck = request.args.get('deck_name')
	ancestor = db.key(claims['sub'], 'Deck', deck)
	cards = fetch_cards(claims['sub'], deck)
	
	ancestor = db.key('User', claims['sub'], 'Deck', deck)
	deck_name = db.get(ancestor)
	index_range = len(cards)#returns the amount of cards in a deck
	card = None
	for potential_card in cards: #checks to see if each card in the list 'cards' meet the below condition, if the a card does, it is stored as the chosen card and returned
		if (potential_card['last_revision'] + timedelta(minutes=potential_card['interval'])) < datetime.now(pytz.utc):
			card = potential_card
			break
	if card == None: 
		return redirect(url_for('home'))
		
	if datetime.now(pytz.utc) > deck_name['end_of_day']:  #checks to see if the current date is greater than the designated end of day for the deck, if it is, reset todays repetitions
		deck_name['repetitions_today'] = 0
		tmp_time = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
		tomorrow = tmp_time + timedelta(days=1)
		deck_name['end_of_day'] = tomorrow
		db.put(deck_name)

	if request.method =='POST':
		difficulty = html.escape(request.form['difficulty'])
		if is_end(cards, card, deck): return redirect(url_for('home')) 
		elif not is_end(cards, card, deck):	
			ancestor = db.key('User', claims['sub'], 'Deck', deck)
			deck_reps = db.get(ancestor)
			deck_reps['repetitions_today']+=1 #when a card is revised add 1 to todays repetitions
			
			card['interval'] = set_interval(card, difficulty)
			card['last_revision'] = datetime.now(pytz.utc)
			db.put(deck_reps)
			db.put(card)
			
	return render_template('study.html',user_data=claims, card=card)
   
 #Function for fetching decks from the data base associated with current user
def fetch_decks(userID): 
    deck_names=[]
    ancestor = db.key('User', userID)
    deck_query = db.query(kind='Deck', ancestor=ancestor)
    return list(deck_query.fetch()) #fetch decks from database

#Function for fetching cards from the database that are associated with a selected deck and current user
def fetch_cards(userID, deck_name): 
	ancestor = db.key('User', userID, 'Deck', deck_name)
	cards = db.query(kind='Card', ancestor=ancestor)
	cards.order=['interval'] #get cards by ascending order of interval
	result = cards.fetch() #fetch cards from database
	result = list(result) 
	return result

#SM-2 SRS Math function
def set_interval(card, difficulty): 
	interval = card['interval']
	if card: 
		if difficulty == "again": interval = 1 #if user pressed 'Again', make it so that the user will see this card again in 1 minute
		elif difficulty == "hard": interval = interval*1.2 #if user pressed 'hard', make it so that the user will see this card again in current interval *1.2 minutes
		elif difficulty == "good": interval = interval*1.6 #if user pressed 'good', make it so that the user will see this card again in current interval *1.6 minutes
		elif difficulty == "easy": interval = interval*1.9 #if user pressed 'easy', make it so that the user will see this card again in current interval *1.9 minutes
	return interval
	
def is_end(cards, card, deckname): #checks to see whether a study session meets a certain end condition
	id_token = request.cookies.get("token")
	claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)	
	ancestor = db.key('User', claims['sub'], 'Deck', deckname)
	deck = db.get(ancestor)
	index_range = len(cards)
	
	today_reps = float(deck['repetitions_today']) #gets todays repetitions value
	max_rep = float(deck['repetitions']) #gets current decks max repetitions
	
	day = timedelta(1)
	then = card['last_revision']
	
	now = datetime.now(pytz.utc)
	card_i_range = len(card)
	
	#if todays repetitions is the same as max repetitions, then end study session
	for i in range(card_i_range): 
		if today_reps < max_rep and (now-then) < day :
			return False
			
		elif today_reps >= max_rep and (now-then) >= day :
			return True 

#checks to see if user is authenticated before sending a request
@app.before_request
def is_authenticated_user():
    if request.endpoint == 'login' or request.path.startswith('/static/'):
        return
    if 'token' in request.cookies:
        id_token = request.cookies.get("token")
        claims = None
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except:
            pass
        if claims != None:
            return
    return redirect(url_for('login'))
   
if __name__ == '__main__': 
    app.run(host='127.0.0.1', port=8080, debug=True)
    