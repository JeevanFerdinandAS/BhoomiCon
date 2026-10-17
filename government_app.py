
import os
import hmac
import pandas as pd
import streamlit as st

from Landlink_db import get_all_land, update_status
from bhoomicon_features import (
    DOCUMENT_STATUSES,
    find_matching_land,
    get_document_records,
    update_document_status,
)

# =========================================================
# 1. PAGE CONFIGURATION — KEEP EXISTING THEME
# =========================================================

st.set_page_config(
    page_title="BhoomiCon | Government Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp {
    background-color: #F7F4EC;
    color: #172033;
}
.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #182235 100%);
    border-right: 1px solid #B18D43;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #E7CC8B !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: #E0E5ED;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 9px;
    padding: 10px 12px;
    margin-bottom: 5px;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background-color: #283448;
    border-color: #8D7442;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background-color: #3B3427;
    border: 1px solid #B18D43;
}
.stApp h1, .stApp h2, .stApp h3 {
    color: #172033;
    letter-spacing: -0.3px;
}
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E7DFCD;
    border-top: 3px solid #B18D43;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 4px 14px rgba(23, 32, 51, 0.05);
}
[data-testid="stMetricLabel"] { color: #77736B; }
[data-testid="stMetricValue"] {
    color: #172033;
    font-weight: 700;
}
.stButton > button, .stFormSubmitButton > button {
    background: linear-gradient(135deg, #C5A45D 0%, #A98435 100%);
    color: #111827;
    border: 1px solid #A98435;
    border-radius: 8px;
    font-weight: 700;
    transition: all 0.2s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #D9BD7B;
    color: #111827;
    border-color: #8F6D28;
}
div[data-baseweb="input"] input,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] textarea {
    border-radius: 8px;
    border-color: #D8CFBB;
}
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border: 1px solid #E7DFCD;
    border-radius: 10px;
    overflow: hidden;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF;
    border-color: #E7DFCD;
    border-radius: 12px;
}
.stApp hr { border-color: #E2D6B9; }
[data-testid="stAlert"] { border-radius: 10px; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 2. APPLICATION SETTINGS
# =========================================================

DEMO_USERNAME = os.getenv("BHOOMICON_USERNAME", "officer")
DEMO_PASSWORD = os.getenv("BHOOMICON_PASSWORD", "ChangeMe123!")

COLUMNS = [
    "ID", "Owner", "Phone", "District", "Location",
    "Land Area", "Area Unit", "Price (INR)",
    "Land Type", "Description", "Status",
]

STATUS_OPTIONS = ["Available", "Under Review", "Approved", "Rejected"]


# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================

def format_inr(value):
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return "₹0"


def area_to_acres(area, unit):
    try:
        area = float(area)
    except (ValueError, TypeError):
        return 0.0

    conversion = {
        "acre": 1.0, "acres": 1.0,
        "cent": 0.01, "cents": 0.01,
        "sq ft": 1 / 43560, "sq.ft": 1 / 43560,
        "sqft": 1 / 43560, "square feet": 1 / 43560,
        "sq m": 1 / 4046.8564224, "sqm": 1 / 4046.8564224,
        "square metres": 1 / 4046.8564224,
        "square meters": 1 / 4046.8564224,
        "hectare": 2.47105381, "hectares": 2.47105381,
    }
    return area * conversion.get(str(unit).strip().lower(), 0.0)


def load_land_data():
    records = get_all_land()
    df = pd.DataFrame(records, columns=COLUMNS)

    if df.empty:
        df["Area in Acres"] = pd.Series(dtype=float)
        return df

    for column in [
        "Owner", "Phone", "District", "Location", "Area Unit",
        "Land Type", "Description", "Status",
    ]:
        df[column] = df[column].fillna("").astype(str)

    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df["Land Area"] = pd.to_numeric(
        df["Land Area"], errors="coerce"
    ).fillna(0)
    df["Price (INR)"] = pd.to_numeric(
        df["Price (INR)"], errors="coerce"
    ).fillna(0)
    df["Status"] = df["Status"].str.strip()

    df["Area in Acres"] = df.apply(
        lambda row: area_to_acres(row["Land Area"], row["Area Unit"]),
        axis=1,
    )
    return df


def display_land_table(df):
    visible = [column for column in COLUMNS if column in df.columns]
    st.dataframe(df[visible], use_container_width=True, hide_index=True)


def page_heading(title, subtitle):
    st.title(title)
    st.caption(subtitle)
    st.divider()


# =========================================================
# 4. GOVERNMENT OFFICER LOGIN — UNCHANGED
# =========================================================

if "government_logged_in" not in st.session_state:
    st.session_state.government_logged_in = False

if not st.session_state.government_logged_in:
    st.markdown(
        "<h1 style='text-align:center;'>🏛️ BhoomiCon</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;'>Government Land Discovery Portal</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    _, login_column, _ = st.columns([1, 1.2, 1])

    with login_column:
        with st.form("government_login_form"):
            st.subheader("Officer Login")
            username = st.text_input(
                "Username", placeholder="Enter officer username"
            )
            password = st.text_input(
                "Password", type="password",
                placeholder="Enter password",
            )
            login_button = st.form_submit_button(
                "Sign In", use_container_width=True
            )

        if login_button:
            valid_username = hmac.compare_digest(username, DEMO_USERNAME)
            valid_password = hmac.compare_digest(password, DEMO_PASSWORD)

            if valid_username and valid_password:
                st.session_state.government_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")

        st.caption(
            "Academic prototype only. Do not use real confidential information."
        )
        st.info(
            "Default demo login: officer\n\n"
            "Default demo password: ChangeMe123!"
        )

    st.stop()


# =========================================================
# 5. SIDEBAR — EXISTING PAGES PLUS TWO NEW PAGES
# =========================================================

with st.sidebar:
    st.markdown("# 🏛️ BhoomiCon")
    st.caption("GOVERNMENT PORTAL")
    st.divider()
    st.markdown("### MAIN MENU")

    page = st.radio(
        "Navigate",
        [
            "Overview",
            "District Analytics",
            "Land Status",
            "Land Value",
            "Smart Matching",
            "Government Project Requirements",
            "Document Verification",
            "Review Listings",
            "All Land Listings",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Connecting Land.**")
    st.markdown("**Enabling Development.**")
    st.caption("Smart Land Discovery for Public Projects")

    if st.button("Log Out", use_container_width=True):
        st.session_state.government_logged_in = False
        st.rerun()


# =========================================================
# 6. LOAD SHARED DATABASE
# =========================================================

try:
    df = load_land_data()
except Exception as error:
    st.error(
        "Could not load land records. Check Landlink_db.py "
        "and landlink.db in your project folder."
    )
    st.exception(error)
    st.stop()


# =========================================================
# 7. OVERVIEW DASHBOARD
# =========================================================

if page == "Overview":
    page_heading(
        "Government Overview",
        "A central view of land registered through BhoomiCon.",
    )

    total = len(df)
    available = int((df["Status"] == "Available").sum()) if total else 0
    under_review = int((df["Status"] == "Under Review").sum()) if total else 0
    approved = int((df["Status"] == "Approved").sum()) if total else 0
    acres = df["Area in Acres"].sum() if total else 0
    total_value = df["Price (INR)"].sum() if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Listings", total)
    c2.metric("Available Lands", available)
    c3.metric("Under Review", under_review)
    c4.metric("Approved Status", approved)

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Land by District")
        if not df.empty:
            st.bar_chart(
                df["District"].replace("", "Unspecified").value_counts(),
                y_label="Number of Listings",
            )
        else:
            st.info("No land listings are available yet.")

    with right:
        st.subheader("Land Status Distribution")
        if not df.empty:
            st.bar_chart(df["Status"].value_counts(),
                         y_label="Number of Listings")
        else:
            st.info("Status analytics will appear after listings are added.")

    st.divider()
    a, b = st.columns(2)
    a.metric("Combined Asking Value", format_inr(total_value))
    b.metric("Combined Registered Area", f"{acres:,.2f} acres")

    st.subheader("Recently Registered Lands")
    if not df.empty:
        display_land_table(df.sort_values("ID", ascending=False).head(5))
    else:
        st.info("No land listings have been registered yet.")


# =========================================================
# 8. DISTRICT ANALYTICS
# =========================================================

elif page == "District Analytics":
    page_heading(
        "District Analytics",
        "Explore registered land across different districts.",
    )

    if df.empty:
        st.info("Add land listings to see district analytics.")
    else:
        summary = (
            df.assign(District=df["District"].replace("", "Unspecified"))
            .groupby("District")
            .agg(
                Listings=("ID", "count"),
                Total_Acres=("Area in Acres", "sum"),
                Asking_Value=("Price (INR)", "sum"),
            )
            .reset_index()
            .sort_values("Listings", ascending=False)
        )

        st.subheader("Listings by District")
        st.bar_chart(
            summary.set_index("District")["Listings"],
            y_label="Number of Listings",
        )
        st.subheader("District Summary")
        summary = summary.rename(
            columns={
                "Total_Acres": "Total Area (Acres)",
                "Asking_Value": "Asking Value (INR)",
            }
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)


# =========================================================
# 9. LAND STATUS
# =========================================================

elif page == "Land Status":
    page_heading(
        "Land Status Management",
        "Monitor the current review status of registered properties.",
    )

    if df.empty:
        st.info("No land records are available.")
    else:
        counts = {
            status: int((df["Status"] == status).sum())
            for status in STATUS_OPTIONS
        }
        cols = st.columns(4)
        for col, status in zip(cols, STATUS_OPTIONS):
            col.metric(status, counts[status])

        st.subheader("Status Distribution")
        st.bar_chart(
            df["Status"].value_counts().reindex(STATUS_OPTIONS, fill_value=0),
            y_label="Number of Listings",
        )

        selected = st.selectbox("Filter by status", ["All"] + STATUS_OPTIONS)
        filtered = df if selected == "All" else df[df["Status"] == selected]
        display_land_table(filtered)


# =========================================================
# 10. LAND VALUE ANALYTICS
# =========================================================

elif page == "Land Value":
    page_heading(
        "Land Value Analytics",
        "Review the asking prices entered by landowners.",
    )

    if df.empty:
        st.info("No land records are available.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Combined Asking Value", format_inr(df["Price (INR)"].sum()))
        c2.metric("Average Listing Price", format_inr(df["Price (INR)"].mean()))
        c3.metric("Highest Asking Price", format_inr(df["Price (INR)"].max()))

        st.subheader("Asking Value by District")
        district_value = (
            df.assign(District=df["District"].replace("", "Unspecified"))
            .groupby("District")["Price (INR)"].sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(district_value, y_label="Asking Value (INR)")
        st.caption(
            "These are owner-entered asking prices, not verified market "
            "valuations or government-approved prices."
        )

        value_df = df[
            ["ID", "District", "Location", "Land Area", "Area Unit",
             "Price (INR)", "Land Type", "Status"]
        ].copy()
        value_df["Price (INR)"] = value_df["Price (INR)"].apply(format_inr)
        st.dataframe(value_df, use_container_width=True, hide_index=True)


# =========================================================
# 11. SMART LAND MATCHING — EXISTING FEATURE
# =========================================================

elif page == "Smart Matching":
    page_heading(
        "Smart Land Matching",
        "Find preliminary matches for a proposed public project.",
    )
    st.info(
        "This educational matching tool provides preliminary estimates, "
        "not legal clearance, environmental approval, or a purchase decision."
    )

    if df.empty:
        st.info("Register land listings before using Smart Matching.")
    else:
        available_df = df[df["Status"] == "Available"].copy()

        if available_df.empty:
            st.warning("There are no listings currently marked Available.")
        else:
            district_options = sorted(
                available_df["District"].replace("", "Unspecified").unique().tolist()
            )
            type_options = sorted(
                available_df["Land Type"].replace("", "Unspecified").unique().tolist()
            )

            with st.form("smart_matching_form"):
                st.subheader("Project Requirements")
                district_choice = st.selectbox(
                    "Required district", ["Any District"] + district_options
                )
                required_acres = st.number_input(
                    "Minimum land area required (acres)",
                    min_value=0.0, value=1.0, step=0.5,
                )
                budget = st.number_input(
                    "Maximum budget (₹)",
                    min_value=0.0, value=10000000.0, step=100000.0,
                )
                type_choice = st.selectbox(
                    "Preferred land type", ["Any Type"] + type_options
                )
                run_matching = st.form_submit_button(
                    "Find Matching Lands", use_container_width=True
                )

            if run_matching:
                matches = available_df.copy()

                if district_choice != "Any District":
                    if district_choice == "Unspecified":
                        matches = matches[matches["District"] == ""]
                    else:
                        matches = matches[matches["District"] == district_choice]

                matches = matches[
                    (matches["Area in Acres"] >= required_acres)
                    & (matches["Price (INR)"] <= budget)
                ]

                if type_choice != "Any Type":
                    if type_choice == "Unspecified":
                        matches = matches[matches["Land Type"] == ""]
                    else:
                        matches = matches[matches["Land Type"] == type_choice]

                if matches.empty:
                    st.warning(
                        "No listings match all requirements. Try changing "
                        "the area, district, land type, or budget."
                    )
                else:
                    def score(row):
                        area_score = (
                            25 if required_acres <= 0
                            else min(25, 25 * row["Area in Acres"] / required_acres)
                        )
                        budget_score = (
                            20 if budget <= 0 and row["Price (INR)"] == 0
                            else max(0, 20 * (1 - row["Price (INR)"] / budget))
                            if budget > 0 else 0
                        )
                        return round(min(100, 30 + 25 + area_score + budget_score), 1)

                    matches["Match Score (%)"] = matches.apply(score, axis=1)
                    matches = matches.sort_values("Match Score (%)", ascending=False)

                    st.success(f"Found {len(matches)} matching listing(s).")
                    result = matches[
                        ["ID", "District", "Location", "Land Area",
                         "Area Unit", "Area in Acres", "Price (INR)",
                         "Land Type", "Match Score (%)"]
                    ].copy()
                    result["Price (INR)"] = result["Price (INR)"].apply(format_inr)
                    st.dataframe(result, use_container_width=True, hide_index=True)
                    st.caption(
                        "Scores are heuristic rankings for demonstration. "
                        "They do not assess legal ownership, zoning, or environmental constraints."
                    )


# =========================================================
# 12. GOVERNMENT PROJECT REQUIREMENTS — NEW FEATURE
# =========================================================

elif page == "Government Project Requirements":
    page_heading(
        "Government Project Requirements",
        "Search available land based on a proposed public project.",
    )

    st.info(
        "This tool only identifies possible matches. It does not select, "
        "reserve, purchase, or transfer any land."
    )

    districts = ["All districts"]
    land_types = ["All types"]

    if not df.empty:
        districts += sorted([
            item for item in df["District"].fillna("").str.strip().unique()
            if item
        ])
        land_types += sorted([
            item for item in df["Land Type"].fillna("").str.strip().unique()
            if item
        ])

    with st.form("government_project_requirements_form"):
        project_type = st.selectbox(
            "Public project type",
            [
                "School", "Hospital", "Public Health Centre",
                "Government Office", "Road", "Public Park", "Other",
            ],
        )
        district = st.selectbox("Required district", districts)
        minimum_area = st.number_input(
            "Minimum land area required",
            min_value=0.01, value=1.0, step=0.25,
        )
        area_unit = st.selectbox(
            "Area unit",
            ["Acres", "Cents", "Square Feet", "Square Metres", "Hectares"],
        )
        maximum_price = st.number_input(
            "Maximum total asking price (₹)",
            min_value=0.0, value=10000000.0, step=100000.0,
        )
        land_type = st.selectbox("Preferred land type", land_types)
        search_clicked = st.form_submit_button(
            "Search Matching Land", use_container_width=True
        )

    if search_clicked:
        try:
            matches = find_matching_land(
                district=district,
                minimum_area=minimum_area,
                area_unit=area_unit,
                maximum_price=maximum_price,
                land_type=land_type,
            )

            st.subheader(f"Results for: {project_type}")

            if matches.empty:
                st.warning(
                    "No available listings match these requirements. "
                    "Try adjusting your budget, area, district, or land type."
                )
            else:
                st.success(f"Found {len(matches)} possible match(es).")
                results = matches.rename(
                    columns={
                        "id": "Listing ID",
                        "owner_name": "Owner",
                        "district": "District",
                        "location": "Location",
                        "land_area": "Land Area",
                        "area_unit": "Area Unit",
                        "area_in_acres": "Area (Acres)",
                        "price": "Asking Price (INR)",
                        "land_type": "Land Type",
                        "status": "Listing Status",
                    }
                )
                display_columns = [
                    "Listing ID", "Owner", "District", "Location",
                    "Land Area", "Area Unit", "Area (Acres)",
                    "Asking Price (INR)", "Land Type", "Listing Status",
                ]
                results = results[display_columns].copy()
                results["Asking Price (INR)"] = results[
                    "Asking Price (INR)"
                ].apply(format_inr)
                st.dataframe(results, use_container_width=True, hide_index=True)

        except Exception as error:
            st.error("The land search could not be completed.")
            st.exception(error)


# =========================================================
# 13. DOCUMENT VERIFICATION — NEW FEATURE
# =========================================================

elif page == "Document Verification":
    page_heading(
        "Document Verification",
        "Record the review status of documents associated with a listing.",
    )

    st.info(
        "This prototype records a review status and note. It does not "
        "upload, authenticate, or legally verify documents."
    )

    try:
        documents_df = get_document_records()

        if documents_df.empty:
            st.info("No land listings are available for document review.")
        else:
            display_df = documents_df[
                [
                    "id", "owner_name", "district", "location",
                    "document_status", "document_reviewed_at",
                ]
            ].rename(
                columns={
                    "id": "Listing ID",
                    "owner_name": "Owner",
                    "district": "District",
                    "location": "Location",
                    "document_status": "Document Status",
                    "document_reviewed_at": "Last Reviewed",
                }
            )

            st.subheader("Document Status Overview")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Update Document Review")

            listing_ids = documents_df["id"].astype(int).tolist()
            selected_id = st.selectbox("Select listing ID", listing_ids)

            selected_row = documents_df[
                documents_df["id"] == selected_id
            ].iloc[0]

            st.write(f"**Owner:** {selected_row['owner_name']}")
            st.write(f"**District:** {selected_row['district']}")
            st.write(f"**Location:** {selected_row['location']}")
            st.write(
                f"**Current document status:** "
                f"{selected_row['document_status']}"
            )

            current_note = str(selected_row["document_review_note"] or "")
            current_status = str(
                selected_row["document_status"] or "Not Submitted"
            )

            with st.form("document_review_form"):
                new_status = st.selectbox(
                    "New document status",
                    DOCUMENT_STATUSES,
                    index=(
                        DOCUMENT_STATUSES.index(current_status)
                        if current_status in DOCUMENT_STATUSES else 0
                    ),
                )
                review_note = st.text_area(
                    "Review note (optional)",
                    value=current_note,
                    placeholder="Example: Please provide a clearer copy.",
                )
                save_review = st.form_submit_button(
                    "Save Document Status", use_container_width=True
                )

            if save_review:
                try:
                    updated = update_document_status(
                        int(selected_id), new_status, review_note
                    )
                    if updated:
                        st.success("Document status updated.")
                        st.rerun()
                    else:
                        st.error("No matching listing was updated.")
                except Exception as error:
                    st.error("Could not update document status.")
                    st.exception(error)

    except Exception as error:
        st.error("Could not load document verification records.")
        st.exception(error)


# =========================================================
# 14. REVIEW LISTINGS — EXISTING FEATURE
# =========================================================

elif page == "Review Listings":
    page_heading(
        "Review Land Listings",
        "Review submissions and update their demonstration status.",
    )

    if df.empty:
        st.info("No land listings are available for review.")
    else:
        review_filter = st.selectbox("Show listings", ["All"] + STATUS_OPTIONS)
        review_df = (
            df.copy() if review_filter == "All"
            else df[df["Status"] == review_filter].copy()
        )

        if review_df.empty:
            st.info("No listings have this status.")
        else:
            display_land_table(review_df)
            st.divider()
            st.subheader("Update Listing Status")

            valid_ids = review_df["ID"].dropna().tolist()
            if valid_ids:
                selected_id = st.selectbox("Select listing ID", valid_ids)
                selected_row = review_df[review_df["ID"] == selected_id].iloc[0]

                st.write(f"**Location:** {selected_row['Location']}")
                st.write(f"**District:** {selected_row['District']}")
                st.write(f"**Current status:** {selected_row['Status']}")

                new_status = st.selectbox(
                    "New status",
                    STATUS_OPTIONS,
                    index=(
                        STATUS_OPTIONS.index(selected_row["Status"])
                        if selected_row["Status"] in STATUS_OPTIONS else 0
                    ),
                )

                if st.button("Save Status Update", use_container_width=True):
                    try:
                        update_status(int(selected_id), new_status)
                        st.success(
                            f"Listing {int(selected_id)} updated to '{new_status}'."
                        )
                        st.rerun()
                    except Exception as error:
                        st.error("The status could not be updated.")
                        st.exception(error)
            else:
                st.info("No valid listing IDs were found.")


# =========================================================
# 15. ALL LAND LISTINGS — EXISTING FEATURE
# =========================================================

elif page == "All Land Listings":
    page_heading(
        "All Land Listings",
        "Search and filter land registered by sellers.",
    )

    if df.empty:
        st.info("No land listings have been registered yet.")
    else:
        search_text = st.text_input(
            "Search by district, location, land type, or description",
            placeholder="Example: Chennai, agricultural, highway...",
        )
        c1, c2 = st.columns(2)

        with c1:
            district_filter = st.selectbox(
                "District",
                ["All"] + sorted(
                    df["District"].replace("", "Unspecified").unique().tolist()
                ),
            )

        with c2:
            status_filter = st.selectbox("Status", ["All"] + STATUS_OPTIONS)

        filtered_df = df.copy()

        if district_filter != "All":
            if district_filter == "Unspecified":
                filtered_df = filtered_df[filtered_df["District"] == ""]
            else:
                filtered_df = filtered_df[
                    filtered_df["District"] == district_filter
                ]

        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["Status"] == status_filter]

        if search_text.strip():
            search_mask = pd.Series(False, index=filtered_df.index)
            for column in ["District", "Location", "Land Type", "Description"]:
                search_mask |= filtered_df[column].str.contains(
                    search_text.strip(), case=False, na=False, regex=False
                )
            filtered_df = filtered_df[search_mask]

        st.write(f"**Showing {len(filtered_df)} listing(s)**")
        display_land_table(filtered_df)

        st.download_button(
            "Download Filtered Listings as CSV",
            data=filtered_df[COLUMNS].to_csv(index=False).encode("utf-8"),
            file_name="bhoomicon_land_listings.csv",
            mime="text/csv",
        )


# =========================================================
# 16. FOOTER
# =========================================================

st.divider()
st.caption("BhoomiCon | Connecting Land. Enabling Development.")
st.caption(
    "Academic prototype only. A listing or status update does not establish "
    "legal ownership, verify documents, or authorise a government land purchase."
)
