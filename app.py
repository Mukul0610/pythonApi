from flask import Flask, jsonify, request
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

# Global variable to store the logged-in Instaloader instance
instaloader_instance = None

# Login credentials
credentials = [
    ("mukulrai1729", "Mukul@123"),
    ("selflearner1729", "0610@Mrai"),
    ("reading4_u", "0610@Mrai"),
    ("mukul_enterpreneur", "Mukul@123")
]

def login_instaloader():
    global instaloader_instance
    if instaloader_instance is not None:
        return instaloader_instance

    L = instaloader.Instaloader()
    for username, password in credentials:
        try:
            L.login(username, password)
            instaloader_instance = L
            return instaloader_instance
        except instaloader.exceptions.ConnectionException as e:
            if 'checkpoint required' in str(e):
                continue
            else:
                return None
    return None

@app.route("/")
def Data():
    return jsonify({
        "username": "mukul"
    })

@app.route("/<string:id>")
def InstPageData(id):
    L = login_instaloader()
    if not L:
        return jsonify({
            "error": "Failed to log in with all provided credentials.",
            "message": "Please complete any required checkpoints and try again."
        }), 401
    
    try:
        profile = instaloader.Profile.from_username(L.context, id)
        total_views = 0

        if profile.mediacount > 30:
            count = 0
            for post in profile.get_posts():
                if count > 30:
                    break
                else:
                    try:
                        total_views += post.video_view_count
                        count += 1
                    except:
                        pass
            average_views = total_views // 30
        elif profile.mediacount == 0:
            average_views = 0
        else:
            count = 0
            for post in profile.get_posts():
                try:
                    total_views += post.video_view_count
                    count += 1
                except:
                    pass
            average_views = total_views // count
        
        return jsonify({
            "username": profile.username,
            "full_name": profile.full_name,
            "followers": profile.followers,
            "following": profile.followees,
            "media_count": profile.mediacount,
            "bio": profile.external_url,
            "average_views": average_views,
            "profile_pic_url": profile.profile_pic_url
        })
    except instaloader.exceptions.ConnectionException as e:
        if 'checkpoint required' in str(e):
            return jsonify({
                "error": "Checkpoint required",
                "message": "Please complete the checkpoint in your browser and try again.",
                "url": "https://www.instagram.com/challenge/"
            }), 401
        else:
            return jsonify({"error": "Login failed", "message": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "An error occurred", "message": str(e)}), 500

def get_reel_views(reel_url):
    L = login_instaloader()
    if not L:
        return {"error": "Failed to log in with all provided credentials."}

    try:
        short_code = reel_url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, short_code)
        return {"views": post.video_view_count}
    except instaloader.exceptions.ConnectionException as e:
        if 'checkpoint required' in str(e):
            return {"error": "Checkpoint required. Please complete the checkpoint in your browser and try again."}
        else:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

@app.route("/views")
def reel_views():
    reel_url = request.args.get('url')
    if not reel_url:
        return jsonify({"error": "Missing required parameter: reel_url"}), 400
    result = get_reel_views(reel_url)
    return jsonify(result)

def download_instagram_reel(reel_url, download_folder='reels'):
    L = login_instaloader()
    if not L:
        return {"error": "Failed to log in with all provided credentials."}

    try:
        short_code = reel_url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, short_code)

        if post.is_video:
            print(f"Downloading reel: {post.url}")
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)
            L.download_post(post, target=download_folder)
            for file_name in os.listdir(download_folder):
                if file_name.endswith('.mp4'):
                    return os.path.join(download_folder, file_name)
            print("Failed to find the downloaded video file.")
            return None
        else:
            print("The provided URL is not a reel.")
            return None
    except instaloader.exceptions.ConnectionException as e:
        if 'checkpoint required' in str(e):
            return {"error": "Checkpoint required. Please complete the checkpoint in your browser and try again."}
        else:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

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
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(input_image, None)
    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    duration = 10
    num_frames = int(frame_rate * duration)
    for _ in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            break
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp2, des2 = sift.detectAndCompute(frame_gray, None)
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
        if len(good_matches) >= min_match_count:
            cap.release()
            return True
    cap.release()
    return False

def main(reel_url, image_url):
    short_code = reel_url.split("/")[-2]
    download_folder = short_code
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    try:
        input_image = read_image_from_url(image_url)
        if input_image is not None:
            video_path = download_instagram_reel(reel_url, download_folder)
            if video_path:
                result = is_image_present_in_video(video_path, input_image)
                print("Image found in video" if result else "Image not found in video")
                return result
            else:
                print("Failed to download the reel or the URL is not a reel.")
        else:
            print("Failed to download the image from the URL.")
    finally:
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
