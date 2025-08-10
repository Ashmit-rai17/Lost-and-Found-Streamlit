import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode
import pydeck as pdk
import cv2
import tempfile
import numpy as np

# ----------------------------
# CONFIG
# ----------------------------
DATA_FILE = "data/items.csv"
IMAGES_DIR = "images"
QR_DIR = "images/qr_codes"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ----------------------------
# SAMPLE DATA CREATION
# ----------------------------

from PIL import Image, ImageDraw, ImageFont

def create_placeholder_image(text, path, size=(400, 300), bg=(240,240,240), text_color=(0,0,0)):
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)

    # try to load a TrueType font, else fallback to default bitmap font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    # compute text width/height in a compatible way
    try:
        # Pillow >= 8/9+: textbbox exists and is recommended
        bbox = d.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        try:
            # older Pillow: textsize may exist
            text_w, text_h = d.textsize(text, font=font)
        except AttributeError:
            # last-resort fallback
            text_w, text_h = font.getsize(text)

    x = (size[0] - text_w) // 2
    y = (size[1] - text_h) // 2

    d.text((x, y), text, fill=text_color, font=font)
    img.save(path)

    img = Image.new('RGB', (400, 300), color=(100, 150, 200))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    text_w, text_h = d.textsize(text, font=font)
    d.text(((400 - text_w) / 2, (300 - text_h) / 2), text, fill=(255, 255, 255), font=font)
    img.save(path)

def generate_qr_code_image(item_id, path):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"Item ID: {item_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)

def create_sample_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            return  # Data exists, no need to recreate

    # Sample items
    items = [
        {
            "id": "11111111-aaaa-bbbb-cccc-111111111111",
            "type": "lost",
            "title": "Blue Backpack",
            "description": "Lost a blue backpack near the library",
            "category": "Bags",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "reported_at": "2025-08-10 10:00:00",
        },
        {
            "id": "22222222-bbbb-cccc-dddd-222222222222",
            "type": "found",
            "title": "Silver Wristwatch",
            "description": "Found a silver wristwatch in the cafeteria",
            "category": "Accessories",
            "latitude": 12.9720,
            "longitude": 77.5950,
            "reported_at": "2025-08-09 14:30:00",
        },
        {
            "id": "33333333-cccc-dddd-eeee-333333333333",
            "type": "lost",
            "title": "Black Jacket",
            "description": "Black jacket lost in auditorium",
            "category": "Clothing",
            "latitude": 12.9705,
            "longitude": 77.5930,
            "reported_at": "2025-08-08 18:20:00",
        },
    ]

    rows = []
    for item in items:
        image_path = os.path.join(IMAGES_DIR, f"{item['id']}.png")
        qr_code_path = os.path.join(QR_DIR, f"{item['id']}.png")

        create_placeholder_image(item['title'], image_path)
        generate_qr_code_image(item['id'], qr_code_path)

        row = {
            "id": item["id"],
            "type": item["type"],
            "title": item["title"],
            "description": item["description"],
            "category": item["category"],
            "image_path": image_path,
            "latitude": item["latitude"],
            "longitude": item["longitude"],
            "reported_at": item["reported_at"],
            "qr_code_path": qr_code_path,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(DATA_FILE, index=False)


# ----------------------------
# LOAD & SAVE FUNCTIONS
# ----------------------------
def load_data():
    create_sample_data()  # Ensure sample data exists on load

    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "id", "type", "title", "description", "category",
            "image_path", "latitude", "longitude",
            "reported_at", "qr_code_path"
        ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def generate_qr_code(item_id):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"Item ID: {item_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(QR_DIR, f"{item_id}.png")
    img.save(qr_path)
    return qr_path

# ----------------------------
# PAGES
# ----------------------------

def home_page():
    st.title("🏠 Lost & Found")
    st.write("""
        Welcome to the Lost & Found app!  
        - Report lost or found items.  
        - Browse and search reports.  
        - View items on a map.  
        - Use QR codes to help reunite items with their owners.
    """)

def report_item_page():
    st.title("📝 Report Lost/Found Item")
    df = load_data()

    with st.form("report_form", clear_on_submit=True):
        item_type = st.radio("Type", ["lost", "found"])
        title = st.text_input("Item Title")
        description = st.text_area("Description")
        category = st.selectbox("Category", ["Accessories", "Bags", "Clothing", "Electronics", "Other"])
        latitude = st.number_input("Latitude", format="%.6f")
        longitude = st.number_input("Longitude", format="%.6f")
        image_file = st.file_uploader("Upload Item Image", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Submit Report")

        if submitted:
            item_id = str(uuid.uuid4())
            image_path = ""
            if image_file:
                image = Image.open(image_file)
                image_path = os.path.join(IMAGES_DIR, f"{item_id}.png")
                image.save(image_path)

            qr_code_path = generate_qr_code(item_id)

            new_item = {
                "id": item_id,
                "type": item_type,
                "title": title,
                "description": description,
                "category": category,
                "image_path": image_path,
                "latitude": latitude,
                "longitude": longitude,
                "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "qr_code_path": qr_code_path
            }

            df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
            save_data(df)
            st.success("Item reported successfully!")

def browse_items_page():
    st.title("🔍 Browse Items")
    df = load_data()
    if df.empty:
        st.info("No items reported yet.")
        return

    filter_type = st.selectbox("Filter by type", ["All", "lost", "found"])
    if filter_type != "All":
        df = df[df["type"] == filter_type]

    search_term = st.text_input("Search by title or description")
    if search_term:
        df = df[df.apply(lambda row: search_term.lower() in row["title"].lower() or search_term.lower() in row["description"].lower(), axis=1)]

    titles = df["title"].tolist()
    selected_title = st.selectbox("Select an item to view details", ["-- Select --"] + titles)

    if selected_title != "-- Select --":
        selected_item = df[df["title"] == selected_title].iloc[0]

        if os.path.exists(selected_item["image_path"]):
            st.image(selected_item["image_path"], width=400)
        else:
            st.text("No image available")

        st.markdown(f"### {selected_item['title']} ({selected_item['type'].capitalize()})")
        st.write(f"**Description:** {selected_item['description']}")
        st.write(f"**Category:** {selected_item['category']}")
        st.write(f"**Location:** Lat {selected_item['latitude']}, Lon {selected_item['longitude']}")
        st.write(f"**Reported at:** {selected_item['reported_at']}")

        if os.path.exists(selected_item["qr_code_path"]):
            st.image(selected_item["qr_code_path"], caption="QR Code", width=150)

def map_view_page():
    st.title("🗺 Map View")
    df = load_data()
    if df.empty:
        st.info("No items to display on map.")
        return

    df_map = df[["latitude", "longitude", "title"]].dropna()
    st.map(df_map)

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df_map,
        get_position='[longitude, latitude]',
        get_color='[200, 30, 0, 160]',
        get_radius=50
    )
    view_state = pdk.ViewState(latitude=df_map["latitude"].mean(),
                               longitude=df_map["longitude"].mean(),
                               zoom=12)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# QR Code Scanner page using OpenCV and pyzbar

def qr_code_scanner_page():
    st.title("📷 QR Code Scanner")
    st.write("Upload a photo of a QR code to decode the item ID.")

    uploaded_file = st.file_uploader("Upload QR code image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        # Save to temp file to work with OpenCV
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        tfile.close()

        # Read image with OpenCV
        img = cv2.imread(tfile.name)
        if img is None:
            st.error("Error loading image. Please try another file.")
            return

        # Decode QR code using pyzbar
        try:
            from pyzbar import pyzbar
        except ImportError:
            st.error("Please install pyzbar to use QR code scanning: pip install pyzbar")
            return

        decoded_objects = pyzbar.decode(img)
        if not decoded_objects:
            st.warning("No QR code detected.")
        else:
            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                st.success(f"Decoded data: {data}")
                # If format is "Item ID: <id>", extract id and show item details
                if data.startswith("Item ID: "):
                    item_id = data.replace("Item ID: ", "").strip()
                    df = load_data()
                    item = df[df["id"] == item_id]
                    if not item.empty:
                        item = item.iloc[0]
                        st.markdown(f"### Item Details for ID: {item_id}")
                        if os.path.exists(item["image_path"]):
                            st.image(item["image_path"], width=400)
                        st.write(f"**Title:** {item['title']}")
                        st.write(f"**Description:** {item['description']}")
                        st.write(f"**Category:** {item['category']}")
                        st.write(f"**Type:** {item['type']}")
                        st.write(f"**Location:** Lat {item['latitude']}, Lon {item['longitude']}")
                        st.write(f"**Reported at:** {item['reported_at']}")
                    else:
                        st.warning("No item found with this ID.")

# ----------------------------
# MAIN APP
# ----------------------------

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Report Item", "Browse Items", "Map View", "QR Code Scanner"])

if page == "Home":
    home_page()
elif page == "Report Item":
    report_item_page()
elif page == "Browse Items":
    browse_items_page()
elif page == "Map View":
    map_view_page()
elif page == "QR Code Scanner":
    qr_code_scanner_page()
