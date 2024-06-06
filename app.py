from flask import Flask,jsonify,request
from flask_cors import CORS
import instaloader
import cv2
import os
import requests
import shutil
import numpy as np
import random

app = Flask(__name__)
CORS(app)
#data extraction
@app.route("/")
def Data():
    return jsonify({
        "username": "mukul"
    })

@app.route("/<string:id>")
def InstPageData(id):
    L = instaloader.Instaloader()
    random_number = random.randint(1, 4)

    if(random_number==1):
        L.login("mukulrai1729", "Mukul@123")
    elif(random_number==2):
        L.login("selflearner1729", "0610@Mrai")
    elif(random_number==3):
        L.login("reading4_u", "0610@Mrai")
    else:
        L.login("mukul_enterpreneur", "Mukul@123")
    
    
    profile = instaloader.Profile.from_username(L.context, id)
    total_views = 0

# Iterate over each post and sum up the view counts
    if(profile.mediacount>30):
        count=0
        for post in profile.get_posts():
            if(count>30):
                break
            else:
                try:
                    total_views +=post.video_view_count
                    count+=1
                except:
                    pass
        average_views=total_views//30
    elif(profile.mediacount==0):
        average_views=0
    else:
        for post in profile.get_posts():
            count=0
            try:
                total_views +=post.video_view_count
                count+=1
            except:
                pass
        average_views=total_views//count
    return jsonify({
        "username": profile.username,
        "full_name": profile.full_name,
        "followers": profile.followers,
        "following": profile.followees,
        "media_count": profile.mediacount,
        "bio": profile.external_url,
        "average_views":average_views,
        "profile_pic_url":profile.profile_pic_url
    })

#--------------------------------------------------reel views----------------------------------------------------
def get_reel_views(reel_url):
    # Initialize Instaloader
    L = instaloader.Instaloader()
    random_number = random.randint(1, 4)
    if(random_number==1):
        L.login("mukulrai1729", "Mukul@123")
    elif(random_number==2):
        L.login("selflearner1729", "0610@Mrai")
    elif(random_number==3):
        L.login("reading4_u", "0610@Mrai")
    else:
        L.login("mukul_enterpreneur", "Mukul@123")
    # Extract the short code from the reel URL
    short_code = reel_url.split("/")[-2]

    # Load the post using the short code
    try:
        post = instaloader.Post.from_shortcode(L.context, short_code)
        return {"views": post.video_view_count}
    except Exception as e:
        return {"error": str(e)}

@app.route("/views")  
def reel_views():
    reel_url = request.args.get('url')

    if not reel_url:
        return jsonify({"error": "Missing required parameter: reel_url"}), 400

    result = get_reel_views(reel_url)
    return jsonify(result)

#--------------------------------------reel verification--------------------------------------------------

def download_instagram_reel(reel_url, download_folder='reels'):
    # Initialize Instaloader
    L = instaloader.Instaloader(
        download_pictures=False,  # Don't download picture thumbnails
        download_videos=True,     # Download videos
        download_video_thumbnails=False,  # Don't download video thumbnails
        save_metadata=False,      # Don't save metadata
        compress_json=False       # Don't compress JSON
    )

    

    # Log in to Instagram
    random_number = random.randint(1, 4)
    if(random_number==1):
        L.login("mukulrai1729", "Mukul@123")
    elif(random_number==2):
        L.login("selflearner1729", "0610@Mrai")
    elif(random_number==3):
        L.login("reading4_u", "0610@Mrai")
    else:
        L.login("mukul_enterpreneur", "Mukul@123")

    # Extract the short code from the reel URL
    short_code = reel_url.split("/")[-2]

    # Load the post using the short code
    post = instaloader.Post.from_shortcode(L.context, short_code)

    # Check if the post is a video
    if post.is_video:
        print(f"Downloading reel: {post.url}")

        # Create the target folder if it doesn't exist
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        # Download the post (which includes the video)
        L.download_post(post, target=download_folder)

        # Look for the downloaded video file in the target folder
        for file_name in os.listdir(download_folder):
            if file_name.endswith('.mp4'):
                return os.path.join(download_folder, file_name)
        
        print("Failed to find the downloaded video file.")
        return None
    else:
        print("The provided URL is not a reel.")
        return None

def read_image_from_url(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        image_array = np.asarray(bytearray(response.content), dtype="uint8")
        image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
        return image
    else:
        print(f"Failed to read image from URL. Status code: {response.status_code}")
        return None


def is_image_present_in_video(video_path, input_image, min_match_count=10):
    # Load input image

    # Initialize SIFT detector
    sift = cv2.SIFT_create()

    # Detect keypoints and compute descriptors for the input image
    kp1, des1 = sift.detectAndCompute(input_image, None)

    # Open video capture
    cap = cv2.VideoCapture(video_path)

    # Read first 10 seconds of frames
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    duration = 10  # seconds
    num_frames = int(frame_rate * duration)
    for _ in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect keypoints and compute descriptors for the frame
        kp2, des2 = sift.detectAndCompute(frame_gray, None)

        # Initialize brute force matcher
        bf = cv2.BFMatcher()

        # Match descriptors
        matches = bf.knnMatch(des1, des2, k=2)

        # Apply ratio test
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        # Check if enough good matches are found
        if len(good_matches) >= min_match_count:
            cap.release()
            return True
        else:
            return False
        

    cap.release()
    return False

def main(reel_url, image_url):
    # Extract the short code from the reel URL
    short_code = reel_url.split("/")[-2]

    # Create a download folder named after the short code
    download_folder = short_code
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    try:
        # Download the image from the provided URL
        input_image = read_image_from_url(image_url)

        if input_image is not None:
            # Download the reel
            video_path = download_instagram_reel(reel_url, download_folder)

            if video_path:
                # Check if the image is present in the video
                result = is_image_present_in_video(video_path, input_image)
                print("Image found in video" if result else "Image not found in video")
                return result
            else:
                print("Failed to download the reel or the URL is not a reel.")
        else:
            print("Failed to download the image from the URL.")
    finally:
        # Delete the entire download folder
        shutil.rmtree(download_folder)
        print(f"Deleted the download folder: {download_folder}")


@app.route("/process")
def post():
    reel_url = request.args.get('reel_url')
    input_image_path = request.args.get('input_image_path')

    if not reel_url or not input_image_path:
        return jsonify({"error": "Missing required parameters"}), 400
    result = main(reel_url, input_image_path)
    return jsonify(result)

if __name__=="__main__":
    app.run(host='0.0.0.0',port=8080)