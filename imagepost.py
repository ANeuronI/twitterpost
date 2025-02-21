import streamlit as st
from PIL import Image
import tweepy
import os
import io

st.title("Image Resizer & Twitter Publisher")
st.write("Upload an image to resize it into multiple dimensions and post to your Twitter (X) account.")


# Twitter API Authentication

st.sidebar.header("Twitter API Credentials")
consumer_key = st.sidebar.text_input("Consumer Key (API Key)")
consumer_secret = st.sidebar.text_input("Consumer Secret (API Secret)", type="password")
access_token = st.sidebar.text_input("Access Token")
access_token_secret = st.sidebar.text_input("Access Token Secret", type="password")

if st.sidebar.button("Authenticate with Twitter"):
    try:
        auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
        api = tweepy.API(auth)
        # Test the credentials by verifying the connection
        api.verify_credentials()
        st.sidebar.success("Authenticated with Twitter!")
        st.session_state['api'] = api
    except Exception as e:
        st.sidebar.error("Authentication failed: " + str(e))


# Image Upload

uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
if uploaded_file is not None:
    try:
        original_image = Image.open(uploaded_file)
        st.image(original_image, caption="Original Image", use_column_width=True)
    except Exception as e:
        st.error("Error opening image: " + str(e))
    
    
    # Choose Resizing Options
    
    st.subheader("Select Image Sizes")
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
    
    
    # Process (Resize) the Image
    
    if st.button("Process Image"):
        resized_images = []
        for idx, (w, h) in enumerate(sizes):
            try:
                resized = original_image.resize((w, h))
                resized_images.append(resized)
            except Exception as e:
                st.error(f"Error resizing image to {w}x{h}: {e}")
        if resized_images:
            st.success("Image processed successfully!")
            st.subheader("Resized Images Preview")
            cols = st.columns(2)
            for i, img in enumerate(resized_images):
                with cols[i % 2]:
                    st.image(img, caption=f"Size: {sizes[i][0]}x{sizes[i][1]}")
        
        
        # Post Images to Twitter (X)
        
        if st.button("Post Resized Images to Twitter"):
            if 'api' not in st.session_state:
                st.error("Twitter API not authenticated. Please enter your credentials in the sidebar.")
            else:
                api = st.session_state['api']
                for i, img in enumerate(resized_images):
                    try:
                        # Save image temporarily to disk (Tweepy expects a filename)
                        temp_filename = f"temp_{sizes[i][0]}x{sizes[i][1]}.png"
                        img.save(temp_filename)
                        
                        # Upload image and post tweet
                        media = api.media_upload(temp_filename)
                        tweet_text = f"Resized image to {sizes[i][0]}x{sizes[i][1]}"
                        api.update_status(status=tweet_text, media_ids=[media.media_id])
                        st.success(f"Posted image {sizes[i][0]}x{sizes[i][1]} successfully!")
                        
                        # Clean up the temporary file
                        os.remove(temp_filename)
                    except Exception as e:
                        st.error(f"Failed to post image {sizes[i][0]}x{sizes[i][1]}: {e}")
