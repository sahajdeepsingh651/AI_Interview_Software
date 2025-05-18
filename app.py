from flask import Flask, render_template, request,session ,redirect,jsonify,flash,url_for
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
from models import db, User, TestResult
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime  # Ensure you import datetime here
import moviepy.editor as mp
import speech_recognition as sr
import subprocess
from flask_migrate import Migrate

import onnxruntime as rt
from transformers import AutoTokenizer

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# Load Word2Vec model
# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

onnx_model_path = os.path.join("onnx_model", "model.onnx")
try:
    onnx_session = rt.InferenceSession(onnx_model_path)
    print("ONNX model loaded successfully.")
except Exception as e:
    print(f"Error loading ONNX model: {e}")
    onnx_session = None


print("Loading  model...")

print("Model loaded.")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)
migrate = Migrate(app, db)

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

    "Difference between hard work and  smart work": "Hard work involves consistent effort and dedication over time, such as working long hours and taking on tasks with full commitment. Smart work, however, is about using strategies, tools, and planning to achieve results more efficiently. Smart workers prioritize tasks, find creative solutions, and optimize processes without compromising on quality, often achieving more in less time.",

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
def get_embeddings(sentences):
    if onnx_session is None:
        raise ValueError("ONNX model is not loaded.")

    if isinstance(sentences, str):
        sentences = [sentences]

    try:
        # Tokenize input sentences with numpy output
        encoded_input = tokenizer(
            sentences,
            padding=True,
            truncation=True,
            return_tensors="np"
        )
        
        inputs = {
            "input_ids": encoded_input["input_ids"].astype(np.int64),
            "attention_mask": encoded_input["attention_mask"].astype(np.int64),
        }

        # Include token_type_ids if model requires them
        if "token_type_ids" in encoded_input:
            inputs["token_type_ids"] = encoded_input["token_type_ids"].astype(np.int64)

        # Run ONNX model to get output embeddings
        outputs = onnx_session.run(None, inputs)
        embeddings = outputs[0]  # Typically shape (batch_size, seq_len, embed_dim)

        print(f"Output embeddings shape: {embeddings.shape}")

        # If output is token embeddings, do mean pooling using attention mask
        if embeddings.ndim == 3:
            attention_mask = encoded_input["attention_mask"].astype(np.float32)
            mask_expanded = np.expand_dims(attention_mask, axis=-1)  # (batch, seq_len, 1)

            summed = np.sum(embeddings * mask_expanded, axis=1)
            counts = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)  # avoid div by 0

            sentence_embeddings = summed / counts  # (batch_size, embed_dim)
        elif embeddings.ndim == 2:
            sentence_embeddings = embeddings  # Already sentence-level
        else:
            raise ValueError(f"Unexpected embeddings shape: {embeddings.shape}")

        # Ensure embeddings are always 2D
        if sentence_embeddings.ndim == 1:
            sentence_embeddings = sentence_embeddings.reshape(1, -1)  # (1, embed_dim)

        print(f"Final sentence embeddings shape: {sentence_embeddings.shape}")

        # If single sentence, return just one embedding vector
        if len(sentence_embeddings) == 1:
            return sentence_embeddings[0].reshape(1, -1)
        
        return sentence_embeddings

    except Exception as e:
        print(f"Error in generating embeddings: {e}")
        return None

@app.before_request
def log_current_endpoint():
    print("Current endpoint:", request.endpoint)

@app.before_request
def before_request():
    print(f"Before Request Triggered. Endpoint: {request.endpoint}, Authenticated: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        print("User is authenticated. Current Endpoint:", request.endpoint)

        # Exempt static files, API calls, and favicon
        if request.path.startswith('/static') or request.path.startswith('/api') or request.path == '/favicon.ico':
            return  # Continue normally

        # Skip logout check if flagged (after POST redirect)
        if session.get('skip_logout_check'):
            print("Skipping logout check due to POST redirect.")
            session.pop('skip_logout_check', None)  # Remove flag after use
            session['last_page'] = request.endpoint
            return

        # Exclude POST and AJAX requests from logout
        if request.method == 'POST' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print("POST or AJAX request detected. Not logging out.")
            return
        
        # Detect refresh only on GET requests
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


@app.route("/task", methods=["GET", "POST"])
@login_required
def task():
    if request.method == "POST":
        data = request.get_json()
        selected_question = data.get("question")
        print("All questions and expected answers:")
        for q, a in answers.items():
            print(f"Q: {q} => A: {a}")


        user_answer = session.get("last_transcribed_answer", "")
        if not user_answer:
            print("No transcribed answer found in session")
            return jsonify({
                "error": "No transcribed answer found.",
                "score": None,
                "average_score": None,
                "transcribed_text": "No answer transcribed yet."
            })

        expected_answer = answers.get(selected_question)
        user_vec = get_embeddings(user_answer)
        expected_vec = get_embeddings(expected_answer)
        fscore = cosine_similarity(user_vec, expected_vec)[0][0] * 100
        if user_vec is None or expected_vec is None:
            return jsonify({'error': 'Failed to generate embeddings.'}), 500
        
        score = round(float(fscore), 2)

        if "score_history" not in session:
            session["score_history"] = {}

        # Initialize list for question if doesn't exist
        if selected_question not in session["score_history"]:
            session["score_history"][selected_question] = []

        # Append new score for the selected question
        session["score_history"][selected_question].append(score)
        session.modified = True

        # Debug output
        print("Score History in session:", session["score_history"])

        # Flatten all scores into a single list to calculate average
        all_scores = [s for scores in session["score_history"].values() for s in scores]

        print("All scores flattened:", all_scores)

        average_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
        print(f"Calculated average score: {average_score}")

        return jsonify({
            "transcribed_text": user_answer,
            "score": score,
            "average_score": average_score
        })
    return render_template("index.html",
                           questions=answers.keys(),
                           score=None,
                           average_score=0.0,
                           user_answer="")


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


@app.route('/upload_video', methods=['POST'])
@login_required
def upload_video():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request format. Expected JSON data.'}), 400

        video_data = data.get('video')
        question_key = data.get('question_key')  # Expect frontend to send question identifier
        
        if not video_data:
            return jsonify({'error': 'No video data provided.'}), 400
        
        if not video_data.startswith('data:video'):
            return jsonify({'error': 'Invalid video format. Ensure it is base64 encoded.'}), 400
        print(f"Received question_key: {question_key}")
        print(f"Available questions in answers: {list(answers.keys())}")
        
        if not question_key or question_key not in answers:
            return jsonify({'error': 'Invalid or missing question identifier.'}), 400

        # Decode base64 video
        video_base64 = video_data.split(",")[1]
        video_data_bytes = base64.b64decode(video_base64)

        # Save video file
        user_folder = os.path.join('static', 'uploads', current_user.username)
        os.makedirs(user_folder, exist_ok=True)
        filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.webm'
        filepath = os.path.join(user_folder, filename)

        with open(filepath, 'wb') as f:
            f.write(video_data_bytes)

        # Fix WebM duration if necessary (assume this function is defined)
        fixed_filepath = fix_webm_duration(filepath)

        # Extract audio and transcribe
        video_clip = mp.VideoFileClip(fixed_filepath)
        audio_filepath = fixed_filepath.replace('.webm', '.wav')
        video_clip.audio.write_audiofile(audio_filepath)

        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_filepath) as source:
            audio = recognizer.record(source)

        user_answer = recognizer.recognize_google(audio)
        print(f"Transcribed Text: {user_answer}")

        # Save transcribed answer in session
        session['last_transcribed_answer'] = user_answer
        session.modified = True

        # Calculate score
        expected_answer = answers[question_key]
        user_vec = get_embeddings(user_answer)
        expected_vec = get_embeddings(expected_answer)

        fscore = cosine_similarity(user_vec, expected_vec)[0][0] * 100

        score = round(float(fscore), 2)
        print(f"Calculated Score: {score}")

        # Store score in session history
        if "score_history" not in session:
            session["score_history"] = {}
        session["score_history"][question_key] = score
        session.modified = True

        # Calculate average score
        score_values = list(session["score_history"].values())
        average_score = round(sum(score_values) / len(score_values), 2) if score_values else 0.0

        return jsonify({
            'message': 'Video uploaded and processed successfully!',
            'score': score,
            'average_score': average_score,
            'transcribed_text': user_answer
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

@app.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    try:
        if "score_history" not in session or not session["score_history"]:
            return jsonify({'error': 'No scores available for submission.'}), 400

        average_score = sum(session["score_history"].values()) / len(session["score_history"])
        average_score = round(average_score, 2)
        
        student_name = current_user.username  # Fetch student's name

        # Save test result with student name and score
        new_result = TestResult(student_name=student_name, score=average_score, user_id=current_user.id)
        db.session.add(new_result)
        db.session.commit()

        return jsonify({'message': 'Test submitted successfully!', 'average_score': average_score}), 200

    except Exception as e:
        print(f"Error in submit_test: {str(e)}")
        return jsonify({'error': f'An error occurred while submitting the test: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

