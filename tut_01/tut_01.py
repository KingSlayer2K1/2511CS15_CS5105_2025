# instagram_style_groups.py
import streamlit as st
import pandas as pd
import re
import io, zipfile
from collections import defaultdict, deque

# ---------- Page config ----------
st.set_page_config(page_title="Groupify — Insta Style", page_icon="📸", layout="wide")

# ---------- Minimal Instagram-like CSS ----------
st.markdown(
    """
    <style>
    .card {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.45);
        margin-bottom: 18px;
    }
    .card h2 { margin: 0 0 8px 0; }
    .centered {
        max-width: 980px;
        margin-left: auto;
        margin-right: auto;
    }
    .muted { color: #9aa3ad; }
    .small { font-size: 0.95rem; color: #bfc7cc; }
    .big-emoji { font-size: 1.6rem; margin-right: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
def extract_branch(roll: str) -> str:
    s = str(roll).strip().upper()
    m = re.search(r"[A-Z]{2,3}", s)
    return m.group() if m else "NA"

def build_branch_map(rolls):
    d = defaultdict(list)
    for r in rolls:
        d[extract_branch(r)].append(r)
    # sort branches by name for consistent output
    return {b: sorted(lst) for b, lst in sorted(d.items())}

def mixed_counts_round_robin(branch_map, k):
    """
    True round-robin assignment but only returns counts per branch per group.
    Cycle through branches and groups assigning one student at a time.
    """
    queues = {b: deque(lst) for b, lst in branch_map.items()}
    branches = list(queues.keys())
    groups = [defaultdict(int) for _ in range(k)]
    g = 0
    idx_b = 0
    # continue until all queues empty
    while any(queues[b] for b in branches):
        bname = branches[idx_b]
        if queues[bname]:
            _ = queues[bname].popleft()
            groups[g][bname] += 1
            g = (g + 1) % k
        idx_b = (idx_b + 1) % len(branches)
    return groups

def uniform_counts_sorted(branch_map, k):
    """
    Distribute each branch's students across groups proportionally.
    Branches processed in descending order (largest first) so max branch
    shows up higher in group tables.
    Returns list of dicts (per group) branch->count.
    """
    groups = [defaultdict(int) for _ in range(k)]
    # sort branches by descending size
    sorted_branches = sorted(branch_map.items(), key=lambda x: len(x[1]), reverse=True)
    for branch, students in sorted_branches:
        n = len(students)
        base = n // k
        rem = n % k
        idx = 0
        for g in range(k):
            take = base + (1 if g < rem else 0)  # distribute remainders to earlier groups
            if take:
                groups[g][branch] += take
                idx += take
    return groups

def df_from_counts_dict(d: dict):
    """Return DataFrame with Branch and Count, sorted by Count desc."""
    items = list(d.items())
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    return pd.DataFrame(items_sorted, columns=["Branch", "Count"])

def make_zip_bytes(pairs):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, df in pairs:
            zf.writestr(name, df.to_csv(index=False).encode("utf-8"))
    return buf.getvalue()

# ---------- Session controls ----------
if "processed" not in st.session_state:
    st.session_state.processed = False

# ---------- Layout: centered column like an IG feed ----------
with st.container():
    st.markdown('<div class="centered">', unsafe_allow_html=True)

    # Upload / instruction card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("<h2>📂 Upload your roster</h2>", unsafe_allow_html=True)
        st.markdown(
            "<div class='small muted'>Drag & drop an Excel file (.xlsx) that contains a column named <b>Roll</b> (e.g. 24CS001).</div>",
            unsafe_allow_html=True,
        )
        st.write("")  # breathe
        uploaded_file = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")
    with col2:
        st.markdown("<h2 style='text-align:right'>⚙️ Options</h2>", unsafe_allow_html=True)
        st.markdown("<div class='small muted' style='text-align:right'>Pick how many groups and press Create.</div>", unsafe_allow_html=True)
        num_groups = st.number_input("Groups", min_value=1, value=3, step=1)
    st.markdown("</div>", unsafe_allow_html=True)

    # Controls card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3 class='small'><span class='big-emoji'>📊</span>Grouping Method</h3>", unsafe_allow_html=True)
    method = st.radio("", options=["Full Branchwise", "Branchwise Mixed", "Branchwise Uniform"], horizontal=False)
    left, right = st.columns([1,1])
    with left:
        if st.button("Create Groups"):
            st.session_state.processed = True
    with right:
        if st.button("Reset"):
            st.session_state.processed = False
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Results area (only after Create)
    if uploaded_file and st.session_state.processed:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

        if "Roll" not in df.columns:
            st.error("Upload must contain a column named 'Roll'.")
            st.stop()

        rolls = df["Roll"].dropna().astype(str).tolist()
        if not rolls:
            st.error("No roll numbers found in 'Roll' column.")
            st.stop()

        branch_map = build_branch_map(rolls)
        total = len(rolls)
        stu_per_group = total // int(num_groups)

        # Small summary card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h3>📌 Summary</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='small muted'>Total students: <b>{total}</b> • Groups: <b>{num_groups}</b> • Students/group (floor): <b>{stu_per_group}</b></div>", unsafe_allow_html=True)
        # show branch totals
        branch_totals = pd.DataFrame([(b, len(lst)) for b, lst in branch_map.items()], columns=["Branch","Total"])
        branch_totals = branch_totals.sort_values("Total", ascending=False).reset_index(drop=True)
        st.markdown("<div style='margin-top:10px'><b>Students per branch:</b></div>", unsafe_allow_html=True)
        st.dataframe(branch_totals, use_container_width=True, height=220)
        st.markdown("</div>", unsafe_allow_html=True)

        # Mode-specific displays
        if method == "Full Branchwise":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h3>🗂️ Full Branchwise — student lists</h3>", unsafe_allow_html=True)
            files = []
            for b, lst in branch_map.items():
                dfb = pd.DataFrame({"Roll": lst})
                st.markdown(f"**{b}** — {len(dfb)} students")
                st.dataframe(dfb, use_container_width=True, height=180)
                csv_bytes = dfb.to_csv(index=False).encode("utf-8")
                st.download_button(f"⬇ Download {b}.csv", data=csv_bytes, file_name=f"{b}.csv", mime="text/csv")
                files.append((f"{b}.csv", dfb))
                st.write("---")
            st.download_button("⬇ Download ALL branches (ZIP)", data=make_zip_bytes(files), file_name="branches_all.zip", mime="application/zip")
            st.markdown("</div>", unsafe_allow_html=True)

        elif method == "Branchwise Mixed":
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h3>🔁 Branchwise Mixed — counts (round-robin)</h3>", unsafe_allow_html=True)
            groups = mixed_counts_round_robin(branch_map, int(num_groups))
            files = []
            for i, g in enumerate(groups, 1):
                dfc = df_from_counts_dict(g)
                st.markdown(f"**Group {i}** — {dfc['Count'].sum()} students")
                # ensure largest branches appear first
                st.dataframe(dfc, use_container_width=True, height=180)
                csvb = dfc.to_csv(index=False).encode("utf-8")
                st.download_button(f"⬇ Download Group{i}.csv", data=csvb, file_name=f"Group{i}.csv", mime="text/csv")
                files.append((f"Group{i}.csv", dfc))
                st.write("---")
            st.download_button("⬇ Download ALL mixed groups (ZIP)", data=make_zip_bytes(files), file_name="mixed_groups.zip", mime="application/zip")
            st.markdown("</div>", unsafe_allow_html=True)

        else:  # Branchwise Uniform
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h3>📌 Branchwise Uniform — counts (largest branch prioritized)</h3>", unsafe_allow_html=True)
            groups = uniform_counts_sorted(branch_map, int(num_groups))
            files = []
            for i, g in enumerate(groups, 1):
                # produce df sorted so largest branch appears on top
                dfc = df_from_counts_dict(g)
                st.markdown(f"**Group {i}** — {dfc['Count'].sum()} students")
                st.dataframe(dfc, use_container_width=True, height=180)
                csvb = dfc.to_csv(index=False).encode("utf-8")
                st.download_button(f"⬇ Download Group{i}.csv", data=csvb, file_name=f"Group{i}.csv", mime="text/csv")
                files.append((f"Group{i}.csv", dfc))
                st.write("---")
            st.download_button("⬇ Download ALL uniform groups (ZIP)", data=make_zip_bytes(files), file_name="uniform_groups.zip", mime="application/zip")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        # show demo card when no upload or not processed
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h3>✨ Demo preview</h3>", unsafe_allow_html=True)
        st.markdown("<div class='small muted'>Upload an .xlsx file with a column named <b>Roll</b> and press Create Groups to see real output.</div>", unsafe_allow_html=True)
        demo = ["24CS001","24CS002","24EE001","24ME002","24CS003","24EE004","24MM005","24CS006"]
        st.dataframe(pd.DataFrame({"Roll": demo}), use_container_width=True, height=140)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close centered div
