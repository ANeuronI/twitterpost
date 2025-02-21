import streamlit as st
from PIL import Image
import tweepy
import os

st.title("Image Resizer & Twitter Publisher")
st.write("Upload an image, resize it into 4 dimensions, and post all images to your Twitter account.")

# Twitter API Credentials (both v1 and v2)

if "TWITTER_CONSUMER_KEY" in st.secrets:
    consumer_key = st.secrets["TWITTER_CONSUMER_KEY"]
    consumer_secret = st.secrets["TWITTER_CONSUMER_SECRET"]
    access_token = st.secrets["TWITTER_ACCESS_TOKEN"]
    access_token_secret = st.secrets["TWITTER_ACCESS_TOKEN_SECRET"]
    bearer_token = st.secrets["TWITTER_BEARER_TOKEN"]
    st.sidebar.info("Twitter API keys loaded from secrets.")
else:
    st.sidebar.header("Twitter API Credentials")
    consumer_key = st.sidebar.text_input("Consumer Key (API Key)")
    consumer_secret = st.sidebar.text_input("Consumer Secret (API Secret)", type="password")
    access_token = st.sidebar.text_input("Access Token")
    access_token_secret = st.sidebar.text_input("Access Token Secret", type="password")
    bearer_token = st.sidebar.text_input("Bearer Token")

# Authenticate with Twitter
if st.sidebar.button("Authenticate with Twitter"):
    try:
        # V1 Twitter API Authentication (for media uploads)
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # V2 Twitter API Authentication (for creating tweets)
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )
        
        # Verify authentication using the v2 client (get your account info)
        user = client.get_me()
        st.sidebar.success(f"Authenticated as @{user.data.username}")
        st.session_state['api'] = api
        st.session_state['client'] = client
    except Exception as e:
        st.sidebar.error("Authentication failed: " + str(e))
        st.sidebar.exception(e)


# Image Upload

uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    try:
        original_image = Image.open(uploaded_file)
        st.image(original_image, caption="Original Image", use_column_width=True)
    except Exception as e:
        st.error("Error opening image: " + str(e))
    
    
    # Resize Options
    
    st.subheader("Resize Options")
    use_default = st.checkbox("Use default sizes (300x250, 728x90, 160x600, 300x600)", value=True)
    if not use_default:
        width1 = st.number_input("Width for Image 1", value=300)
        height1 = st.number_input("Height for Image 1", value=250)
        width2 = st.number_input("Width for Image 2", value=728)
        height2 = st.number_input("Height for Image 2", value=90)
        width3 = st.number_input("Width for Image 3", value=160)
        height3 = st.number_input("Height for Image 3", value=600)
        width4 = st.number_input("Width for Image 4", value=300)
        height4 = st.number_input("Height for Image 4", value=600)
        sizes = [(width1, height1), (width2, height2), (width3, height3), (width4, height4)]
    else:
        sizes = [(300, 250), (728, 90), (160, 600), (300, 600)]
    
    
    # Resize the Image into Four Dimensions
    
    if st.button("Resize Image"):
        resized_images = []
        for (w, h) in sizes:
            try:
                resized = original_image.resize((w, h))
                resized_images.append(resized)
            except Exception as e:
                st.error(f"Error resizing image to {w}x{h}: {e}")
        if resized_images:
            st.success("Image resized successfully!")
            st.subheader("Resized Images Preview")
            cols = st.columns(2)
            for i, img in enumerate(resized_images):
                with cols[i % 2]:
                    st.image(img, caption=f"Size: {sizes[i][0]}x{sizes[i][1]}", use_column_width=True)
            st.session_state['resized_images'] = resized_images
            st.session_state['sizes'] = sizes

    
    # Post All Resized Images to Twitter
    
    if st.button("Post All Resized Images to Twitter"):
        if 'api' not in st.session_state or 'client' not in st.session_state:
            st.error("Twitter API not authenticated. Please authenticate using the sidebar.")
        elif 'resized_images' not in st.session_state:
            st.error("Please resize the image first.")
        else:
            api = st.session_state['api']
            client = st.session_state['client']
            media_ids = []
            temp_files = []
            # Loop through each resized image, save it temporarily, and upload it using the v1 API.
            for i, img in enumerate(st.session_state['resized_images']):
                size_label = f"{st.session_state['sizes'][i][0]}x{st.session_state['sizes'][i][1]}"
                temp_filename = f"temp_{size_label}.png"
                try:
                    img.save(temp_filename)
                    temp_files.append(temp_filename)
                    st.write(f"Uploading image {temp_filename} ...")
                    media = api.media_upload(filename=temp_filename)
                    st.write(f"Uploaded image {size_label} with media_id: {media.media_id_string}")
                    media_ids.append(media.media_id_string)
                except Exception as e:
                    st.error(f"Failed to upload image {size_label}: {e}")
                    st.exception(e)
            st.write(f"Collected Media IDs: {media_ids}")
            if media_ids:
                try:
                    tweet_text = "Here are my resized images:"
                    st.write("Posting tweet with images...")
                    response = client.create_tweet(text=tweet_text, media_ids=media_ids)
                    st.success("All resized images posted to Twitter!")
                    # st.write("Tweet details:", response)
                except Exception as e:
                    st.error("Failed to post tweet: " + str(e))
                    st.exception(e)
            # Clean up temporary files
            for filename in temp_files:
                if os.path.exists(filename):
                    os.remove(filename)
