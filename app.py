from flask import Flask, render_template, request,session ,redirect,jsonify,flash,url_for
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
from random import random
from models import db, User, Video
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime  # Ensure you import datetime here
import moviepy.editor as mp
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import subprocess


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# Load Word2Vec model
print("Loading Word2Vec model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()



answers = {
       "Tell me about yourself": "I am a dedicated and adaptable individual . I  and have developed a strong interest in problem-solving, teamwork, and continuous learning. In my past experiences, I’ve worked on both individual and group projects where I’ve learned to manage time efficiently and communicate effectively. I take pride in being organized, goal-oriented, and motivated to take on challenges that help me grow both personally and professionally.",

    "Why should I hire you?": "You should consider hiring me because I offer a strong mix of technical abilities, a proactive attitude, and the ability to work collaboratively in a team. I am quick to learn, open to feedback, and focused on delivering high-quality results. I believe in taking responsibility for my tasks and ensuring that goals are met within deadlines. Additionally, I bring a positive energy and a mindset that looks for solutions instead of problems.",

    "What are your strengths and weaknesses?": "One of my key strengths is my ability to remain calm and focused under pressure, which allows me to make clear decisions even in stressful situations. I’m also very organized and dependable, always aiming to deliver high-quality work. On the other hand, one area I’ve been working on is delegating tasks. I tend to take on too much responsibility myself, but I’m learning to trust my team and distribute work more effectively to ensure better outcomes.",

    "Why do you want to work at our company?": "Your company has a reputation for innovation, employee development, and excellence in service.  I’m eager to work in an environment that encourages growth and collaboration, and I believe this role will offer the challenges and learning opportunities I’m seeking as I build my career.",

    "Difference between confidence and overconfidence": "Confidence is the self-assurance that comes from preparation, knowledge, and experience. It allows you to face challenges calmly and competently. Overconfidence, on the other hand, is when someone overestimates their abilities and underestimates the difficulty of a task, often leading to mistakes. While confidence is grounded in reality, overconfidence can lead to careless decisions and poor planning.",

    "Difference between hard work and smart work": "Hard work involves consistent effort and dedication over time, such as working long hours and taking on tasks with full commitment. Smart work, however, is about using strategies, tools, and planning to achieve results more efficiently. Smart workers prioritize tasks, find creative solutions, and optimize processes without compromising on quality, often achieving more in less time.",

    "How do you feel about working at night and weekends?": "I understand that certain roles require flexibility in working hours, especially when deadlines are tight or when clients are in different time zones. I’m fully open to working night shifts or weekends if it’s necessary for the success of the project or organization. I believe commitment and adaptability are key to succeeding in any professional environment.",

    "Can you work under pressure?": "Yes, I can. In fact, I’ve often found that pressure sharpens my focus and motivates me to stay organized and perform better. For instance, during my final year project, we faced unexpected setbacks close to the submission deadline. I restructured the timeline, divided responsibilities within the team, and ensured we delivered a quality project on time. I believe pressure, when managed well, can lead to growth and innovation.",

    "What are your goals?": "My short-term goal is to join an organization where I can apply my skills and grow as a professional. I want to be part of a team that values learning and development. In the long term, I aim to take on leadership roles where I can mentor others, contribute to strategic decisions, and make a meaningful impact on the company’s success.",

    "What motivates you to do a job?": "I am motivated by a sense of purpose and accomplishment. Knowing that my work contributes to a larger goal keeps me focused and energized. I also find motivation in learning new things and overcoming challenges, whether it’s solving a technical issue or finding a better way to complete a task. Recognition and constructive feedback also inspire me to keep improving.",

    "What makes you angry?": "I try to maintain emotional balance, but what frustrates me is a lack of accountability or repeated dishonesty in a team setting. I believe in open communication and mutual respect, so when someone consistently avoids responsibility or doesn’t communicate, it can affect team morale. I handle such situations by calmly addressing the issue and trying to understand their perspective before jumping to conclusions.",

    "Give me an example of your creativity": "During a college event, I was part of the organizing team and we were short on budget for decorations. I proposed using recycled materials and digital projection for visual effects instead of physical items. The result was unique and appreciated by the attendees, and we stayed within budget. I believe creativity is about solving problems in an innovative way, not just being artistic.",

    "How long would you expect to work for us if hired?": "I am looking for long-term opportunities where I can grow with the organization. As long as I am learning, contributing, and feel that my work is making a difference, I’d be committed to staying and advancing within the company.",

    "What are your career options right now?": "I am exploring roles where I can utilize both my technical and interpersonal skills. I’ve applied to a few companies that align with my interests, but this role in particular stands out because of the responsibilities, culture, and potential to grow.",

    "Explain how you would be an asset to this organization": "I bring not just the skills listed on my resume but also a willingness to take initiative, learn new tools quickly, and collaborate with others. I take ownership of my work and always look for ways to improve processes or outcomes. I believe I’d contribute positively to the team and help drive the organization’s goals forward.",

    "What are your outside interests?": "Outside of work, I enjoy reading non-fiction, hiking, and working on personal development through online courses. I also volunteer occasionally, as I believe giving back to the community helps you grow as a person.",

    "Would you lie for the company?": "I believe in integrity and honesty. I would never do anything that compromises my values or the company’s reputation. I would handle difficult situations diplomatically, ensuring that we protect both the truth and the interests of the organization.",

    "Who has inspired you in your life?": "My father has been a big inspiration. His discipline, perseverance, and attitude toward problem-solving have taught me how to stay focused and overcome obstacles without giving up."
    
}
# Function to get the average vector of a text (for cosine similarity)
def get_avg_vector(text):
    embedding = model.encode(text)
    return np.array(embedding)

@app.before_request
def before_request():
    print(f"Before Request Triggered. Endpoint: {request.endpoint}, Authenticated: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        print("User is authenticated. Current Endpoint:", request.endpoint)

        # Exempt static files, API calls, and favicon
        if request.path.startswith('/static') or request.path.startswith('/api') or request.path == '/favicon.ico':
            return  # Do nothing, continue normally

        # Exclude form submissions (POST requests)
        if request.method == 'POST':
            print("POST request detected. Not logging out.")
            return  # Skip logout on POST requests
        
        # Only detect refresh on GET requests (not video recording)
        if request.method == 'GET':
            if request.endpoint is None:
                print("Request with None endpoint. Ignoring.")
                return

            if 'last_page' not in session:
                session['last_page'] = request.endpoint
                print("First visit, setting last_page.")
            elif session.get('last_page') == request.endpoint:
                print("Page refresh detected. Logging out.")
                logout_user()
                session.clear()
                return redirect(url_for('home'))
            else:
                print("Navigating to a new page.")
                session['last_page'] = request.endpoint
    else:
        print("User is not authenticated. No logout.")


@app.route("/", methods=["GET"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for("task"))
    return render_template("home.html")

# This is the route that will handle the main task page after login
@app.route("/task", methods=["GET", "POST"])
@login_required  # Protect the page so only logged-in users can access
def task():
    score = None
    average_score = 0.0
    selected_question = list(answers.keys())[0]
    user_answer = ""

    if "score_history" not in session:
        session["score_history"] = {}
        session.modified = True

    if request.method == "POST":
        selected_question = request.form["question"]

        # Fetch the transcribed answer from the most recent video
        user_answer = session.get("last_transcribed_answer", "")
        if not user_answer:
            return render_template("index.html",
                                   questions=answers.keys(),
                                   score=score,
                                   average_score=average_score,
                                   selected=selected_question,
                                   user_answer="No transcribed answer found.",
                                   model_answer=answers.get(selected_question))

        expected_answer = answers[selected_question]
        user_vec = get_avg_vector(user_answer)
        expected_vec = get_avg_vector(expected_answer)

        score = cosine_similarity([user_vec], [expected_vec])[0][0] * 100
        score = float(round(score, 2))

        session["score_history"][selected_question] = score
        session.modified = True

        # Average of most recent scores per unique question
        score_values = list(session["score_history"].values())
        if score_values:
            average_score = round(sum(score_values) / len(score_values), 2)

    elif "score_history" in session:
        score_values = list(session["score_history"].values())
        if score_values:
            average_score = round(sum(score_values) / len(score_values), 2)

    return render_template("index.html",
                           questions=answers.keys(),
                           score=score,
                           average_score=average_score,
                           selected=selected_question,
                           user_answer=user_answer,
                           model_answer=answers.get(selected_question))

def fix_webm_duration(filepath):
    try:
        # Verify if the video is already readable
        clip = mp.VideoFileClip(filepath)
        clip.close()
        print("WebM file is valid. No fix needed.")
        return filepath

    except Exception:
        print("Error opening video file. Attempting to fix with FFmpeg.")

        fixed_filepath = filepath.replace('.webm', '_fixed.webm')
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', filepath,
            '-c:v', 'libvpx-vp9', '-c:a', 'libopus',  # Recommended codecs for WebM
            '-fflags', '+genpts', fixed_filepath
        ]

        try:
            result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
            print("FFmpeg Output:", result.stdout)
            print("FFmpeg Error:", result.stderr)
            if os.path.exists(fixed_filepath):
                return fixed_filepath
            else:
                raise Exception("FFmpeg failed to create fixed file.")

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg command failed: {e}")
            raise Exception("FFmpeg failed to fix the video.")


# Upload video route
@app.route('/upload_video', methods=['POST'])
@login_required
def upload_video():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request format. Expected JSON data.'}), 400

        video_data = data.get('video')
        if not video_data:
            return jsonify({'error': 'No video data provided.'}), 400

        if not video_data.startswith('data:video'):
            return jsonify({'error': 'Invalid video format. Ensure it is base64 encoded.'}), 400

        # Decode the base64 data
        try:
            video_base64 = video_data.split(",")[1]
            video_data_bytes = base64.b64decode(video_base64)
        except (IndexError, base64.binascii.Error) as e:
            return jsonify({'error': 'Malformed base64 data.'}), 400

        # Save video
        user_folder = os.path.join('static', 'uploads', current_user.username)
        os.makedirs(user_folder, exist_ok=True)
        filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.webm'
        filepath = os.path.join(user_folder, filename)

        with open(filepath, 'wb') as f:
            f.write(video_data_bytes)

        # Fix WebM duration if necessary
        fixed_filepath = fix_webm_duration(filepath)

        # Extract audio from video (if audio exists)
        video_clip = mp.VideoFileClip(fixed_filepath)
        if not video_clip.audio:
            return jsonify({'error': 'No audio track found in the video.'}), 400

        audio_clip = video_clip.audio
        audio_filepath = fixed_filepath.replace('.webm', '.wav')
        audio_clip.write_audiofile(audio_filepath)

        # Speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_filepath) as source:
            audio = recognizer.record(source)

        user_answer = recognizer.recognize_google(audio)
        print(f"Transcribed Text: {user_answer}")

        # Store transcribed answer in session
        session['last_transcribed_answer'] = user_answer
        session.modified = True

        # Save video info to the database
        video = Video(filename=filename, user_id=current_user.id)
        db.session.add(video)
        db.session.commit()

        return jsonify({
            'message': 'Video uploaded and processed successfully!',
            'transcribed_text': user_answer,
            'filepath': fixed_filepath
        }), 200

    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand the audio.'}), 400

    except sr.RequestError as e:
        return jsonify({'error': f'Google Speech Recognition error: {e}'}), 500

    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        user = User(username=username, password=password)
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", 'danger')
            return redirect('/register')
        
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! You can now login.", 'success')
        return redirect('/login')  # Redirect to login page after successful registration
    return render_template('register.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('task'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists in the database
        user = User.query.filter_by(username=username).first()
        
        # If the user exists and password matches
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful!", "success")
            return redirect(url_for('task'))
        else:
            flash('Login Failed. Check your username and/or password', 'danger')
            # Optional: You could log the failed attempt to the console for debugging
            print(f"Failed login attempt for username: {username}")
    
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/reset")
def reset():
    session["score_history"] = {}
    session.modified = True
    return redirect("/")


if __name__ == "__main__": 
    app.run(debug=True) 
print("Current endpoint:", request.endpoint)
