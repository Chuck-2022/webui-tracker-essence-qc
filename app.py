from flask import Flask, request, render_template, redirect, url_for, flash
from database import *
from common import *
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
app = Flask(__name__)
app.secret_key = '&^DTNmD2jHJ^e3^h5zgFgpJ@uvAx!U7pC%*hZjEQ$^&Ag9yY`k'

# Initialize database
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    banner_search = request.args.get('banner', '')
    address_search = request.args.get('address', '')
    postal_search = request.args.get('code_postal', '')
    websites = get_all_station()

    sort_by = request.args.get('sort_by', '')
    sort_dir = request.args.get('sort_dir', 'asc')

    selected_stations = [w for w in websites if w[7]]
    filtered_stations = [w for w in websites if not w[7]]

    if banner_search or address_search or postal_search:
        banner_term = banner_search.lower()
        address_term = address_search.lower()
        postal_term = postal_search.lower()

        filtered_stations = [
            w for w in filtered_stations
            if (not banner_search or banner_term in (w[1] or '').lower())
            and (not address_search or address_term in (w[2] or '').lower())
            and (not postal_search or postal_term in (w[5] or '').lower())
        ]

    sort_mapping = {
        'banner': 1,
        'address': 2,
        'prix_regulier': 3,
        'prix_super': 4,
        'code_postal': 5,
    }
    if sort_by in sort_mapping:
        idx = sort_mapping[sort_by]
        reverse = sort_dir == 'desc'
        selected_stations.sort(key=lambda w: (w[idx] or '').lower(), reverse=reverse)
        filtered_stations.sort(key=lambda w: (w[idx] or '').lower(), reverse=reverse)

    if request.method == 'POST':
        address = request.form.get('address')

        if address:
            data = {
                'banner': '',
                'address': address,
                'prix_regulier': '',
                'prix_super': '',
                'code_postal': '',
                'gmap': ''
            }
            add_website(data)
            flash('Station added successfully!', 'success')
        else:
            flash('Address is required!', 'error')

        return redirect(url_for('index'))

    return render_template(
        'index.html',
        selected_stations=selected_stations,
        filtered_stations=filtered_stations,
        banner_search=banner_search,
        address_search=address_search,
        postal_search=postal_search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        has_filters=bool(banner_search or address_search or postal_search)
    )

def update_all_data(from_site=False):
    try:
        print('\nUpdating data...', end=' ')
        fetch_data()
        df = pd.read_excel('./data/data.xlsx')
        # Assume columns are 'banner', 'address', 'prix_regulier', 'prix_super', 'code_postal', 'gmap'
        for index, row in df.iterrows():
            data = {
                'banner': row['Bannière'],
                'address': row['Adresse'],
                'prix_regulier': row['Prix Régulier'],
                'prix_super': row['Prix Super'],
                'code_postal': row['Code Postal'],
                'gmap': create_gmap_link(str(row['Adresse'])),
                'selected': False
            }
            existing = get_station_by_address(data['address'])
            if existing:
                update_website_data(data, existing[0])
            else:
                add_website(data)
        print('Data updated successfully!')
        if from_site:
            flash('Data updated successfully!', 'success')
    except Exception as e:
        print('Error update_all_data', e)
        if from_site:
            flash(f'Error updating data: {str(e)}', 'error')
@app.route('/update', methods=['POST'])
def update():
    update_all_data(True)
    return redirect(url_for('index'))

@app.route('/delete/<int:website_id>')
def delete(website_id):
    delete_website(website_id)
    flash('Website deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/toggle/<int:website_id>')
def toggle(website_id):
    toggle_selected(website_id)
    return redirect(url_for('index'))  # Redirects without search parameter


if __name__ == '__main__':
    # Setup scheduler
    scheduler = BackgroundScheduler()
    update_all_data()
    scheduler.add_job(update_all_data, 'interval', minutes=5)
    scheduler.start()

    # app.run(debug=True, host="127.0.0.1")
    try:
        app.run(host="0.0.0.0")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()