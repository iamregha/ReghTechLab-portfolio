"""
ReghTechLab — Database Seeder
==============================
Run once to populate the blog with real posts.
Usage: python seed.py

WARNING: This deletes all existing posts and creates fresh ones.
Do NOT run this in production after real users have posted.
"""
# WARNING: Only run locally or once on a fresh production DB.
# Running on a live DB with real user content will delete posts.

from app import app, db, User, Post
from slugify import slugify

POSTS = [
    {
        "title": "Why Fuel Station Networks Lose More to Reporting Than to Equipment Failure",
        "category": "Retail Operations",
        "excerpt": "The most expensive gap in downstream retail is not a broken pump. It is the three days between when a fault occurs and when a manager sees it on a report.",
        "cover_url": "https://images.unsplash.com/photo-1612630741022-b29ec14f5c76?w=1200&q=80",
        "content": """## The Invisible Cost

Every downstream retail operator knows the cost of a pump going down. You lose throughput. You lose revenue by the hour. The maintenance team mobilises. The fault gets fixed.

What almost nobody measures is the cost of what happens *before* the fault gets into a system.

A field technician resolves a submersible pump fault at 0700hrs on a Monday. The fix takes 90 minutes. The institutional knowledge of why that fault happened — the specific symptom pattern, the environmental factor, the component that keeps failing — lives entirely in that technician's head.

The maintenance report? Filed on Wednesday. Half the fields empty. No fault code. No component history.

## The Pattern Across Networks

I have observed this across multiple high-volume retail networks in Nigeria. The pattern is consistent:

- Field technicians diagnose and fix faults correctly and efficiently
- Data capture happens hours or days later, from memory
- Reports are designed for upward reporting, not operational learning
- The same fault recurs at different stations with zero knowledge transfer

Multiply that across a network of 50 stations and you are not just losing maintenance hours. You are losing the compounding value of operational experience that should be making your network more reliable every single month.

## What Closing This Gap Looks Like

The stations genuinely improving their uptime numbers are not doing it with expensive CMMS software. They are doing it by making data capture so simple that the technician in the field can complete it in the same time it takes to fill a paper form.

Three fields. One timestamp. One fault code from a dropdown.

That is enough to start building pattern recognition. That is enough to start predicting which stations will have the same fault next quarter. That is enough to order the right spare parts before the emergency.

The knowledge already exists in your network. The question is whether you are building systems that capture it — or watching it walk out the door every time an experienced technician moves on.

## The Engineering Principle

In reliability engineering, we talk about MTTR — Mean Time To Repair. Every maintenance team tracks it. But the metric that actually drives long-term reliability improvement is something quieter: the rate at which your organisation learns from each failure.

You cannot improve what you do not measure. And you cannot measure what you never captured.

The reporting gap is not a software problem. It is a workflow design problem. Software is just the tool that makes the right workflow effortless.""",
    },
    {
        "title": "ATG Systems in Nigerian Fuel Retail: What They Measure and Why Most Operators Miss the Value",
        "category": "Retail Operations",
        "excerpt": "Automatic Tank Gauging systems sit on thousands of forecourts across Nigeria, collecting data continuously. Most operators use them for one thing: compliance. They could be using them for five.",
        "cover_url": "https://images.unsplash.com/photo-1611273426858-450d8e3c9fce?w=1200&q=80",
        "content": """## What an ATG Actually Does

An Automatic Tank Gauging (ATG) system is a continuous monitoring installation inside your underground storage tanks. A probe sits in the tank and measures — typically every minute — the fuel level, water level, and product temperature.

That data goes to a console. The console generates reports. The operator uses those reports to verify deliveries and detect leaks.

That is the standard use case. Compliance and delivery verification.

But the ATG is also telling you things that most operators never look at.

## Five Signals Most Operators Ignore

**1. Consumption rate variance**

Your ATG knows exactly how much product left the tank in the last hour. Your dispensing pumps know how much was dispensed. If those numbers diverge consistently, you have a problem — not necessarily theft, but possibly a meter calibration issue, a leak in the line, or an underground tank fitting that is weeping.

**2. Temperature-adjusted volume**

Fuel expands and contracts with temperature. A delivery of 33,000 litres at 35°C is not the same as 33,000 litres at 25°C when you measure it at standard conditions. ATG systems with temperature probes can do this adjustment automatically. Most operators read the gross volume and wonder why their wet stock never quite reconciles.

**3. Water ingress trends**

Every UST accumulates some water — from condensation, from delivery contamination, from compromised fill caps. The ATG tracks this. A slow, steady increase in water level is normal. A sudden jump is a red flag that something changed. Operators who check this weekly catch problems before product quality is affected.

**4. Delivery verification**

When a truck delivers, the ATG records the level before and after. That delta is your actual received volume, temperature-compensated, to two decimal places. Compare that to the waybill. Discrepancies above your tolerance trigger a query — before the truck leaves the forecourt.

**5. Pump correlation**

Advanced ATG setups correlate tank depletion rate with individual pump meter readings. If tank depletion exceeds the sum of all pump transactions over any period, something is leaving the tank that is not being metered.

## The Gap Between Installed and Used

Nigeria has thousands of ATG-equipped stations. The majority use the console for one function: printing the daily inventory report for regulatory compliance.

The data that could tell them about slow leaks, meter drift, product loss patterns, and delivery fraud sits in the console's memory, never exported, never analysed, never acted on.

The hardware is already paid for. The sensors are already running. The data is already there.

The missing piece is a simple extraction and analysis layer — something that pulls that data nightly, flags anomalies, and puts a one-page summary in front of the manager every morning.

That is not a complex engineering problem. It is a workflow problem with a straightforward software solution.""",
    },
    {
        "title": "Building a Fault Log System with Python and Flask: A Field Engineer's Approach",
        "category": "Python & Backend",
        "excerpt": "How I built a simple maintenance logging tool that replaced a folder full of WhatsApp voice notes and Excel sheets — and what I learned about translating field problems into code.",
        "cover_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200&q=80",
        "content": """## The Problem I Was Actually Solving

Before I write a single line of code, I ask myself one question: what manual process is this replacing, and exactly where is the pain?

For this project, the pain was specific. Fault reports from field technicians were arriving as WhatsApp voice notes, hand-written job cards, and occasional Excel sheets with inconsistent column names. By the time a fault reached the maintenance manager's weekly review, the data was days old, partially reconstructed from memory, and nearly impossible to query.

I wanted to build the simplest possible thing that solved that specific problem. Not a full CMMS. Not a enterprise asset management system. A fault log — structured data capture at the point of work.

## The Data Model First

Before opening VS Code, I drew the entities on paper:
Station  ──< FaultLog
Equipment ──< FaultLog
Technician ──< FaultLog

A fault log belongs to one station, describes one piece of equipment, and is submitted by one technician. That is three foreign keys. Simple.

```python
class FaultLog(db.Model):
    __tablename__ = "fault_logs"

    id             = db.Column(db.Integer, primary_key=True)
    station_id     = db.Column(db.Integer, db.ForeignKey("stations.id"))
    equipment_type = db.Column(db.String(80), nullable=False)
    fault_code     = db.Column(db.String(40), default="")
    description    = db.Column(db.Text, nullable=False)
    resolution     = db.Column(db.Text, default="")
    downtime_hours = db.Column(db.Float, default=0.0)
    resolved       = db.Column(db.Boolean, default=False)
    logged_at      = db.Column(db.DateTime,
                               default=lambda: datetime.now(timezone.utc))
    technician_id  = db.Column(db.Integer, db.ForeignKey("users.id"))
```

The `downtime_hours` field is the most important one. It converts a maintenance event into a business metric. When you sum `downtime_hours` by station, by equipment type, by month — you start to see patterns that are invisible inside individual job cards.

## The API Endpoint

The technician in the field uses a mobile browser. The form is three required fields and three optional ones. Submitting takes 45 seconds.

```python
@app.route("/fault/new", methods=["GET", "POST"])
@login_required
def log_fault():
    if request.method == "POST":
        log = FaultLog(
            station_id     = request.form.get("station_id", type=int),
            equipment_type = request.form.get("equipment_type"),
            description    = request.form.get("description"),
            downtime_hours = request.form.get("downtime_hours",
                                              type=float, default=0),
            technician_id  = current_user.id,
        )
        db.session.add(log)
        db.session.commit()
        flash("Fault logged.", "success")
        return redirect(url_for("dashboard"))
    return render_template("fault/new.html", stations=stations)
```

## What This Taught Me

The most valuable lesson from building this was about scope. My first instinct was to build a dashboard with charts, trend analysis, export to PDF, email notifications, and role-based permissions.

I shipped none of that in version 1.

Version 1 was: submit a fault log, view the list of fault logs, mark one as resolved. Three routes. Two templates. One model.

Version 1 went into use within two weeks. The team used it. They asked for things. The things they actually asked for were not the things I had planned to build. The dashboard they wanted was simpler than what I imagined. The export format they needed was CSV, not PDF.

Build the smallest thing that solves the real problem. Use it. Let the actual users tell you what to build next.

That principle applies whether you are building a fault log system for a 20-station retail network or a production-grade SCADA integration for a refinery. Start small. Ship. Learn. Iterate.

## Running It

If you want to adapt this pattern for your own network:

```bash
git clone [repo-url]
cd fault-log
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
flask db upgrade
python app.py
```

The database schema is in `migrations/`. The models are in `app.py`. The templates are in `templates/`. Total codebase: under 400 lines.

That is the point. Maintainable, understandable, deployable by one engineer.""",
    },
]


def seed():
    with app.app_context():

        # ── Find or create admin user ──────────────────────
        admin = db.session.execute(
            db.select(User).filter_by(username="Abraham")
        ).scalar_one_or_none()

        if not admin:
            admin = User(
                username="Abraham",
                email="regha87@gmail.com",
                is_admin=True,
                bio=(
                    "COREN-certified Mechanical Engineer and Python developer. "
                    "6+ years in downstream oil & gas retail operations. "
                    "Building software that understands physical hardware."
                )
            )
            admin.set_password("Admin12345!")
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Admin user created: Abraham")
        else:
            print(f"✓ Admin user already exists: Abraham")

        # ── Delete existing seeded posts ───────────────────
        existing = db.session.execute(
            db.select(Post).filter_by(author_id=admin.id)
        ).scalars().all()

        for p in existing:
            db.session.delete(p)
        db.session.commit()
        print(f"✓ Cleared {len(existing)} existing posts")

        # ── Create posts ───────────────────────────────────
        for data in POSTS:
            slug = slugify(data["title"])

            post = Post(
                title     = data["title"],
                slug      = slug,
                category  = data["category"],
                excerpt   = data["excerpt"],
                content   = data["content"],
                cover_url = data["cover_url"],
                published = True,
                author_id = admin.id,
            )
            db.session.add(post)
            print(f"✓ Post created: {data['title'][:55]}...")

        db.session.commit()
        print("\n✅  Seeding complete.")
        print("    Login: abraham / change-this-password-immediately")
        print("    Change that password immediately after first login.")


if __name__ == "__main__":
    seed()