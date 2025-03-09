import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter, ImageOps
from io import BytesIO
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import qrcode
from math import ceil
from base64 import b64encode
import json

# Initialize session state to store webhook debug info
if 'webhook_debug' not in st.session_state:
    st.session_state.webhook_debug = {}

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
FOOTER_HEIGHT = 160  # Slightly taller footer for better spacing
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
LOGO_HEIGHT = 120
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "Montserrat-VariableFont_wght.ttf")
EXATEC_BLUE = (0, 61, 165)  # Main EXATEC blue
EXATEC_LIGHT_BLUE = (41, 128, 185)  # Lighter blue for better contrast
ACCENT_COLOR = (255, 200, 0)  # Golden accent color
ICON_SIZE = 24  # Size of icons

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
    """Add white footer with logo, call to action, and QR code - improved design"""
    # Create a white footer with no gradient - just plain white as per feedback
    footer = Image.new('RGBA', (IMAGE_SIZE[0], FOOTER_HEIGHT), (255, 255, 255, 255))
    
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
        logo_pos = (40, (FOOTER_HEIGHT - LOGO_HEIGHT) // 2)  # More left padding
        
        # Paste logo
        footer.paste(logo, logo_pos, logo if logo.mode == 'RGBA' else None)
        
        # Add call to action text
        draw = ImageDraw.Draw(footer)
        
        try:
            # Use Montserrat font with different weights for hierarchy
            font_cta = ImageFont.truetype(FONT_PATH, 26)
            font_cta.set_variation_by_name('SemiBold')  # Semi-bold for CTA
            
            font_link = ImageFont.truetype(FONT_PATH, 32)
            font_link.set_variation_by_name('Bold')  # Bold for link
        except:
            font_cta = ImageFont.load_default()
            font_link = ImageFont.load_default()
            
        cta_text = "RESERVA TU LUGAR EN:"
        link_text = "de.exatec.info/eventos"
        
        # Right-align text with padding
        right_padding = 35
        qr_size = 110  # Slightly larger QR code
        qr_padding = 25  # Padding between text and QR code
        
        # Calculate text width and height using newer methods
        cta_width = draw.textlength(cta_text, font=font_cta)
        link_width = draw.textlength(link_text, font=font_link)
        
        # Get font heights using font metrics
        cta_height = font_cta.getbbox("Ay")[3]
        link_height = font_link.getbbox("Ay")[3]
        
        # Position the text to the left of the QR code
        text_x = IMAGE_SIZE[0] - qr_size - qr_padding - max(cta_width, link_width) - right_padding
        cta_y = (FOOTER_HEIGHT - cta_height - link_height - 8) // 2  # Center vertically
        link_y = cta_y + cta_height + 8  # Slightly below the CTA text
        
        # Draw call to action with EXATEC blue color
        draw.text((text_x, cta_y), cta_text, fill=EXATEC_BLUE, anchor="lt", font=font_cta)
        
        # Draw link with accent color for emphasis
        draw.text((text_x, link_y), link_text, fill=EXATEC_LIGHT_BLUE, anchor="lt", font=font_link)
        
        # Generate QR code with improved quality
        qr_url = "https://de.exatec.info/eventos"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,
            border=2,  # Smaller border for better look
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color=EXATEC_BLUE, back_color="white").convert('RGBA')
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Add subtle rounded border to QR code
        qr_with_border = Image.new('RGBA', (qr_size + 8, qr_size + 8), (255, 255, 255, 0))
        draw_border = ImageDraw.Draw(qr_with_border)
        draw_border.rounded_rectangle(
            [(0, 0), (qr_size + 7, qr_size + 7)], 
            radius=5,
            fill=(255, 255, 255, 255),
            outline=EXATEC_LIGHT_BLUE, 
            width=2
        )
        qr_with_border.paste(qr_img, (4, 4), qr_img)
        
        # Position QR code in the footer
        qr_pos = (IMAGE_SIZE[0] - qr_size - right_padding - 4, (FOOTER_HEIGHT - qr_size - 8) // 2)
        footer.paste(qr_with_border, (qr_pos[0]-4, qr_pos[1]-4), qr_with_border)
        
        # Add subtle separator line between logo and text
        separator_x = logo_pos[0] + logo_width + 40
        draw.line(
            [(separator_x, FOOTER_HEIGHT//4), (separator_x, 3*FOOTER_HEIGHT//4)],
            fill=(200, 200, 200, 150),
            width=1
        )
        
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
        # EXATEC blue gradient with improved colors
        top_color = (0, 45, 98)     # Dark blue
        bottom_color = (0, 84, 166)  # Light blue
        
        for y in range(size[1]):
            ratio = y / size[1]
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))
            
        # Add subtle pattern overlay
        for i in range(0, size[1], 20):
            opacity = int(40 * (1 - i/size[1]))  # Fade out toward bottom
            draw.line([(0, i), (size[0], i)], fill=(255, 255, 255, opacity), width=1)
    
    elif style == "geometric":
        # Improved geometric pattern
        background_color = (0, 45, 98)  # Dark blue
        accent_color = (0, 84, 166)     # Light blue
        
        # Fill background
        draw.rectangle((0, 0, size[0], size[1]), fill=background_color)
        
        # Add abstract geometric elements
        # Top right corner triangle
        draw.polygon([(size[0]-200, 0),
                      (size[0], 0),
                      (size[0], 200)], 
                      fill=accent_color)
        
        # Bottom left corner triangle
        draw.polygon([(0, size[1]),
                      (0, size[1]-200),
                      (200, size[1])],
                      fill=accent_color)
                      
        # Add subtle dot pattern
        for x in range(0, size[0], 40):
            for y in range(0, size[1], 40):
                if (x + y) % 80 == 0:
                    draw.ellipse([(x-2, y-2), (x+2, y+2)], fill=(255, 255, 255, 30))
    
    return image

def create_event_image(time, date, event_name, place, address, query=None, page=1):
    """Create the event image with all details and improved visual design"""
    # Create or fetch background
    if query and query.strip():
        # If query is provided, try to fetch image from Pexels
        background = fetch_background_image(query, page)
        if background:
            # Resize and crop to square
            background = background.resize(IMAGE_SIZE)
            # Apply blue tint with more transparency for better contrast
            overlay = Image.new('RGBA', IMAGE_SIZE, (0, 30, 90, 150))  # More transparent blue
            background = background.convert('RGBA')
            background = Image.alpha_composite(background, overlay)
            
            # Apply subtle blur for more professional look
            background = background.filter(ImageFilter.GaussianBlur(radius=2))
        else:
            # Fallback to white background if fetch fails
            background = Image.new('RGB', IMAGE_SIZE, 'white')
    else:
        # Always use white background when no query is provided
        background = Image.new('RGB', IMAGE_SIZE, 'white')

    # Create a new layer for the blue rectangle with improved styling
    blue_overlay = Image.new('RGBA', IMAGE_SIZE, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(blue_overlay)
    
    # Define the blue rectangle dimensions (centered, 85% of width for more impact)
    rect_width = int(IMAGE_SIZE[0] * 0.85)
    rect_height = int(IMAGE_SIZE[1] * 0.65)  # Slightly taller for better content spacing
    rect_left = (IMAGE_SIZE[0] - rect_width) // 2
    rect_top = int(IMAGE_SIZE[1] * 0.14)  # Start a bit higher

    # Draw the semi-transparent blue rectangle with darker blue color as requested
    darker_blue = (0, 83, 255, 255)  # RGB (0, 83, 255) with full opacity
    draw_overlay.rectangle(
        [(rect_left, rect_top), (rect_left + rect_width, rect_top + rect_height)],
        fill=darker_blue  # Darker blue with full opacity
    )
    
    # Add subtle border around the rectangle
    border_width = 3
    draw_overlay.rectangle(
        [(rect_left-border_width, rect_top-border_width), 
         (rect_left + rect_width+border_width, rect_top + rect_height+border_width)],
        outline=(255, 255, 255, 180),  # White semi-transparent border
        width=border_width
    )
    
    # Add accent line at the top using light blue (#54C0E8) instead of yellow
    accent_height = 6
    light_blue = (84, 192, 232)  # #54C0E8 in RGB
    draw_overlay.rectangle(
        [(rect_left, rect_top), (rect_left + rect_width, rect_top + accent_height)],
        fill=light_blue + (255,)  # Light blue accent with full opacity
    )
    
    # Composite the blue overlay onto the background
    background = Image.alpha_composite(background.convert('RGBA'), blue_overlay)
    
    # Add text
    draw = ImageDraw.Draw(background)
    
    # Load fonts
    try:
        # Load the font path once
        font_path = FONT_PATH
        
        # Prepare different font sizes with more variation for hierarchy
        font_datetime = ImageFont.truetype(font_path, 30)  # Slightly larger
        font_datetime.set_variation_by_name('SemiBold')  # Semi-bold weight
        
        font_place = ImageFont.truetype(font_path, 40)  # Larger for venue
        font_place.set_variation_by_name('SemiBold')  # Semi-bold weight
        
        font_address = ImageFont.truetype(font_path, 30)  # Slightly larger
        font_address.set_variation_by_name('Regular')  # Regular weight
    except Exception as e:
        st.error(f"Error loading fonts: {str(e)}")
        return None
    
    # Calculate text positions
    center_x = IMAGE_SIZE[0] // 2
    
    # Position text elements with improved spacing
    datetime_y = rect_top + 50  # More space from top of blue rectangle
    place_y = rect_top + rect_height - 95  # More space from bottom
    address_y = place_y + 45  # More spacing below place
    
    # Draw time and date at top with icons
    clock_icon = get_icon("clock")
    calendar_icon = get_icon("calendar")
    # We no longer need the location icon as per feedback
    # location_icon = get_icon("location")
    
    # Format time and date nicely
    time_text = time
    date_text = date
    
    # Calculate icon positions
    icon_spacing = 10
    time_width = draw.textlength(time_text, font=font_datetime)
    date_width = draw.textlength(date_text, font=font_datetime)
    
    # Position for time with icon
    if clock_icon:
        time_icon_x = center_x - (time_width + ICON_SIZE + icon_spacing + 20 + date_width + ICON_SIZE + icon_spacing) // 2
        time_text_x = time_icon_x + ICON_SIZE + icon_spacing
        # Convert to integers with int()
        clock_pos = (int(time_icon_x), int(datetime_y - ICON_SIZE//2))
        background.paste(clock_icon, clock_pos, clock_icon)
    else:
        time_text_x = center_x - (time_width + 20 + date_width) // 2
    
    # Position for date with icon
    if calendar_icon:
        date_icon_x = time_text_x + time_width + 20
        date_text_x = date_icon_x + ICON_SIZE + icon_spacing
        # Convert to integers with int()
        calendar_pos = (int(date_icon_x), int(datetime_y - ICON_SIZE//2))
        background.paste(calendar_icon, calendar_pos, calendar_icon)
    else:
        date_text_x = time_text_x + time_width + 20
    
    # Draw time and date texts
    draw.text((time_text_x, datetime_y), time_text, fill="white", anchor="lm", font=font_datetime)
    draw.text((date_text_x, datetime_y), date_text, fill="white", anchor="lm", font=font_datetime)
    
    # Calculate available space for event name
    available_height = place_y - datetime_y - 100  # More buffer space
    max_width = rect_width * 0.88  # Slightly wider max width
    
    # Get event name lines and convert to uppercase
    event_name_lines = [line.strip().upper() for line in event_name.split('\n') if line.strip()]
    
    # Adaptive font sizing for event name - increased initial size
    initial_font_size = 110  # Start with larger size for more impact
    min_font_size = 40     # Don't go smaller than this
    
    # Function to check if text fits within constraints
    def text_fits(lines, font_size):
        test_font = ImageFont.truetype(font_path, font_size)
        test_font.set_variation_by_name('Bold')
        
        # Calculate total height with line spacing
        line_spacing = font_size * 0.2  # 20% of font size for spacing
        total_height = len(lines) * (font_size + line_spacing)
        
        # Check height constraint
        if total_height > available_height:
            return False
            
        # Check width constraint for each line
        for line in lines:
            if draw.textlength(line, font=test_font) > max_width:
                return False
                
        return True
    
    # Find the largest font size that fits
    font_size = initial_font_size
    while font_size >= min_font_size:
        if text_fits(event_name_lines, font_size):
            break
        font_size -= 4  # Decrease by 4pt each time
    
    # If text still doesn't fit at minimum size, try wrapping words
    if font_size < min_font_size:
        font_size = min_font_size
        
        # Combine all text and rewrap
        all_text = " ".join(event_name_lines)
        event_name_lines = []
        words = all_text.split()
        current_line = []
        
        font_event = ImageFont.truetype(font_path, font_size)
        font_event.set_variation_by_name('Bold')
        
        for word in words:
            test_line = " ".join(current_line + [word]) if current_line else word
            if draw.textlength(test_line, font=font_event) <= max_width:
                current_line.append(word)
            else:
                if current_line:  # Add completed line
                    event_name_lines.append(" ".join(current_line))
                current_line = [word]  # Start new line with current word
                
        # Add the last line if it exists
        if current_line:
            event_name_lines.append(" ".join(current_line))
    
    # Create final font with determined size
    font_event = ImageFont.truetype(font_path, font_size)
    font_event.set_variation_by_name('Bold')
    
    # Calculate position to center the text block vertically
    line_spacing = font_size * 0.25  # Increased spacing between event name lines
    total_height = len(event_name_lines) * (font_size + line_spacing) - line_spacing  # Subtract last spacing
    event_name_y = datetime_y + 85 + (available_height - total_height) / 2
    
    # Draw each line of the event name with enhanced styling
    current_y = event_name_y
    for i, line in enumerate(event_name_lines):
        # Add subtle text shadow for better visibility
        shadow_offset = max(2, ceil(font_size / 30))  # Dynamic shadow based on font size
        draw.text((center_x+shadow_offset, current_y+shadow_offset), line, 
                  fill=(0, 0, 0, 100), anchor="mm", font=font_event)
        
        # Draw main text
        draw.text((center_x, current_y), line, fill="white", anchor="mm", font=font_event)
            
        current_y += font_size + line_spacing
    
    # Draw place name with subtle shadow - no location icon as per feedback
    shadow_offset = 2
    draw.text((center_x+shadow_offset, place_y+shadow_offset), place, 
              fill=(0, 0, 0, 100), anchor="mm", font=font_place)
    draw.text((center_x, place_y), place, fill="white", anchor="mm", font=font_place)
    
    # Draw address in regular weight
    draw.text((center_x, address_y), address, fill="white", anchor="mm", font=font_address)
    
    # Add footer
    final_image = add_footer(background)
    
    return final_image

# Function to load or download icons
def get_icon(icon_name):
    icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    icon_path = os.path.join(icons_dir, f"{icon_name}.png")
    
    if not os.path.exists(icon_path):
        # Dictionary of icon URLs - you can replace these with your preferred icons
        icon_urls = {
            "clock": "https://cdn-icons-png.flaticon.com/512/2088/2088617.png",
            "calendar": "https://cdn-icons-png.flaticon.com/512/2693/2693507.png",
            "location": "https://cdn-icons-png.flaticon.com/512/1180/1180755.png"
        }
        
        if icon_name in icon_urls:
            try:
                response = requests.get(icon_urls[icon_name])
                if response.status_code == 200:
                    with open(icon_path, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                print(f"Error downloading icon {icon_name}: {str(e)}")
                return None
    
    if os.path.exists(icon_path):
        try:
            icon = Image.open(icon_path).convert("RGBA")
            icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
            return icon
        except Exception as e:
            print(f"Error loading icon {icon_name}: {str(e)}")
    
    return None

def send_webhook(image, event_details):
    """
    Simplified webhook function that sends event details and image URL to a webhook endpoint
    Returns: (success_boolean, message)
    """
    import hashlib
    import os
    
    # Webhook URL
    webhook_url = "https://hook.eu2.make.com/damd40lgectmsmlhqg9l3ravlesoslyz"
    
    try:
        # Create a buffer for the image
        buffered = BytesIO()
        
        # Ensure image is in RGB format (not RGBA)
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        
        # Save as PNG
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        
        # Create a hash of the image for the filename
        img_hash = hashlib.sha224(img_bytes).hexdigest()
        
        # Determine base URL based on environment
        base_url = "https://exatec-alemania-posters-para-eventos.streamlit.app"
        
        # Construct the image URL
        image_url = f"{base_url}/~/+/media/{img_hash}.png"
        
        st.write(f"Image URL: {image_url}")
        
        # Create payload with image URL instead of base64 data
        payload = {
            "image_url": image_url,
            "event_name": event_details["event_name"],
            "date": event_details["date"],
            "time": event_details["time"],
            "place": event_details["place"],
            "address": event_details["address"]
        }
        
        # Send the request
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Check response
        if response.status_code == 200:
            return True, "Event successfully published!"
        else:
            return False, f"Error: {response.status_code} - {response.text[:100]}"
            
    except Exception as e:
        import traceback
        st.error(f"Error: {str(e)}")
        st.write(traceback.format_exc())
        return False, f"Error preparing data: {str(e)}"

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
                
            # Option to publish to webhook automatically
            auto_publish = st.checkbox("Automatically publish to website", value=True,
                help="When checked, the event image will be automatically sent to the website")

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
                # Always generate a white background version first
                white_bg_image = create_event_image(
                    formatted_time,
                    formatted_date,
                    event_name,
                    place,
                    address,
                    query=None
                )
                
                # Prepare event details for webhook
                event_details = {
                    "event_name": event_name,
                    "date": formatted_date,
                    "time": formatted_time,
                    "place": place,
                    "address": address
                }
                
                # If auto-publish is enabled, send the white background image
                if auto_publish and white_bg_image:
                    with st.status("Publishing event to website...") as status:
                        success, message = send_webhook(white_bg_image, event_details)
                        if success:
                            status.update(label="✅ " + message, state="complete")
                        else:
                            status.update(label="❌ " + message, state="error")
                
                # Generate additional versions with backgrounds if keywords provided
                images = []
                if white_bg_image:
                    images.append((white_bg_image, "White Background"))
                
                if background_keywords.strip():
                    # When background keywords are provided, use them as the main search term
                    # and fetch different pages to ensure variety
                    search_query = background_keywords
                    
                    # Try to generate additional images using different pages
                    for page_num in range(1, 4):  # Generate up to 3 background variations
                        with st.spinner(f"Creating variation {page_num}..."):
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
                                images.append((image, f"Background Variation {page_num}"))
                
                if images:
                    # Display all generated images
                    for idx, (image, version) in enumerate(images):
                        st.markdown(
                            f"<div class='version-header'>{version}</div>", 
                            unsafe_allow_html=True
                        )
                        st.image(image)
                        
                        # Create columns for buttons
                        btn_col1, btn_col2 = st.columns(2)
                        
                        # Download button
                        with btn_col1:
                            buf = BytesIO()
                            image.save(buf, format="PNG")
                            st.download_button(
                                label=f"📥 Download",
                                data=buf.getvalue(),
                                file_name=f"event_{date.strftime('%Y%m%d')}_{idx+1}.png",
                                mime="image/png",
                                use_container_width=True
                            )
                        
                        # Manual publish button (only for versions that aren't auto-published)
                        with btn_col2:
                            if version != "White Background" or not auto_publish:
                                if st.button(
                                    "🚀 Publish This Version", 
                                    key=f"publish_btn_{idx}",
                                    use_container_width=True
                                ):
                                    success, message = send_webhook(image, event_details)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                            else:
                                # If this was auto-published, show a disabled button
                                st.markdown('<div style="text-align: center; color: green; padding: 10px;">✅ Published</div>', unsafe_allow_html=True)
                        
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
