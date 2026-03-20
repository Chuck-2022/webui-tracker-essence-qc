from flask import Flask, request, render_template, redirect, url_for, flash
import random
from database import *
import time
from common import *
from apscheduler.schedulers.background import BackgroundScheduler 
app = Flask(__name__)
app.secret_key = '&^DTNmD2jHJ^e3^h5zgFgpJ@uvAx!U7pC%*hZjEQ$^&Ag9yY`k'

# Initialize database
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        
        if url:
            try:
                # Validate URL format
                try:
                    url.replace(' ', '')
                except:
                    pass
                if not url.startswith('https://'):
                    url = 'https://' + url
                if 'https://www.gasbuddy' not in url:
                    flash('Support only gasbuddy')
                    return redirect(url_for('index'))
                name_data, price_data, updated_data, gmap_link = fetch_data(url)
                
                # Add to database with scraped data
                add_website(url, name_data, price_data, updated_data, gmap_link)
                flash('Website added successfully with scraped data!', 'success')
            except Exception as e:
                print('Error index',e)
                flash(f'Error adding website: {str(e)}', 'error')
        else:
            flash('URL and Name are required!', 'error')
        
        return redirect(url_for('index'))
    
    elif request.method == 'GET':
        # Get all websites from database
        websites = get_all_websites()
        return render_template('index.html', websites=websites)

def update_all_data(from_site=False):
    websites = get_all_websites()
    try:
        for w in websites:
            update_data(w[0], from_site)
            time.sleep(random.uniform(1,1.5))
    except Exception as e:
        print('Error update_all_data', e)
        None
@app.route('/update_all', methods=['POST'])
def update_all():
    update_all_data(True)
    return redirect(url_for('index'))

@app.route('/delete/<int:website_id>')
def delete(website_id):
    delete_website(website_id)
    flash('Website deleted successfully!', 'success')
    return redirect(url_for('index'))


def update_data(website_id, from_site=False):
    try:
        # Get website URL from database
        # Direct database access without connection pooling issues
        conn = sqlite3.connect('websites.db')
        c = conn.cursor()
        c.execute('SELECT url FROM websites WHERE id = ?', (website_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            url = result[0]
            name_data, price_data, updated_data, gmap_link = fetch_data(url)
            # Update database
            update_website_data(website_id, name_data, price_data, updated_data, gmap_link)
        else:
            print(e)
            if from_site:
                flash('Website not found!', url)
    except Exception as e:
        print(e)
        if from_site:
            flash(f'Error updating data: {str(e)}', 'error')
    return
    
@app.route('/update_data/<int:website_id>')
def update_data_website(website_id):
    update_data(website_id, True)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Setup scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_all_data, 'interval', minutes=5)
    scheduler.start()
    
    try:
        app.run(host="0.0.0.0")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()