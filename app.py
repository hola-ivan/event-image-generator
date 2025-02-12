import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont, ImageColor
from io import BytesIO
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Pexels API configuration
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
if not PEXELS_API_KEY or PEXELS_API_KEY == 'your_pexels_api_key_here':
    st.error("Please set a valid PEXELS_API_KEY in the .env file")
    st.write("You need to replace 'your_pexels_api_key_here' with your actual Pexels API key")
    st.stop()

# Constants for image generation
IMAGE_SIZE = (1080, 1080)
FOOTER_HEIGHT = 150
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
LOGO_HEIGHT = 120
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "Montserrat-VariableFont_wght.ttf")

# Download fonts if they don't exist
def download_font(url, save_path):
    if not os.path.exists(save_path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)

def enhance_search_query(event_name):
    """Enhance the search query with relevant keywords"""
    keywords = ["Networking", "event", "professional", "business", "venue"]
    # Extract meaningful words from event name (exclude common words)
    common_words = {"networking", "event", "professional", "the", "a", "an", "in", "at", "on", "with"}
    event_words = set(word.lower() for word in event_name.split())
    meaningful_words = event_words - common_words
    
    if meaningful_words:
        # Use the meaningful words from the event name
        return " ".join(meaningful_words)
    else:
        # Fallback to using the full event name
        return event_name

def fetch_background_image(query, page=1, per_page=15):
    """Fetch a background image from Pexels API"""
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    # Clean up the query
    query = query.strip()
    if not query:
        query = "event"
    
    # Make the API request with popularity sorting
    url = (
        f"https://api.pexels.com/v1/search"
        f"?query={query}"
        f"&per_page={per_page}"
        f"&page={page}"
        # f"&orientation=square"
        # f"&sort=popular"  # Sort by popularity
    )
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Check if we have any photos
        if data.get('photos'):
            photos = data['photos']
            if photos:
                # Get a specific photo from this page
                photo_index = min((page - 1) % per_page, len(photos) - 1)
                photo = photos[photo_index]
                image_url = photo['src']['original']
                
                # Download and open the image
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image = Image.open(BytesIO(image_response.content))
                return image
            
        # If we get here, no photos were found
        return None
    except Exception as e:
        print(f"Error fetching image: {str(e)}")  # Log the error but don't show to user
        return None

def apply_blue_tint(image):
    """Apply a blue tint to the image"""
    overlay = Image.new('RGBA', image.size, (0, 0, 102, 128))
    image = image.convert('RGBA')
    return Image.alpha_composite(image, overlay)

def add_footer(image):
    """Add white footer with logo and call to action"""
    # Create a white footer
    footer = Image.new('RGBA', (IMAGE_SIZE[0], FOOTER_HEIGHT), 'white')
    
    try:
        # Load and resize logo
        if not os.path.exists(LOGO_PATH):
            st.error(f"Logo not found at path: {LOGO_PATH}")
            return image
        
        logo = Image.open(LOGO_PATH)
        logo_aspect = logo.width / logo.height
        logo_width = int(LOGO_HEIGHT * logo_aspect)
        logo = logo.resize((logo_width, LOGO_HEIGHT), Image.Resampling.LANCZOS)
        
        # Calculate positions
        logo_pos = (30, (FOOTER_HEIGHT - LOGO_HEIGHT) // 2)
        
        # Paste logo
        footer.paste(logo, logo_pos, logo if logo.mode == 'RGBA' else None)
        
        # Add call to action text
        draw = ImageDraw.Draw(footer)
        try:
            # Use Montserrat font with regular weight
            font = ImageFont.truetype(FONT_PATH, 28)
            font.set_variation_by_name('Regular')  # Set to regular weight
        except:
            font = ImageFont.load_default()
            
        cta_text = "Reserva tu lugar:"
        link_text = "de.exatec.info/eventos"
        
        # Right-align text with padding
        right_padding = 30
        cta_width = draw.textlength(cta_text, font=font)
        link_width = draw.textlength(link_text, font=font)
        
        # Adjust vertical position to align better with logo
        vertical_offset = 10  # Move text up by 10 pixels
        cta_pos = (IMAGE_SIZE[0] - cta_width - right_padding, FOOTER_HEIGHT//2 - 20 - vertical_offset)
        link_pos = (IMAGE_SIZE[0] - link_width - right_padding, FOOTER_HEIGHT//2 + 6 - vertical_offset)
        
        draw.text(cta_pos, cta_text, fill='black', font=font)
        draw.text(link_pos, link_text, fill=(0, 51, 153), font=font)
        
        # Create final image with footer
        final_image = Image.new('RGBA', (IMAGE_SIZE[0], IMAGE_SIZE[1]), (255, 255, 255, 0))
        final_image.paste(image, (0, 0))
        final_image.paste(footer, (0, IMAGE_SIZE[1] - FOOTER_HEIGHT), footer)
        
        return final_image
    except Exception as e:
        st.error(f"Error adding footer: {str(e)}")
        return image

def create_minimalistic_background(size, style="gradient"):
    """Create a minimalistic background with different style options"""
    image = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(image)
    
    if style == "gradient":
        # EXATEC blue gradient
        top_color = (0, 45, 98)     # Dark blue
        bottom_color = (0, 84, 166)  # Light blue
        
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    
    elif style == "geometric":
        # Solid background with geometric patterns
        background_color = (0, 45, 98)  # Dark blue
        accent_color = (0, 84, 166)     # Light blue

        # Check if any line in event_name exceeds 12 characters.
        if any(len(line) > 12 for line in event_name.splitlines()):
            # Extend the blue background to the full canvas width.
            background_rect = (0, 0, canvas_width, background_height)
        else:
            # Use default margins.
            background_rect = (margin, 0, canvas_width - margin, background_height)

        draw.rectangle(background_rect, fill=background_color)
    
    elif style == "minimal":
        # Solid color with subtle corner accent
        main_color = (0, 45, 98)    # Dark blue
        accent_color = (0, 84, 166)  # Light blue
        
        image = Image.new('RGB', size, main_color)
        draw = ImageDraw.Draw(image)
        
        # Draw corner accent
        corner_size = size[0] // 4
        draw.rectangle([(0, 0), (corner_size, corner_size)], fill=accent_color)
    
    return image

def create_event_image(time, date, event_name, place, address, query=None, page=1):
    """Create the event image with all details"""
    # Create or fetch background
    if query and query.strip():
        # If query is provided, try to fetch image from Pexels
        background = fetch_background_image(query, page)
        if background:
            # Resize and crop to square
            background = background.resize(IMAGE_SIZE)
            # Apply blue tint
            background = apply_blue_tint(background)
        else:
            # Fallback to white background if fetch fails
            background = Image.new('RGB', IMAGE_SIZE, 'white')
    else:
        # Use white background if no query provided
        background = Image.new('RGB', IMAGE_SIZE, 'white')

    # Create a new layer for the blue rectangle
    blue_overlay = Image.new('RGBA', IMAGE_SIZE, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(blue_overlay)
    
    # Define the blue rectangle dimensions (centered, 80% of width)
    rect_width = int(IMAGE_SIZE[0] * 0.8)
    rect_height = int(IMAGE_SIZE[1] * 0.6)
    rect_left = (IMAGE_SIZE[0] - rect_width) // 2
    rect_top = int(IMAGE_SIZE[1] * 0.15)  # Start at 15% from top instead of center
    
    # Draw the semi-transparent blue rectangle
    draw_overlay.rectangle(
        [(rect_left, rect_top), (rect_left + rect_width, rect_top + rect_height)],
        fill=(0, 82, 204, 255)  # Solid blue color with full opacity
    )
    
    # Composite the blue overlay onto the background
    background = Image.alpha_composite(background.convert('RGBA'), blue_overlay)
    
    # Add text
    draw = ImageDraw.Draw(background)
    
    # Load fonts with regular weight (400)
    try:
        font_large = ImageFont.truetype(FONT_PATH, 96)
        font_large.set_variation_by_name('Bold')  # Set event name to bold weight
        
        font_medium = ImageFont.truetype(FONT_PATH, 36)  # Reduced from 48
        font_medium.set_variation_by_name('Regular')
        
        font_small = ImageFont.truetype(FONT_PATH, 28)  # Reduced from 36
        font_small.set_variation_by_name('Regular')
    except Exception as e:
        st.error(f"Error loading fonts: {str(e)}")
        return None
    
    # Calculate text positions relative to the blue rectangle
    center_x = IMAGE_SIZE[0] // 2
    
    # Position text elements with adjusted spacing
    datetime_y = rect_top + 40  # Fixed position from top of blue rectangle
    event_name_y = rect_top + (rect_height // 2)  # Center in blue rectangle
    place_y = rect_top + rect_height - 80  # Fixed position from bottom
    address_y = place_y + 40  # Fixed spacing below place
    
    # Draw text elements
    # Time and date at top with vertical separator
    separator = " | "
    datetime_text = f"{time}{separator}{date}"
    draw.text((center_x, datetime_y), datetime_text, fill="white", anchor="mm", font=font_small)
    
    # Event name in the middle (can be multiple lines)
    event_name_lines = [line.strip().upper() for line in event_name.split('\n')]  # Convert to uppercase
    total_height = len(event_name_lines) * font_large.size
    current_y = event_name_y - (total_height / 2)
    
    for line in event_name_lines:
        draw.text((center_x, current_y), line, fill="white", anchor="mm", font=font_large)
        current_y += font_large.size
    
    # Place and address at bottom
    draw.text((center_x, place_y), place, fill="white", anchor="mm", font=font_medium)
    draw.text((center_x, address_y), address, fill="white", anchor="mm", font=font_small)
    
    # Add footer
    final_image = add_footer(background)
    
    return final_image

def main():
    st.set_page_config(
        page_title="Generador de Imagenes para Eventos",
        page_icon="🎇",
        layout="centered"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .main-header {
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        .generated-image {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .image-container {
            margin-bottom: 30px;
        }
        .version-header {
            color: #666;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<div class='main-header'><h1>Posters para Eventos</h1></div>", unsafe_allow_html=True)
    st.markdown("Genera material para promoción de nuestros eventos! **Solo para uso autorizado de miembros de la comunidad EXATEC.**")
    st.write("Contacto: [asociacion.alemania@exatec.tec.mx](mailto:asociacion.alemania@exatec.tec.mx)")

    # Create two columns for form and preview
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📝 Event Details")
        with st.form("event_details"):
            # Time input using time_input
            default_time = datetime.strptime("19:00", "%H:%M").time()
            time = st.time_input(
                "Time",
                value=default_time,
                help="Select the event time"
            )

            # Format time to 24-hour format
            formatted_time = time.strftime("%H:%M")

            # Date input using date picker
            default_date = datetime.now() + timedelta(days=7)  # Default to a week from now
            date = st.date_input(
                "Date",
                value=default_date,
                min_value=datetime.now(),
                help="Select the event date"
            )
            # Format date to be more readable
            formatted_date = date.strftime("%d.%m.%Y")

            # Event name with text area for better visibility
            event_name = st.text_area(
                "Event Name",
                value="Reunión\nEXATEC\nBonn",
                help="Enter the name of your event. Use multiple lines for longer names.",
                height=100
            )

            # Location details with autocomplete suggestions
            place = st.text_input(
                "Venue Name",
                value="Gasthaus El Borrego",
                help="Enter the name of the venue"
            )

            address = st.text_input(
                "Address",
                value="Garza Sada Allee 2501, Bonn",
                help="Enter the full address of the venue"
            )

            # Additional options in an expander
            with st.expander("🎨 Background Image", expanded=False):
                background_keywords = st.text_input(
                    "Background Image Keywords (optional)",
                    value="",
                    help="Add specific keywords to customize the background image. Leave empty for white background."
                )

            # Center the generate button and make it more prominent
            col1_1, col1_2, col1_3 = st.columns([1, 2, 1])
            with col1_2:
                generate_button = st.form_submit_button(
                    "✨ Generate Images",
                    use_container_width=True,
                    type="primary"
                )

    # Preview column
    with col2:
        st.markdown("### 👁️ Preview")
        
        if generate_button:
            with st.spinner("🎨 Creating your event images..."):
                # Generate five different versions
                images = []
                
                if background_keywords.strip():
                    # When background keywords are provided, use them as the main search term
                    # and fetch different pages to ensure variety
                    search_query = background_keywords
                    
                    # Try to generate 5 unique images using different pages
                    for page_num in range(1, 8):  # Try up to page 8 to get 5 images
                        if len(images) >= 5:
                            break
                            
                        image = create_event_image(
                            formatted_time,
                            formatted_date,
                            event_name,
                            place,
                            address,
                            query=search_query,
                            page=page_num
                        )
                        
                        if image:
                            images.append((image, f"Version {len(images) + 1}"))
                else:
                    # Use white background
                    image = create_event_image(
                        formatted_time,
                        formatted_date,
                        event_name,
                        place,
                        address,
                        query=None
                    )
                    
                    if image:
                        images.append((image, "Preview"))
                
                if images:
                    # Display all generated images
                    for idx, (image, version) in enumerate(images, 1):
                        st.markdown(
                            f"<div class='version-header'>{version}</div>", 
                            unsafe_allow_html=True
                        )
                        st.markdown("<div class='generated-image'>", unsafe_allow_html=True)
                        st.image(image)  # Changed from use_column_width
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Add download button for each version
                        buf = BytesIO()
                        image.save(buf, format="PNG")
                        st.download_button(
                            label=f"📥 Download {version}",
                            data=buf.getvalue(),
                            file_name=f"event_{date.strftime('%Y%m%d')}_v{idx}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                        st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.error("❌ Could not generate any images. Please try again.")
        else:
            # Show placeholder when no image is generated
            st.markdown(
                """
                <div style="
                    border: 2px dashed #cccccc;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    color: #666666;
                    margin: 20px 0;
                ">
                    <h3>Your event images will appear here</h3>
                    <p>Fill in the details and click "Generate Images"</p>
                </div>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()
