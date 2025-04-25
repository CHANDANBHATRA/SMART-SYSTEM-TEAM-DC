import pandas as pd
from flask import Flask, render_template, request, redirect
import folium
import os
import openpyxl
from sklearn.linear_model import LogisticRegression

app = Flask(__name__)

EXCEL_FILE = 'shopkeepers.xlsx'

# Load shopkeeper data from Excel
def load_data():
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df['Achieved_Target'] = df['Achieved_Target'].fillna(0)
        return df
    else:
        return pd.DataFrame(columns=[
            'Shopkeeper_Name', 'Area', 'Mobile_Number', 'Revenue',
            'Target', 'Pincode', 'Latitude', 'Longitude', 'Achieved_Target'
        ])

# Initialize data and ML model
df = load_data()
if not df.empty:
    X = df[['Revenue', 'Target']]
    y = df['Achieved_Target']
    model = LogisticRegression()
    model.fit(X, y)
else:
    model = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    global df, model
    df = load_data()  # Reload latest data
    if not df.empty:
        X = df[['Revenue', 'Target']]
        y = df['Achieved_Target']
        model = LogisticRegression()
        model.fit(X, y)

    query = request.form['query'].strip().lower()
    results = df[(df['Area'].str.lower().str.contains(query)) | (df['Pincode'].astype(str).str.contains(query))]

    if not results.empty:
        results['Prediction'] = model.predict(results[['Revenue', 'Target']])
        results['Prediction_Label'] = results['Prediction'].apply(lambda x: '✅ Good Performance' if x == 1 else '❌ Unlikely')

    map_center = [results.iloc[0]['Latitude'], results.iloc[0]['Longitude']] if not results.empty else [26.9124, 75.7873]
    shop_map = folium.Map(location=map_center, zoom_start=13)

    for _, row in results.iterrows():
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=f"<b>{row['Shopkeeper_Name']}</b><br>Mobile: {row['Mobile_Number']}<br>Target: {row['Target']}<br>Revenue: ₹{row['Revenue']}<br>Prediction: {row['Prediction_Label']}"
        ).add_to(shop_map)

    map_html = shop_map._repr_html_()
    return render_template('results.html', results=results.to_dict(orient='records'), map_html=map_html)

@app.route('/add', methods=['GET', 'POST'])
def add_shopkeeper():
    if request.method == 'POST':
        new_data = {
            'Shopkeeper_Name': request.form['name'],
            'Area': request.form['area'],
            'Mobile_Number': request.form['mobile'],
            'Revenue': float(request.form['revenue']),
            'Target': float(request.form['target']),
            'Pincode': request.form['pincode'],
            'Latitude': float(request.form['latitude']),
            'Longitude': float(request.form['longitude']),
            'Achieved_Target': int(request.form['achieved'])
        }

        if os.path.exists(EXCEL_FILE):
            book = openpyxl.load_workbook(EXCEL_FILE)
            sheet = book.active
        else:
            book = openpyxl.Workbook()
            sheet = book.active
            sheet.append(list(new_data.keys()))  # Add headers

        sheet.append(list(new_data.values()))
        book.save(EXCEL_FILE)

        return redirect('/')

    return render_template('add_shopkeeper.html')

if __name__ == '__main__':
    app.run(debug=True)

