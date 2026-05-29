from flask import Flask, render_template, jsonify, request, session
import os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cloudhero_secret_2024")

# ──────────────────────────────────────────────
# DATABASE SETUP — PostgreSQL on Render, SQLite locally
# ──────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # Render provides postgres:// but psycopg2 needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    import psycopg2
    import psycopg2.extras

    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    def placeholder():
        return "%s"

    def last_insert_id(cursor, table, pk="id"):
        return cursor.fetchone()[0]

    PG = True
else:
    import sqlite3
    DB = "cloudhero.db"

    def get_db():
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        return conn

    def placeholder():
        return "?"

    PG = False


def db_execute(conn, sql, params=()):
    """Run a statement, return cursor."""
    c = conn.cursor()
    c.execute(sql, params)
    return c


def db_fetchall(conn, sql, params=()):
    c = conn.cursor()
    c.execute(sql, params)
    if PG:
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]
    else:
        rows = c.fetchall()
        return [dict(r) for r in rows]


def db_fetchone(conn, sql, params=()):
    c = conn.cursor()
    c.execute(sql, params)
    if PG:
        row = c.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in c.description]
        return dict(zip(cols, row))
    else:
        row = c.fetchone()
        return dict(row) if row else None


def P(n=1):
    """Return n placeholders for the active DB."""
    ph = "%s" if PG else "?"
    return ", ".join([ph] * n)


def init_db():
    conn = get_db()
    c = conn.cursor()

    if PG:
        c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY,
            slug TEXT UNIQUE,
            title TEXT,
            parent_slug TEXT,
            order_num INTEGER
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id SERIAL PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            topic_slug TEXT,
            completed INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            last_seen TEXT,
            UNIQUE(user_id, topic_slug)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id SERIAL PRIMARY KEY,
            user_id TEXT DEFAULT 'default',
            topic_slug TEXT,
            question_id INTEGER,
            correct INTEGER,
            answered_at TEXT
        )""")
    else:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT,
            parent_slug TEXT,
            order_num INTEGER
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            topic_slug TEXT,
            completed INTEGER DEFAULT 0,
            score INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            last_seen TEXT,
            UNIQUE(user_id, topic_slug)
        );
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            topic_slug TEXT,
            question_id INTEGER,
            correct INTEGER,
            answered_at TEXT
        );
        """)
    conn.commit()

    conn.commit()

    # Insert topics
    topics = [
        ("what-is-cloud","What is Cloud?",None,1),
        ("cloud-history","History of Cloud",None,2),
        ("cloud-models","Cloud Service Models",None,3),
        ("cloud-types","Types of Cloud",None,4),
        ("cloud-providers","Major Cloud Providers",None,5),
        ("cloud-security","Cloud Security",None,6),
        ("cloud-security-principles","Security Principles","cloud-security",1),
        ("cloud-security-threats","Common Threats","cloud-security",2),
        ("cloud-security-tools","Security Tools","cloud-security",3),
        ("cloud-security-compliance","Compliance & Standards","cloud-security",4),
        ("cloud-networking","Cloud Networking",None,7),
        ("cloud-storage","Cloud Storage",None,8),
        ("cloud-devops","Cloud & DevOps",None,9),
        ("cloud-career","Career Roadmap",None,10),
    ]
    ph = P(4)
    if PG:
        for t in topics:
            c.execute(f"INSERT INTO topics(slug,title,parent_slug,order_num) VALUES({ph}) ON CONFLICT(slug) DO NOTHING", t)
    else:
        c.executemany(f"INSERT OR IGNORE INTO topics(slug,title,parent_slug,order_num) VALUES({ph})", topics)
    conn.commit()
    conn.close()

# ──────────────────────────────────────────────
# QUIZ DATA
# ──────────────────────────────────────────────
QUIZ_DATA = {
"what-is-cloud": [
  {"id":1,"q":"What does 'cloud computing' primarily refer to?","options":["Physical servers in your office","Delivery of computing services over the internet","Weather forecasting systems","Local area networks"],"ans":1},
  {"id":2,"q":"Which of these is NOT a core characteristic of cloud computing?","options":["On-demand self-service","Broad network access","Physical hardware ownership","Measured service"],"ans":2},
  {"id":3,"q":"The 'pay-as-you-go' model in cloud computing means:","options":["You pay a flat monthly fee","You pay only for resources you use","You prepay for a year","You get free services"],"ans":1},
  {"id":4,"q":"Which NIST characteristic describes the ability to scale resources up or down quickly?","options":["Broad network access","Resource pooling","Rapid elasticity","Measured service"],"ans":2},
  {"id":5,"q":"Cloud computing helps organizations by:","options":["Increasing capital expenditure","Reducing need for IT staff entirely","Converting CapEx to OpEx","Eliminating internet dependency"],"ans":2},
],
"cloud-history": [
  {"id":1,"q":"Who coined the term 'cloud computing' in its modern sense?","options":["Bill Gates","Eric Schmidt (Google)","Larry Ellison","Linus Torvalds"],"ans":1},
  {"id":2,"q":"Amazon Web Services (AWS) launched its first cloud service in:","options":["2000","2006","2010","2015"],"ans":1},
  {"id":3,"q":"The concept of 'utility computing' was first proposed in which decade?","options":["1950s","1970s","1990s","2000s"],"ans":0},
  {"id":4,"q":"Salesforce is often credited as a pioneer of:","options":["IaaS","PaaS","SaaS","FaaS"],"ans":2},
  {"id":5,"q":"Virtualization technology, key to cloud computing, was significantly advanced by:","options":["Google","VMware","Microsoft","Amazon"],"ans":1},
],
"cloud-models": [
  {"id":1,"q":"In IaaS, what does the cloud provider manage?","options":["Applications and runtime","Operating system and middleware","Physical infrastructure, networking, and virtualization","Only the database"],"ans":2},
  {"id":2,"q":"Which service model gives developers a platform to build and deploy applications without managing servers?","options":["IaaS","PaaS","SaaS","NaaS"],"ans":1},
  {"id":3,"q":"Gmail and Google Docs are examples of:","options":["IaaS","PaaS","SaaS","FaaS"],"ans":2},
  {"id":4,"q":"AWS EC2 is an example of:","options":["SaaS","PaaS","IaaS","DBaaS"],"ans":2},
  {"id":5,"q":"In the shared responsibility model of PaaS, who manages the application code?","options":["Cloud provider","The customer","Both equally","A third party"],"ans":1},
  {"id":6,"q":"Serverless computing falls under which category?","options":["IaaS","PaaS","FaaS/Serverless","SaaS"],"ans":2},
],
"cloud-types": [
  {"id":1,"q":"A Public Cloud is:","options":["Owned by a single organization","Shared infrastructure available to the general public","A combination of public and private","Located on-premises"],"ans":1},
  {"id":2,"q":"Which cloud type offers the highest level of control and security?","options":["Public Cloud","Community Cloud","Private Cloud","Hybrid Cloud"],"ans":2},
  {"id":3,"q":"A Hybrid Cloud combines:","options":["Two public clouds","Two private clouds","Public and private cloud","On-premises and SaaS only"],"ans":2},
  {"id":4,"q":"Which deployment model is best for organizations with strict regulatory requirements?","options":["Public Cloud","Multi-cloud","Private Cloud","Community Cloud"],"ans":2},
  {"id":5,"q":"Multi-cloud strategy means:","options":["Using one cloud provider for multiple services","Using multiple cloud providers","A hybrid of on-prem and cloud","Community shared cloud"],"ans":1},
],
"cloud-providers": [
  {"id":1,"q":"Which cloud provider has the largest market share globally?","options":["Microsoft Azure","Google Cloud","Amazon Web Services","IBM Cloud"],"ans":2},
  {"id":2,"q":"Microsoft Azure's AI and ML platform is called:","options":["SageMaker","Azure Machine Learning","Google AI Platform","Watson"],"ans":1},
  {"id":3,"q":"Google Cloud's container orchestration service is:","options":["EKS","AKS","GKE","Kubernetes Engine"],"ans":2},
  {"id":4,"q":"AWS's serverless compute service is:","options":["Azure Functions","Cloud Functions","AWS Lambda","App Engine"],"ans":2},
  {"id":5,"q":"Which provider is known for its 'Availability Zones' and 'Regions' terminology?","options":["Only AWS","Only Azure","Only GCP","All major providers use similar concepts"],"ans":3},
],
"cloud-security": [
  {"id":1,"q":"What is the CIA Triad in cloud security?","options":["Confidentiality, Integrity, Availability","Cloud, Infrastructure, Access","Control, Identity, Audit","Compliance, Intelligence, Assurance"],"ans":0},
  {"id":2,"q":"The shared responsibility model means:","options":["Provider handles all security","Customer handles all security","Security is divided between provider and customer","A third party handles security"],"ans":2},
  {"id":3,"q":"Which attack involves overloading a cloud service with traffic?","options":["SQL Injection","DDoS Attack","Man-in-the-Middle","Phishing"],"ans":1},
  {"id":4,"q":"Zero Trust security model assumes:","options":["Internal network is always safe","Never trust, always verify","Firewalls are sufficient","Users inside the network are trusted"],"ans":1},
  {"id":5,"q":"Data encryption at rest means:","options":["Encrypting data while it travels over the network","Encrypting data stored on disk","Encrypting data in use","No encryption needed"],"ans":1},
],
"cloud-security-principles": [
  {"id":1,"q":"Principle of Least Privilege means:","options":["Users get maximum access","Users get only the access they need","Admins have no restrictions","Public access to all resources"],"ans":1},
  {"id":2,"q":"Defense in Depth strategy involves:","options":["One strong firewall","Multiple layers of security controls","Only perimeter security","Trusting all internal traffic"],"ans":1},
  {"id":3,"q":"What is IAM in cloud security?","options":["Internet Access Management","Identity and Access Management","Infrastructure Asset Monitoring","Incident and Alert Management"],"ans":1},
  {"id":4,"q":"Multi-Factor Authentication (MFA) adds security by:","options":["Requiring a longer password","Requiring two or more verification methods","Blocking all external access","Encrypting login pages"],"ans":1},
  {"id":5,"q":"Security by Design means:","options":["Adding security after development","Security is embedded from the beginning","Buying third-party security tools","Relying only on cloud provider security"],"ans":1},
],
"cloud-security-threats": [
  {"id":1,"q":"A data breach in cloud occurs when:","options":["A server reboots","Unauthorized parties access sensitive data","A backup completes successfully","Network latency increases"],"ans":1},
  {"id":2,"q":"Ransomware in cloud environments typically:","options":["Speeds up services","Encrypts data and demands payment","Improves security","Reduces storage costs"],"ans":1},
  {"id":3,"q":"Insider threats come from:","options":["External hackers only","Employees or contractors with authorized access","Only former employees","Only contractors"],"ans":1},
  {"id":4,"q":"Account hijacking in cloud refers to:","options":["Deleting a cloud account","Unauthorized control of cloud accounts","Creating new accounts","Account billing issues"],"ans":1},
  {"id":5,"q":"A misconfigured S3 bucket is an example of:","options":["A DDoS attack","A malware infection","A cloud misconfiguration vulnerability","A phishing attack"],"ans":2},
],
"cloud-security-tools": [
  {"id":1,"q":"AWS Security Hub is used for:","options":["Storing files securely","Centralizing security findings across AWS services","Creating virtual machines","Managing DNS"],"ans":1},
  {"id":2,"q":"A SIEM tool in cloud security is used for:","options":["Storage management","Security Information and Event Management","Server Image Encryption Method","System Integration and Error Monitoring"],"ans":1},
  {"id":3,"q":"Cloudflare is primarily known for:","options":["IaaS hosting","DDoS protection and CDN services","Database management","Code deployment"],"ans":1},
  {"id":4,"q":"HashiCorp Vault is used for:","options":["Container orchestration","Secrets management and data protection","CI/CD pipelines","Load balancing"],"ans":1},
  {"id":5,"q":"Which tool is used for cloud infrastructure compliance scanning?","options":["Terraform","Prowler","Kubernetes","Jenkins"],"ans":1},
],
"cloud-security-compliance": [
  {"id":1,"q":"GDPR is a regulation focused on:","options":["Cloud infrastructure standards","Data privacy for EU citizens","Network security protocols","Software development practices"],"ans":1},
  {"id":2,"q":"SOC 2 compliance is important for:","options":["Physical security of buildings","Service organizations handling customer data","Network hardware vendors","Hardware manufacturers"],"ans":1},
  {"id":3,"q":"PCI DSS applies to organizations that:","options":["Handle payment card data","Use public cloud only","Develop mobile apps","Run data centers"],"ans":0},
  {"id":4,"q":"ISO 27001 is a standard for:","options":["Cloud cost management","Information security management systems","Software quality assurance","Network protocol design"],"ans":1},
  {"id":5,"q":"HIPAA compliance is required for organizations handling:","options":["Financial data","Healthcare information","Government secrets","Intellectual property"],"ans":1},
],
"cloud-networking": [
  {"id":1,"q":"A VPC (Virtual Private Cloud) provides:","options":["Physical servers","An isolated virtual network in the cloud","Free bandwidth","Automatic scaling"],"ans":1},
  {"id":2,"q":"A CDN (Content Delivery Network) improves:","options":["Database security","Content delivery speed by caching closer to users","Server processing power","Code compilation speed"],"ans":1},
  {"id":3,"q":"Load balancing in cloud distributes:","options":["Storage across devices","Incoming traffic across multiple servers","Security policies","Billing costs"],"ans":1},
  {"id":4,"q":"DNS in cloud networking translates:","options":["IP addresses to MAC addresses","Domain names to IP addresses","Ports to protocols","Data to encryption keys"],"ans":1},
  {"id":5,"q":"A subnet in a VPC is:","options":["A type of firewall","A subdivision of the VPC's IP address range","A cloud storage bucket","A type of virtual machine"],"ans":1},
],
"cloud-storage": [
  {"id":1,"q":"Object storage in cloud is best for:","options":["Running databases","Storing unstructured data like images and videos","Real-time data processing","Code execution"],"ans":1},
  {"id":2,"q":"AWS S3 stands for:","options":["Simple Storage Service","Secure Server System","Scalable Storage Solution","Standard Storage System"],"ans":0},
  {"id":3,"q":"Block storage is typically used for:","options":["Static website files","Databases and operating systems requiring low latency","Email archiving","Log file storage"],"ans":1},
  {"id":4,"q":"Data redundancy in cloud storage means:","options":["Deleting old data","Storing copies of data in multiple locations","Compressing data","Encrypting data"],"ans":1},
  {"id":5,"q":"Which cloud storage class is most cost-effective for infrequently accessed data?","options":["Standard","Frequent Access","Infrequent Access / Cold Storage","Premium"],"ans":2},
],
"cloud-devops": [
  {"id":1,"q":"CI/CD in DevOps stands for:","options":["Cloud Infrastructure / Cloud Deployment","Continuous Integration / Continuous Delivery","Code Inspection / Code Delivery","Container Integration / Container Deployment"],"ans":1},
  {"id":2,"q":"Infrastructure as Code (IaC) means:","options":["Writing apps in cloud","Managing infrastructure using code files","Coding inside cloud VMs","Using cloud-provided IDEs"],"ans":1},
  {"id":3,"q":"Kubernetes is primarily used for:","options":["Object storage management","Container orchestration","Network security","Database management"],"ans":1},
  {"id":4,"q":"Docker containers provide:","options":["Virtual machines","Lightweight, portable application environments","Cloud networking","Database replication"],"ans":1},
  {"id":5,"q":"Terraform is an example of:","options":["A cloud provider","An IaC tool","A container runtime","A monitoring tool"],"ans":1},
],
"cloud-career": [
  {"id":1,"q":"Which certification is considered entry-level for AWS?","options":["AWS Solutions Architect Professional","AWS Certified Cloud Practitioner","AWS DevOps Engineer","AWS Advanced Networking"],"ans":1},
  {"id":2,"q":"A Cloud Security Engineer primarily focuses on:","options":["Designing UI for cloud apps","Securing cloud infrastructure and applications","Managing cloud billing","Writing cloud marketing content"],"ans":1},
  {"id":3,"q":"Which skill is most important for a Cloud Architect?","options":["Graphic design","Designing scalable, cost-efficient cloud infrastructure","Social media management","Hardware assembly"],"ans":1},
  {"id":4,"q":"CompTIA Security+ is relevant for:","options":["Hardware engineering","Cloud security fundamentals","Database administration","UI/UX design"],"ans":1},
  {"id":5,"q":"A DevSecOps engineer integrates:","options":["Development and marketing","Security into development and operations pipelines","Hardware and software","Networking and storage only"],"ans":1},
],
}

# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/topic/<slug>")
def topic(slug):
    return render_template("topic.html", slug=slug)

@app.route("/api/topics")
def api_topics():
    conn = get_db()
    topics = db_fetchall(conn, "SELECT * FROM topics ORDER BY order_num")
    conn.close()
    return jsonify(topics)

@app.route("/api/progress")
def api_progress():
    uid = session.get("uid","default")
    conn = get_db()
    rows = db_fetchall(conn, f"SELECT * FROM progress WHERE user_id={P()}", (uid,))
    total_row = db_fetchone(conn, "SELECT COUNT(*) as cnt FROM topics")
    conn.close()
    total = total_row["cnt"]
    completed = sum(1 for r in rows if r["completed"])
    return jsonify({
        "total": total,
        "completed": completed,
        "percent": round(completed/total*100) if total else 0,
        "details": rows
    })

@app.route("/api/quiz/<slug>")
def api_quiz(slug):
    questions = QUIZ_DATA.get(slug, [])
    safe = [{"id":q["id"],"q":q["q"],"options":q["options"]} for q in questions]
    return jsonify(safe)

@app.route("/api/quiz/<slug>/answer", methods=["POST"])
def api_answer(slug):
    uid = session.get("uid","default")
    data = request.json
    qid = data.get("question_id")
    selected = data.get("selected")
    questions = QUIZ_DATA.get(slug, [])
    q = next((x for x in questions if x["id"]==qid), None)
    if not q:
        return jsonify({"error":"Question not found"}), 404
    correct = (selected == q["ans"])

    conn = get_db()
    ph = P(5)
    db_execute(conn, f"INSERT INTO quiz_results(user_id,topic_slug,question_id,correct,answered_at) VALUES({ph})",
               (uid, slug, qid, int(correct), datetime.now().isoformat()))
    conn.commit()

    if correct:
        total_q = len(questions)
        row = db_fetchone(conn,
            f"SELECT COUNT(DISTINCT question_id) as cnt FROM quiz_results WHERE user_id={P()} AND topic_slug={P()} AND correct=1",
            (uid, slug))
        correct_count = row["cnt"]
        score = round(correct_count / total_q * 100)
        completed = 1 if score >= 60 else 0
        if PG:
            db_execute(conn, f"""
                INSERT INTO progress(user_id,topic_slug,completed,score,attempts,last_seen)
                VALUES({P(6)})
                ON CONFLICT(user_id,topic_slug) DO UPDATE SET
                score=EXCLUDED.score, completed=EXCLUDED.completed,
                attempts=progress.attempts+1, last_seen=EXCLUDED.last_seen""",
                (uid, slug, completed, score, 1, datetime.now().isoformat()))
        else:
            db_execute(conn, f"""
                INSERT INTO progress(user_id,topic_slug,completed,score,attempts,last_seen)
                VALUES({P(6)})
                ON CONFLICT(user_id,topic_slug) DO UPDATE SET
                score=excluded.score, completed=excluded.completed,
                attempts=attempts+1, last_seen=excluded.last_seen""",
                (uid, slug, completed, score, 1, datetime.now().isoformat()))
        conn.commit()
    conn.close()

    import random
    msgs_correct = [
        "🎉 Excellent! You nailed it! Keep going, Cloud Hero!",
        "🚀 Correct! You're on fire! The cloud has no limits for you!",
        "⚡ Spot on! Every correct answer brings you closer to mastery!",
        "🌟 Perfect! You're building a rock-solid cloud foundation!",
        "💪 That's right! Cloud security bows to your knowledge!",
    ]
    msgs_wrong = [
        "❌ Not quite — but every mistake is a lesson. Review and try again!",
        "🔄 Incorrect, but don't give up! Great cloud engineers learn from every error.",
        "📚 Wrong answer, but that's okay! Review the material and come back stronger.",
        "💡 Not this time — but now you know what to study. You've got this!",
        "🛡️ Incorrect — but every Cloud Hero stumbles before they soar. Keep learning!",
    ]
    msg = random.choice(msgs_correct) if correct else random.choice(msgs_wrong)
    return jsonify({"correct": correct, "correct_index": q["ans"], "message": msg})

@app.route("/api/quiz/<slug>/progress")
def api_quiz_progress(slug):
    uid = session.get("uid","default")
    questions = QUIZ_DATA.get(slug, [])
    conn = get_db()
    rows = db_fetchall(conn,
        f"SELECT question_id, MAX(correct) as correct FROM quiz_results WHERE user_id={P()} AND topic_slug={P()} GROUP BY question_id",
        (uid, slug))
    conn.close()
    answered_map = {r["question_id"]: r["correct"] for r in rows}
    return jsonify({"total": len(questions), "answered": answered_map})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    uid = session.get("uid","default")
    conn = get_db()
    db_execute(conn, f"DELETE FROM progress WHERE user_id={P()}", (uid,))
    db_execute(conn, f"DELETE FROM quiz_results WHERE user_id={P()}", (uid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
