from dotenv import dotenv_values
from PIL import Image
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
import streamlit as st


# Streamlit App UI
st.set_page_config(
    page_title="::: Cartoonize GPT :::",
    page_icon="🎨",
)
st.title("Cartoonize your Photo")


# Load Configuration
if "CLOUDFLARE_ACCOUNT_ID" in st.secrets:
    ACCOUNT_ID = st.secrets["CLOUDFLARE_ACCOUNT_ID"]
    API_KEY = st.secrets["CLOUDFLARE_API_TOKEN_IMAGES"]
else:
    config = dotenv_values(".env")
    ACCOUNT_ID = config["CLOUDFLARE_ACCOUNT_ID"]
    API_KEY = config["CLOUDFLARE_API_TOKEN_IMAGES"]


# Handle OAuth Login
st.login()
user = st.experimental_user

if user.is_logged_in:
    st.success(f"✅ Welcome to Cartoonize GPT, {user.name}님!")
    st.write("- User Info:")
    st.json(user.to_dict())
else:
    st.warning("Check your Account!")
    st.stop()

with st.sidebar:
    # Cartoon Style
    selected_style = st.selectbox(
        "Choose a Cartoon Style",
        (
            "케이팝 | k-pop",
            "뽀로로 | ppororo",
            "지브리 | ghibli",
            "짱구   | crayon shinchan",
            "디즈니 | disney",
            "고흐   | van gogh",
            "피카소 | picaso",
        ),
    )

    # Link to Github Repo
    st.markdown("---")
    github_link = (
        "https://github.com/toweringcloud/cartoonize-gpt/blob/main/app_cloudflare.py"
    )
    badge_link = "https://badgen.net/badge/icon/GitHub?icon=github&label"
    st.write(f"[![Repo]({badge_link})]({github_link})")


def upload_image_to_cloudflare(image_file):
    """Upload Image on Storage Server using Cloudflare Images API"""
    CLOUDFLARE_UPLOAD_URL = (
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/images/v1"
    )

    encoder = MultipartEncoder(
        fields={"file": (image_file.name, image_file, "image/jpeg")}
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": encoder.content_type,
    }

    response = requests.post(CLOUDFLARE_UPLOAD_URL, headers=headers, data=encoder)

    if response.status_code == 200:
        return response.json()["result"]["variants"][0]
    else:
        st.error(f"Failed to upload: {response.text}")
        return None


if not API_KEY:
    st.error("Please input your Cloudflare API Token on runtime configuration")
else:
    uploaded_file = st.file_uploader("Upload your photo!", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # Check File Size (Max 3MB)
        if uploaded_file.size > 3 * 1024 * 1024:
            st.warning("File size exceeds 3MB. Try again.")
        else:
            # Load Original Image
            image = Image.open(uploaded_file)

            # Select Image Rataion
            rotation = st.radio("Image Rotation", ("None", "Left 90", "Right 90"))
            if rotation == "Left 90":
                image = image.rotate(90, expand=True)
            elif rotation == "Right 90":
                image = image.rotate(-90, expand=True)

            #  Show Original Image
            st.image(image, caption="Original Image", use_container_width=True)

            # Action to Cartoonize
            if st.button("Cartoonize your photo!"):
                # Upload Image on Cloudflare Storage
                image_url = None
                with st.spinner("Uploading..."):
                    image_url = upload_image_to_cloudflare(uploaded_file)

                if image_url:
                    st.success("✅ Uploaded!")

                    # Transform Uploaded Image using Cloudflare Workers
                    art_style = selected_style.split(" | ")[1]
                    files = {"file": uploaded_file.getvalue(), "style": art_style}

                    with st.spinner("Transforming..."):
                        response = requests.post(
                            "https://cartoonize.toweringcloud.workers.dev", files=files
                        )

                    if response.status_code == 200:
                        result = response.json()
                        cartoon_url = result.get("result", {}).get("variants", [])[0]

                        if cartoon_url:
                            st.success("✅ Transformed!")

                            # Show Transformed Image
                            st.image(
                                cartoon_url,
                                caption=f"{art_style} style of cartoon",
                                use_container_width=True,
                            )
                        else:
                            st.error("Failed to transform...😢")
