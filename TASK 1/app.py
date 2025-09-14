from flask import Flask, render_template, request
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

CSV_PATH = "books_toscrape.csv"

# Load CSV safely
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"{CSV_PATH} not found. Run Book.py first to scrape data.")

df = pd.read_csv(CSV_PATH)

@app.route("/")
def index():
    query = request.args.get("q", "").lower()
    results = df.copy()

    if query:
        results = results[
            results["title"].str.lower().str.contains(query, na=False) |
            results["description"].str.lower().str.contains(query, na=False)
        ]

    return render_template("index.html", books=results.to_dict(orient="records"), query=query)


@app.route("/charts")
def charts():
    plt.figure(figsize=(8, 6))
    df["price"] = df["price"].astype(float)

    # Simple histogram of prices
    df["price"].hist(bins=20, color="skyblue", edgecolor="black")
    plt.xlabel("Price")
    plt.ylabel("Number of Books")
    plt.title("Book Price Distribution")

    # Convert plot to base64 for HTML embedding
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template("charts.html", plot_url=plot_url)


if __name__ == "__main__":
    app.run(debug=True)
