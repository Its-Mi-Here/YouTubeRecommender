# YouTube Recommender

A custom YouTube Recommender and Visualizer for better insight into one's interests.

## Features
1. **Summarization** - of User's interests based on their Youtube subscriptions
![Summary](./assets/Summary_img.png)

2. **Visualization** - of interest profile of users 
<!-- ![Interests visualization](./assets/pie_chart.png) -->
<div style="display: flex; justify-content: space-around;">
  <img src="./assets/pie_chart.png" alt="Image 1" style="width: 42%; margin-right: 10px;" />
  <img src="./assets/bar_chart.png" alt="Image 2" style="width: 42%; margin-left: 10px;" />
</div>


3. **Recommendations** - based on user Group & interests
<!-- ![Recommendations](./assets/Recom.png) -->
<img src="./assets/Recom.png" alt="Recommendations" style="width: 50%; height: auto; margin-left: 40px" />


## Tech stack
1. Backend - FastAPI, YouTube Data API
2. Machine Learning - OpenAI GPT, NLTK, PyTorch 
3. Frontend - React, HTML, CSS


## API Endpoints
1. OAuth Endpoint
2. Get data from Youtube API v3 (If oauth call or go to 1)
3. Summarize (GPT API call)
4. Categorize interests & display interests charts (NLP & GPT API call)
5. Get recommendations based on Group
    a. For all members in group - get channels
    b. For all channels, get videos & store
    c. Run ML recommender & show the recommendations
