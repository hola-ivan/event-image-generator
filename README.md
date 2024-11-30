# Event Image Generator

A Streamlit application that generates event images with location-based backgrounds from Pexels.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get a Pexels API key:
   - Go to [Pexels](https://www.pexels.com/api/)
   - Sign up for an account
   - Create a new API key

3. Configure your API key:
   - Open the `.env` file
   - Replace `your_pexels_api_key_here` with your actual Pexels API key

## Running the Application

Run the Streamlit app with:
```bash
streamlit run app.py
```

## Features

- Generate square event images with custom:
  - Time
  - Date
  - Event Name
  - Place
  - Address
- Automatically fetches relevant background images from Pexels based on the location
- Applies a professional blue tint overlay
- Download generated images as PNG files

## Note

Make sure you have a valid Pexels API key and stable internet connection for the background image fetching to work properly.
