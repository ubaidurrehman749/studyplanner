import base64
import csv
import hashlib
import html as htmllib
import io
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(page_title="Study Planner · Study Sparks AI", page_icon="✦", layout="wide")

OWNER_NAME = "Ubaid ur Rehman"
TIMEZONE = "Asia/Karachi"   # apni timezone yahan change kar sakte hain

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DIFF = {1: "Easy", 2: "Fairly easy", 3: "Medium", 4: "Hard", 5: "Very hard"}
PALETTE = ["#0E9F8E", "#FF7A59", "#3B82F6", "#F5B301", "#8B5CF6", "#EC4899", "#14B8A6", "#64748B"]


def today():
    return datetime.now(ZoneInfo(TIMEZONE)).date()


# ---------- Logo ----------
def logo_tag():
    mimes = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".svg": "image/svg+xml"}
    for ext, mime in mimes.items():
        p = Path(__file__).parent / f"logo{ext}"
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f'<img class="logo" src="data:{mime};base64,{b64}" alt="Study Sparks AI logo">'
    return '<span class="spark">✦</span>'


# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.2rem; max-width: 1100px; }
.topbar { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;
          padding-bottom:14px; border-bottom:1px solid #D5EBE7; }
.brand { display:flex; align-items:center; gap:12px; font-family:'Bricolage Grotesque',sans-serif;
         font-weight:800; font-size:1.45rem; color:#12304A; }
.brand .logo { height:46px; width:46px; object-fit:contain; border-radius:10px; }
.brand .spark { color:#FF7A59; font-size:1.6rem; }
.brand b { color:#0E9F8E; }
.owner { background:#12304A; color:#F0FAF8; padding:8px 16px; border-radius:999px; font-weight:500; font-size:.95rem; }
.owner b { color:#FF7A59; }
.hero h1 { font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:2.4rem;
           line-height:1.1; color:#12304A; margin:1.2rem 0 .3rem; letter-spacing:-.02em; }
.hero p { color:#4A6572; font-size:1.1rem; margin-bottom:.8rem; }

.sub { background:#fff; border:1px solid #D5EBE7; border-left:7px solid #0E9F8E; border-radius:14px;
       padding:12px 16px; margin-bottom:10px; box-shadow:0 14px 26px -22px rgba(18,48,74,.5); }
.sub .n { font-weight:700; color:#12304A; font-size:1.05rem; }
.sub .d { color:#4A6572; font-size:.92rem; }
.sub .left { float:right; background:rgba(255,122,89,.14); color:#E0562F; font-weight:700;
             padding:3px 12px; border-radius:999px; font-size:.88rem; }

.day { display:flex; gap:14px; align-items:flex-start; padding:10px 0; border-bottom:1px dashed #D5EBE7; }
.dlabel { min-width:62px; text-align:center; background:#12304A; color:#F0FAF8; border-radius:12px;
          padding:6px 8px; font-size:.82rem; line-height:1.3; }
.dlabel b { color:#FF7A59; font-size:1rem; }
.pills { display:flex; flex-wrap:wrap; gap:8px; }
.pill { background:#fff; border:1px solid #D5EBE7; border-radius:10px; padding:6px 12px; font-size:.9rem; color:#12304A; }
.pill.done { opacity:.5; text-decoration:line-through; }
.pill.exam { background:#FF7A59; color:#fff; border-color:#FF7A59; font-weight:700; }

div.stButton > button, div.stDownloadButton > button { border-radius:12px; font-weight:700; padding:.6rem 1rem; }
div.stButton > button[kind="primary"], div.stDownloadButton > button, div.stFormSubmitButton > button {
    background:#0E9F8E; color:#fff; border:0; }
div.stButton > button[kind="primary"]:hover, div.stDownloadButton > button:hover,
div.stFormSubmitButton > button:hover { background:#0B7F72; color:#fff; }
[data-testid="stMetricValue"] { color:#0E9F8E; font-family:'Bricolage Grotesque',sans-serif; }
.stTabs [data-baseweb="tab"] { font-weight:700; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="topbar">
  <div class="brand">{logo_tag()}<span>Study Sparks <b>AI</b></span></div>
  <div class="owner">Created by <b>{OWNER_NAME}</b></div>
</div>
<div class="hero">
  <h1>Study Planner</h1>
  <p>Add your subjects and exam dates. Get a day-by-day plan, tick off sessions and track your progress.</p>
</div>
""", unsafe_allow_html=True)

# ---------- State ----------
ss = st.session_state
ss.setdefault("subjects", [])
ss.setdefault("done", set())
ss.setdefault("msg", None)
ss.setdefault("daily_hours", 3.0)
ss.setdefault("session_min", 45)
ss.setdefault("start_time", time(17, 0))
ss.setdefault("start_date", today())
ss.setdefault("study_days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"])


def color_of(name):
    for i, s in enumerate(ss.subjects):
        if s["name"] == name:
            return PALETTE[i % len(PALETTE)]
    return PALETTE[0]


def esc(t):
    return htmllib.escape(str(t))


def clear_checkbox_keys():
    for k in [k for k in ss.keys() if k.startswith("cb_")]:
        del ss[k]


def remove_subject(i):
    if 0 <= i < len(ss.subjects):
        ss.subjects.pop(i)


def toggle(bid):
    if ss.get(f"cb_{bid}"):
        ss.done.add(bid)
    else:
        ss.done.discard(bid)


def reset_progress():
    ss.done = set()
    clear_checkbox_keys()


# ---------- Schedule engine ----------
def build_schedule(subjects, start, daily_hours, session_min, start_t, days_ok):
    blocks = []
    if not subjects or not days_ok:
        return blocks
    end = min(max(s["exam"] for s in subjects), start + timedelta(days=180))
    slots_per_day = max(1, int(daily_hours * 60 // session_min))
    assigned = {s["name"]: 0 for s in subjects}

    d = start
    while d < end:
        if DAY_NAMES[d.weekday()] in days_ok:
            active = [s for s in subjects if s["exam"] > d]
            if active:
                def priority(s):
                    left = (s["exam"] - d).days
                    return s["difficulty"] * (1 + 6 / left) / (1 + assigned[s["name"]])

                counts, order = {}, []
                for _ in range(slots_per_day):
                    s = max(active, key=priority)
                    assigned[s["name"]] += 1
                    if s["name"] not in counts:
                        order.append(s["name"])
                    counts[s["name"]] = counts.get(s["name"], 0) + 1

                cur = datetime.combine(d, start_t)
                exams = {s["name"]: s["exam"] for s in active}
                for idx, name in enumerate(order):
                    mins = counts[name] * session_min
                    blocks.append({
                        "id": f"{d.isoformat()}|{name}|{idx}", "date": d, "subject": name,
                        "minutes": mins, "start": cur, "end": cur + timedelta(minutes=mins),
                        "final": (exams[name] - d).days == 1,
                    })
                    cur = cur + timedelta(minutes=mins + 10)  # 10 min break
        d += timedelta(days=1)
    return blocks


def make_ics(blocks, subjects):
    def e(t):
        return str(t).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    stamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Study Sparks AI//Study Planner//EN", "CALSCALE:GREGORIAN"]
    for b in blocks:
        uid = hashlib.md5(b["id"].encode()).hexdigest()
        L += ["BEGIN:VEVENT", f"UID:{uid}@studysparks", f"DTSTAMP:{stamp}",
              f"DTSTART:{b['start'].strftime('%Y%m%dT%H%M%S')}", f"DTEND:{b['end'].strftime('%Y%m%dT%H%M%S')}",
              f"SUMMARY:{e('Study: ' + b['subject'] + (' (final revision)' if b['final'] else ''))}", "END:VEVENT"]
    for s in subjects:
        uid = hashlib.md5(("exam" + s["name"]).encode()).hexdigest()
        L += ["BEGIN:VEVENT", f"UID:{uid}@studysparks", f"DTSTAMP:{stamp}",
              f"DTSTART;VALUE=DATE:{s['exam'].strftime('%Y%m%d')}",
              f"DTEND;VALUE=DATE:{(s['exam'] + timedelta(days=1)).strftime('%Y%m%d')}",
              f"SUMMARY:{e('EXAM: ' + s['name'])}", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(L)


def plan_json():
    return json.dumps({
        "subjects": [{"name": s["name"], "exam": s["exam"].isoformat(), "difficulty": s["difficulty"]}
                     for s in ss.subjects],
        "settings": {"daily_hours": ss.daily_hours, "session_min": ss.session_min,
                     "start_time": ss.start_time.strftime("%H:%M"), "start_date": ss.start_date.isoformat(),
                     "study_days": ss.study_days},
        "done": sorted(ss.done),
    }, indent=2)


def load_plan():
    f = ss.get("plan_upload")
    if not f:
        return
    try:
        data = json.loads(f.getvalue().decode("utf-8"))
        subjects = [{"name": s["name"], "exam": date.fromisoformat(s["exam"]), "difficulty": int(s["difficulty"])}
                    for s in data["subjects"]]
        cfg = data.get("settings", {})
        ss.subjects = subjects
        ss.daily_hours = float(cfg.get("daily_hours", 3.0))
        ss.session_min = int(cfg.get("session_min", 45))
        h, m = str(cfg.get("start_time", "17:00")).split(":")
        ss.start_time = time(int(h), int(m))
        ss.start_date = date.fromisoformat(cfg.get("start_date", today().isoformat()))
        ss.study_days = [d for d in cfg.get("study_days", DAY_NAMES) if d in DAY_NAMES]
        ss.done = set(data.get("done", []))
        clear_checkbox_keys()
        ss.msg = ("success", "Plan loaded.")
    except Exception as e:
        ss.msg = ("error", f"Could not load the plan file: {e}")


tab_setup, tab_today, tab_plan, tab_progress = st.tabs(
    ["① Setup", "② Today", "③ Full plan", "④ Progress & export"])

# ======================= SETUP =======================
with tab_setup:
    st.subheader("Your subjects")
    with st.form("add_subject", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1.4, 1.6])
        name = c1.text_input("Subject name", placeholder="e.g. Chemistry")
        exam = c2.date_input("Exam date", value=today() + timedelta(days=14), min_value=today())
        diff = c3.select_slider("Difficulty", options=[1, 2, 3, 4, 5], value=3, format_func=lambda x: DIFF[x])
        if st.form_submit_button("Add subject", use_container_width=True):
            nm = name.strip()
            if not nm:
                st.warning("Write the subject name first.")
            elif any(s["name"].lower() == nm.lower() for s in ss.subjects):
                st.warning("This subject is already in your list.")
            else:
                ss.subjects.append({"name": nm, "exam": exam, "difficulty": diff})
                st.rerun()

    if not ss.subjects:
        st.info("No subjects yet. Add your first subject above.")
    for i, s in enumerate(ss.subjects):
        left = (s["exam"] - today()).days
        tag = f"{left} days left" if left > 0 else ("Exam today" if left == 0 else "Exam passed")
        r1, r2 = st.columns([5, 1])
        r1.markdown(
            f'<div class="sub" style="border-left-color:{PALETTE[i % len(PALETTE)]}">'
            f'<span class="left">{tag}</span><div class="n">{esc(s["name"])}</div>'
            f'<div class="d">Exam on {s["exam"].strftime("%a, %d %b %Y")} | Difficulty: {DIFF[s["difficulty"]]}</div></div>',
            unsafe_allow_html=True)
        r2.button("Remove", key=f"rm_{i}", on_click=remove_subject, args=(i,), use_container_width=True)

    st.subheader("Study settings")
    a, b = st.columns(2)
    a.slider("Study hours per day", 0.5, 12.0, step=0.5, key="daily_hours")
    b.selectbox("Session length (minutes)", [25, 30, 45, 60, 90], key="session_min")
    c, d = st.columns(2)
    c.time_input("Daily start time", key="start_time")
    d.date_input("Plan starts on", key="start_date")
    st.multiselect("Days you can study", DAY_NAMES, key="study_days")
    summary_slot = st.empty()

blocks = build_schedule(ss.subjects, ss.start_date, ss.daily_hours, ss.session_min, ss.start_time, ss.study_days)
block_ids = {b["id"] for b in blocks}
done_ids = ss.done & block_ids
total_min = sum(b["minutes"] for b in blocks)

if blocks:
    summary_slot.success(f"Plan ready: {len(blocks)} study blocks, about {total_min / 60:.1f} hours in total. "
                         f"Open the **Today** tab to begin.")
elif ss.subjects:
    summary_slot.warning("No study blocks could be created. Check your start date, study days and exam dates.")

# ======================= TODAY =======================
with tab_today:
    t = today()
    if not ss.subjects:
        st.info("Add subjects in the **Setup** tab first.")
    else:
        upcoming = sorted([s for s in ss.subjects if s["exam"] >= t], key=lambda s: s["exam"])[:3]
        if upcoming:
            cols = st.columns(len(upcoming))
            for col, s in zip(cols, upcoming):
                left = (s["exam"] - t).days
                col.metric(s["name"], f"{left} days" if left else "Today", s["exam"].strftime("%d %b"),
                           delta_color="off")

        for s in ss.subjects:
            if s["exam"] == t:
                st.error(f"Exam day: {s['name']}. Stay calm and do your best.")

        todays = [b for b in blocks if b["date"] == t]
        if t < ss.start_date:
            st.info(f"Your plan starts on {ss.start_date.strftime('%A, %d %b')}.")
        elif todays:
            planned = sum(b["minutes"] for b in todays)
            finished = sum(b["minutes"] for b in todays if b["id"] in ss.done)
            st.markdown(f"### Today's plan ({t.strftime('%A, %d %b')})")
            st.progress(finished / planned if planned else 0.0)
            st.caption(f"{finished} of {planned} minutes completed")
            for b in todays:
                with st.container(border=True):
                    label = (f"{b['subject']}: {b['start']:%H:%M} to {b['end']:%H:%M} ({b['minutes']} min)"
                             + ("  | Final revision" if b["final"] else ""))
                    st.checkbox(label, value=b["id"] in ss.done, key=f"cb_{b['id']}",
                                on_change=toggle, args=(b["id"],))
            if finished == planned:
                st.success("All of today's sessions are done. Great work!")
        else:
            nxt = next((b for b in blocks if b["date"] > t), None)
            msg = "No study session is planned for today. Take a rest."
            if nxt:
                msg += f" Next session: {nxt['date'].strftime('%A, %d %b')} at {nxt['start']:%H:%M} ({nxt['subject']})."
            st.info(msg)

# ======================= FULL PLAN =======================
with tab_plan:
    if not blocks:
        st.info("Your plan will appear here after you add subjects.")
    else:
        names = [s["name"] for s in ss.subjects]
        pick = st.multiselect("Show subjects", names, default=names)
        shown = [b for b in blocks if b["subject"] in pick]
        exams = [s for s in ss.subjects if s["name"] in pick]
        days = sorted({b["date"] for b in shown} | {s["exam"] for s in exams if s["exam"] >= ss.start_date})

        weeks = {}
        for d in days:
            weeks.setdefault(d - timedelta(days=d.weekday()), []).append(d)

        for mon, wdays in sorted(weeks.items()):
            sun = mon + timedelta(days=6)
            hrs = sum(b["minutes"] for b in shown if mon <= b["date"] <= sun) / 60
            is_now = mon <= today() <= sun
            with st.expander(f"Week of {mon.strftime('%d %b')} to {sun.strftime('%d %b')} | {hrs:.1f} h",
                             expanded=is_now or mon == min(weeks)):
                for d in wdays:
                    pills = ""
                    for b in [x for x in shown if x["date"] == d]:
                        cls = "pill done" if b["id"] in ss.done else "pill"
                        tick = "✓ " if b["id"] in ss.done else ""
                        fin = " (final revision)" if b["final"] else ""
                        pills += (f'<span class="{cls}" style="border-left:5px solid {color_of(b["subject"])}">'
                                  f'{tick}<b>{esc(b["subject"])}</b> {b["start"]:%H:%M}-{b["end"]:%H:%M} '
                                  f'({b["minutes"]} min){fin}</span>')
                    for s in exams:
                        if s["exam"] == d:
                            pills += f'<span class="pill exam">Exam: {esc(s["name"])}</span>'
                    st.markdown(f'<div class="day"><div class="dlabel">{d.strftime("%a")}<br>'
                                f'<b>{d.strftime("%d %b")}</b></div><div class="pills">{pills}</div></div>',
                                unsafe_allow_html=True)

# ======================= PROGRESS & EXPORT =======================
with tab_progress:
    if not blocks:
        st.info("Your progress will appear here after you add subjects.")
    else:
        done_min = sum(b["minutes"] for b in blocks if b["id"] in done_ids)
        pct = round(done_min / total_min * 100) if total_min else 0
        nxt_exam = min((s for s in ss.subjects if s["exam"] >= today()), key=lambda s: s["exam"], default=None)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Planned", f"{total_min / 60:.1f} h")
        m2.metric("Completed", f"{done_min / 60:.1f} h")
        m3.metric("Progress", f"{pct}%")
        m4.metric("Next exam", f"{(nxt_exam['exam'] - today()).days} days" if nxt_exam else "None")
        st.progress(pct / 100)

        st.markdown("#### By subject")
        for s in ss.subjects:
            plan_m = sum(b["minutes"] for b in blocks if b["subject"] == s["name"])
            got_m = sum(b["minutes"] for b in blocks if b["subject"] == s["name"] and b["id"] in done_ids)
            st.markdown(f"**{esc(s['name'])}**: {got_m} of {plan_m} minutes")
            st.progress(got_m / plan_m if plan_m else 0.0)
        st.button("Reset progress", on_click=reset_progress)

    st.markdown("#### Export and backup")
    if blocks:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Date", "Day", "Start", "End", "Subject", "Minutes", "Type", "Done"])
        for b in blocks:
            w.writerow([b["date"].isoformat(), b["date"].strftime("%A"), f"{b['start']:%H:%M}", f"{b['end']:%H:%M}",
                        b["subject"], b["minutes"], "Final revision" if b["final"] else "Study",
                        "Yes" if b["id"] in ss.done else "No"])
        e1, e2 = st.columns(2)
        e1.download_button("Download CSV", buf.getvalue(), file_name="study-plan.csv", mime="text/csv",
                           use_container_width=True)
        e2.download_button("Download calendar (.ics)", make_ics(blocks, ss.subjects),
                           file_name="study-plan.ics", mime="text/calendar", use_container_width=True)
        st.caption("The .ics file opens in Google Calendar, Apple Calendar and Outlook.")

    st.download_button("Save my plan (.json)", plan_json(), file_name="my-study-plan.json",
                       mime="application/json", use_container_width=True)
    st.file_uploader("Load a saved plan", type=["json"], key="plan_upload", on_change=load_plan)
    st.caption("This app does not keep your data after you close the page. Save your plan file and load it next time.")
    if ss.msg:
        getattr(st, ss.msg[0])(ss.msg[1])
        ss.msg = None

st.markdown(f"<hr><center style='color:#4A6572'>© Study Sparks AI · Created by {OWNER_NAME}</center>",
            unsafe_allow_html=True)
