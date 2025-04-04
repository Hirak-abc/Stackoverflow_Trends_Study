from flask import Flask, render_template, request, Response
import pandas as pd
import matplotlib.pyplot as plt
import os
import io

app = Flask(__name__)

# Define the file path
file_path = r"E:\DHP\Sub_Fold\Final_Pro.xlsx"

# Function to load and process data
def load_data():
    if not os.path.isfile(file_path):
        return None

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None

    # Ensure required columns exist
    required_columns = ["Date", "Tags"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: Missing columns. Available columns: {df.columns.tolist()}")
        return None

    # Convert 'Date' column to datetime and extract year
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Year"] = df["Date"].dt.year

    # Filter for years 2022 to 2024
    df = df[(df["Year"] >= 2022) & (df["Year"] <= 2024)]

    # Explode the tags column
    df["Tag_List"] = df["Tags"].str.split(",")  # Assuming tags are comma-separated
    df = df.explode("Tag_List")
    df["Tag_List"] = df["Tag_List"].str.strip().str.lower()

    return df

# Load unique tags once
df = load_data()
unique_tags = sorted(df["Tag_List"].dropna().unique()) if df is not None else []

@app.route("/", methods=["GET", "POST"])
def index():
    selected_tags = []
    show_graph = False

    if request.method == "POST":
        selected_tags = request.form.getlist("tags")  # Get selected checkboxes
        show_graph = True if selected_tags else False

    return render_template("index.html", tags=unique_tags, selected_tags=selected_tags, show_graph=show_graph)

@app.route("/plot.png")
def plot():
    df = load_data()
    if df is None:
        return "Error loading data.", 500

    selected_tags = request.args.getlist("tags")

    # Compute total number of questions per year
    questions_per_year = df.groupby("Year").size()

    plt.figure(figsize=(10, 5))

    # Plot data for each selected tag
    for tag in selected_tags:
        tag_counts = df[df["Tag_List"] == tag].groupby("Year").size()
        tag_ratio = (tag_counts / questions_per_year).fillna(0)
        plt.plot(tag_ratio.index, tag_ratio.values, marker="o", linestyle="-", label=f"Ratio of {tag}")

    plt.xlabel("Year")
    plt.ylabel("Tag Ratio")
    plt.title("Stack Overflow Tags Trend (2022-2024)")
    plt.xticks([2022, 2023, 2024])  # Ensure only yearly intervals are shown
    plt.legend()
    plt.grid(True)

    # Save the plot to a bytes buffer
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
