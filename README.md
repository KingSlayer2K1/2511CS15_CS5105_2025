🎉 Student Grouping App

Once upon a time in IIT Patna, students had to form groups… but chaos ruled ⚡
Some branches had too many students, others too few.
Professors wanted order, students wanted fairness, and Excel sheets wanted mercy.

So this app was born. 💡

📖 The Story

You upload your class list (Excel/CSV).

The app listens patiently… 🗂️

Then, with its magical Streamlit powers, it offers you 3 ways to group:

🏫 Full Branchwise → Every branch stays together, roll numbers shown.

🔄 Branchwise Mixed → A true round-robin mix of branches, shown as branch counts.

⚖️ Branchwise Uniform → Balanced groups, but the branch with more students always shines on top.

And just like Instagram ✨, everything looks clean, card-like, and scrollable.

🚀 How to Run

Clone this repo:

git clone https://github.com/your-username/student-grouping-app.git
cd student-grouping-app


Create a virtual environment:

python -m venv venv


Activate it:

Windows (PowerShell)

venv\Scripts\activate


Linux/Mac

source venv/bin/activate


Install requirements:

pip install -r requirements.txt


Run the app:

python -m streamlit run instagram_style_groups.py


Open browser → http://localhost:8501 and enjoy 🎉

📂 Files

groups.py → the app.

requirements.txt → what the app eats.

.gitignore → what Git should forget.

README.md → this story 📖

💾 Output

Download groups as CSV (per group).

Or grab them all at once as a ZIP.
