import sqlite3
from transformers import pipeline
from tqdm import tqdm

# Define categories for classification
categories = [
    "Film & Animation", "Autos & Vehicles", "Music", "Pets & Animals", "Sports", "Short Movies",
    "Travel & Events", "Gaming", "Videoblogging", "People & Blogs", "Comedy", "Entertainment",
    "News & Politics", "Howto & Style", "Education", "Science & Technology", "Movies", "Anime/Animation",
    "Action/Adventure", "Classics", "Comedy", "Documentary", "Drama", "Family", "Foreign", "Horror",
    "Sci-Fi/Fantasy", "Thriller", "Shorts", "Shows", "Trailers", "History & Geography", "Economics & Finance"
]

# Initialize the zero-shot classifier with BART
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Connect to the SQLite database
db_path = "sql_app_categories.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add new columns for categories if they don't exist
try:
    cursor.execute("ALTER TABLE subscriptions ADD COLUMN category_1 TEXT")
    cursor.execute("ALTER TABLE subscriptions ADD COLUMN category_2 TEXT")
    conn.commit()
except sqlite3.OperationalError:
    print("Columns category_1 and category_2 already exist. Proceeding with classification...")

# Fetch all channels with their descriptions
cursor.execute("SELECT id, description FROM subscriptions LIMIT 10")
rows = cursor.fetchall()
print(f"rows: {rows}")

# Process each channel
for channel_id, description in tqdm(rows, desc="Classifying Channels"):
    if not description:
        # Skip if description is empty
        continue

    # Run zero-shot classification
    result = classifier(description, categories, multi_label=False)
    
    # Get top 2 categories
    top_categories = result['labels'][:2]

    # Update the database with the predicted categories
    category_1 = top_categories[0] if len(top_categories) > 0 else None
    category_2 = top_categories[1] if len(top_categories) > 1 else None

    cursor.execute("""
        UPDATE subscriptions
        SET category_1 = ?, category_2 = ?
        WHERE id = ?
    """, (category_1, category_2, channel_id))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("✅ Channel classification completed and database updated!")
