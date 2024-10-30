from flask import Flask, jsonify
import json

app = Flask(__name__)

def load_data():
    with open('scraped_products.json', 'r') as file:
        return json.load(file)

@app.route('/products', methods=['GET'])
def get_all_products():
    data = load_data()
    products = [item for item in data if "Last Crawl Date" not in item]
    return jsonify(products)

@app.route('/products/<product_type>', methods=['GET'])
def get_products_by_type(product_type):
    data = load_data()
    filtered_products = [
        item for item in data
        if item.get("Product Type", "").lower() == product_type.lower()
    ]
    if filtered_products:
        return jsonify(filtered_products)
    else:
        return jsonify({"message": "No products found for this category."}), 404


@app.route('/last_crawl', methods=['GET'])
def get_last_crawl_date():
    data = load_data()
    last_crawl_date = data[0].get("Last Crawl Date", "No last crawl date available")
    return jsonify({"Last Crawl Date": last_crawl_date})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
