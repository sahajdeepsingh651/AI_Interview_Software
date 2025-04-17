from flask import Flask, render_template, request,session ,redirect
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# Load Word2Vec model
print("Loading Word2Vec model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")


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

def get_avg_vector(text):
    # Generate embeddings for the text (user answer and model answer)
    embedding = model.encode(text)
    return np.array(embedding)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        session["score_history"] = {}
        session.modified = True

    score = None
    average_score = 0.0
    selected_question = list(answers.keys())[0]
    user_answer = ""

    if request.method == "POST":
        selected_question = request.form["question"]
        user_answer = request.form["answer"]

        expected_answer = answers[selected_question]
        user_vec = get_avg_vector(user_answer)
        expected_vec = get_avg_vector(expected_answer)

        score = cosine_similarity([user_vec], [expected_vec])[0][0] * 100
        score = round(score, 2)

        # Store score per question
        if "score_history" not in session:
            session["score_history"] = {}

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


@app.route("/reset")
def reset():
    session["score_history"] = {}
    session.modified = True
    return redirect("/")

if __name__ == "__main__": 
    app.run()