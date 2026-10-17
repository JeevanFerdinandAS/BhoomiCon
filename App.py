
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from bhoomicon_features import (
    get_document_records,
    prepare_feature_columns,
)


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="BhoomiCon | Seller Portal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).resolve().parent / "landlink.db"

STATUSES = [
    "Available",
    "Under Review",
    "Approved",
    "Rejected",
    "Sold Privately",
    "Withdrawn from Sale",
]

SELLER_AVAILABILITY = [
    "Available",
    "Sold Privately",
    "Withdrawn from Sale",
]


# =========================================================
# 2. ROYAL NAVY, GOLD AND IVORY THEME
# =========================================================

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
    background: linear-gradient(
        180deg,
        #111827 0%,
        #182235 100%
    );
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
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background-color: #283448;
    border-color: #8D7442;
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(
    input:checked
) {
    background-color: #3B3427;
    border: 1px solid #B18D43;
}

.stApp h1,
.stApp h2,
.stApp h3 {
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

[data-testid="stMetricLabel"] {
    color: #77736B;
}

[data-testid="stMetricValue"] {
    color: #172033;
    font-weight: 700;
}

.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(
        135deg,
        #C5A45D 0%,
        #A98435 100%
    );
    color: #111827;
    border: 1px solid #A98435;
    border-radius: 8px;
    font-weight: 700;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
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

.stApp hr {
    border-color: #E2D6B9;
}

[data-testid="stAlert"] {
    border-radius: 10px;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. DATABASE FUNCTIONS
# =========================================================

def get_connection():
    return sqlite3.connect(str(DB_PATH))


def load_records():
    """Read records from the shared database."""
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT id, owner_name, phone, district, location,
                   land_area, area_unit, price, land_type,
                   description, status
            FROM land_records
            ORDER BY id DESC
            """,
            conn,
        )


def add_land(
    owner_name,
    phone,
    district,
    location,
    land_area,
    area_unit,
    price,
    land_type,
    description,
):
    """Create a new land listing."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO land_records (
                owner_name, phone, district, location,
                land_area, area_unit, price, land_type,
                description, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_name.strip(),
                phone.strip(),
                district.strip(),
                location.strip(),
                float(land_area),
                area_unit,
                float(price),
                land_type,
                description.strip(),
                "Available",
            ),
        )


def update_land_details(
    land_id,
    phone,
    owner_name,
    district,
    location,
    land_area,
    area_unit,
    price,
    land_type,
    description,
):
    """Update a listing only when its ID and phone match."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE land_records
            SET owner_name = ?,
                district = ?,
                location = ?,
                land_area = ?,
                area_unit = ?,
                price = ?,
                land_type = ?,
                description = ?
            WHERE id = ? AND phone = ?
            """,
            (
                owner_name.strip(),
                district.strip(),
                location.strip(),
                float(land_area),
                area_unit,
                float(price),
                land_type,
                description.strip(),
                int(land_id),
                phone.strip(),
            ),
        )

        return cursor.rowcount > 0


def update_availability(land_id, phone, new_status):
    """Change availability only for the matching listing and phone."""
    if new_status not in SELLER_AVAILABILITY:
        raise ValueError("Invalid seller availability option.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE land_records
            SET status = ?
            WHERE id = ? AND phone = ?
            """,
            (
                new_status,
                int(land_id),
                phone.strip(),
            ),
        )

        return cursor.rowcount > 0


def area_in_acres(area, unit):
    """Convert common land units to acres."""
    conversion = {
        "Acres": 1.0,
        "Cents": 0.01,
        "Square Feet": 1 / 43560,
        "Square Metres": 1 / 4046.8564224,
        "Hectares": 2.47105381,
    }

    return float(area) * conversion.get(unit, 0.0)


def money(value):
    return f"₹{float(value):,.0f}"


def heading(title, subtitle):
    st.title(title)
    st.caption(subtitle)
    st.divider()


def show_listings(df):
    if df.empty:
        st.info("No listings found.")
        return

    display_df = df[
        [
            "id",
            "district",
            "location",
            "land_area",
            "area_unit",
            "price",
            "land_type",
            "status",
        ]
    ].copy()

    display_df.columns = [
        "Listing ID",
        "District",
        "Location",
        "Land Area",
        "Unit",
        "Asking Price (INR)",
        "Land Type",
        "Availability / Status",
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 4. CHECK DATABASE
# =========================================================

try:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS land_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                district TEXT NOT NULL,
                location TEXT NOT NULL,
                land_area REAL NOT NULL,
                area_unit TEXT NOT NULL,
                price REAL NOT NULL,
                land_type TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Available'
            )
            """
        )

        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(land_records)"
            ).fetchall()
        }

        if "status" not in columns:
            conn.execute(
                """
                ALTER TABLE land_records
                ADD COLUMN status TEXT DEFAULT 'Available'
                """
            )

    # Add the new document fields without deleting existing data.
    prepare_feature_columns()

except Exception as error:
    st.error("Could not prepare the BhoomiCon database.")
    st.code(str(error))
    st.stop()


# =========================================================
# 5. SELLER VERIFICATION FOR THIS PROTOTYPE
# =========================================================

if "seller_phone_verified" not in st.session_state:
    st.session_state.seller_phone_verified = False

if "seller_phone" not in st.session_state:
    st.session_state.seller_phone = ""


# =========================================================
# 6. SIDEBAR — EXISTING INTERFACE
# =========================================================

with st.sidebar:
    st.markdown("# 🌿 BhoomiCon")
    st.caption("SELLER PORTAL")
    st.divider()

    st.markdown("### MAIN MENU")

    page = st.radio(
        "Navigate",
        [
            "Overview",
            "Register Land",
            "My Listings",
            "Edit Listing",
            "Manage Availability",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**Your land. Your choice.**")
    st.caption("Connecting Land. Enabling Development.")

    if st.session_state.seller_phone_verified:
        st.success("Seller session active")

        if st.button("End Seller Session", use_container_width=True):
            st.session_state.seller_phone_verified = False
            st.session_state.seller_phone = ""
            st.rerun()


# =========================================================
# 7. LOAD DATA
# =========================================================

try:
    records_df = load_records()
except Exception as error:
    st.error("Unable to load land records.")
    st.code(str(error))
    st.stop()


# =========================================================
# 8. OVERVIEW
# =========================================================

if page == "Overview":

    heading(
        "Seller Dashboard",
        "Manage your registered properties and availability.",
    )

    st.markdown(
        """
        Welcome to **BhoomiCon**.

        Register land you are willing to sell, keep your listing
        details up to date, and change availability whenever your
        plans change.
        """
    )

    total_listings = len(records_df)

    available_count = int(
        (records_df["status"] == "Available").sum()
    ) if total_listings else 0

    sold_count = int(
        (records_df["status"] == "Sold Privately").sum()
    ) if total_listings else 0

    withdrawn_count = int(
        (records_df["status"] == "Withdrawn from Sale").sum()
    ) if total_listings else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Listings", total_listings)
    c2.metric("Available", available_count)
    c3.metric("Sold Privately", sold_count)
    c4.metric("Withdrawn", withdrawn_count)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Listings by Land Type")

        if not records_df.empty:
            st.bar_chart(records_df["land_type"].value_counts())
        else:
            st.info("Your land analytics will appear here.")

    with right:
        st.subheader("Listing Status")

        if not records_df.empty:
            st.bar_chart(records_df["status"].value_counts())
        else:
            st.info("No status data is available yet.")

    st.divider()

    st.subheader("Recent Listings")
    show_listings(records_df.head(5))

    st.caption(
        "The dashboard summary includes all prototype records. "
        "Use seller verification in My Listings to access your own listings."
    )


# =========================================================
# 9. REGISTER LAND
# =========================================================

elif page == "Register Land":

    heading(
        "Register New Land",
        "Add the property details you want to share with the portal.",
    )

    with st.form("register_land_form"):

        st.subheader("Owner Details")

        owner_name = st.text_input("Owner name")
        phone = st.text_input(
            "Contact phone number",
            help="Use the same phone number later to manage this listing.",
        )

        st.subheader("Property Details")

        col1, col2 = st.columns(2)

        with col1:
            district = st.text_input("District")
            location = st.text_input("Land location / area / village")
            land_area = st.number_input(
                "Land area",
                min_value=0.01,
                value=1.0,
                step=0.5,
            )

        with col2:
            area_unit = st.selectbox(
                "Area unit",
                [
                    "Acres",
                    "Cents",
                    "Square Feet",
                    "Square Metres",
                    "Hectares",
                ],
            )

            price = st.number_input(
                "Total asking price (₹)",
                min_value=0.0,
                value=1000000.0,
                step=50000.0,
            )

            land_type = st.selectbox(
                "Land type",
                [
                    "Agricultural",
                    "Residential",
                    "Commercial",
                    "Industrial",
                    "Mixed Use",
                    "Other",
                ],
            )

        description = st.text_area(
            "Description",
            placeholder=(
                "Mention road access, nearby facilities, "
                "or other non-sensitive details."
            ),
        )

        consent = st.checkbox(
            "I agree to share these listing details with "
            "the BhoomiCon prototype for demonstration."
        )

        submitted = st.form_submit_button(
            "Register Land",
            use_container_width=True,
        )

    if submitted:
        if not all([
            owner_name.strip(),
            phone.strip(),
            district.strip(),
            location.strip(),
        ]):
            st.error(
                "Please enter the owner name, phone number, "
                "district, and location."
            )

        elif not phone.strip().replace("+", "").replace(" ", "").isdigit():
            st.error(
                "Enter a valid phone number using digits and an optional +."
            )

        elif not consent:
            st.warning("Please confirm the data-sharing statement.")

        else:
            try:
                add_land(
                    owner_name,
                    phone,
                    district,
                    location,
                    land_area,
                    area_unit,
                    price,
                    land_type,
                    description,
                )

                st.success("Land listing registered successfully!")
                st.info(
                    "Keep your listing ID and registered phone number "
                    "available so you can manage this listing later."
                )
                st.rerun()

            except Exception as error:
                st.error("Could not register the land listing.")
                st.code(str(error))


# =========================================================
# 10. VERIFY SELLER FOR LISTING MANAGEMENT
# =========================================================

elif page in ["My Listings", "Edit Listing", "Manage Availability"]:

    heading(
        page,
        "Access and manage listings using the registered contact number.",
    )

    if not st.session_state.seller_phone_verified:

        st.warning(
            "For this prototype, verify a listing using its ID "
            "and the phone number registered with that listing."
        )

        with st.form("seller_verification_form"):

            verify_id = st.number_input(
                "Listing ID",
                min_value=1,
                step=1,
            )

            verify_phone = st.text_input("Registered phone number")

            verify_button = st.form_submit_button(
                "Verify Listing",
                use_container_width=True,
            )

        if verify_button:
            try:
                with get_connection() as conn:
                    result = conn.execute(
                        """
                        SELECT id, phone
                        FROM land_records
                        WHERE id = ? AND phone = ?
                        """,
                        (int(verify_id), verify_phone.strip()),
                    ).fetchone()

                if result:
                    st.session_state.seller_phone_verified = True
                    st.session_state.seller_phone = verify_phone.strip()
                    st.success("Listing verified.")
                    st.rerun()
                else:
                    st.error(
                        "No matching listing was found. "
                        "Check the ID and registered phone number."
                    )

            except Exception as error:
                st.error("Verification failed.")
                st.code(str(error))

        st.stop()

    seller_df = records_df[
        records_df["phone"].astype(str)
        == st.session_state.seller_phone
    ].copy()

    if seller_df.empty:
        st.info("No listings are linked to this contact number.")
        st.stop()


    # =====================================================
    # 11. MY LISTINGS + DOCUMENT VERIFICATION STATUS
    # =====================================================

    if page == "My Listings":

        st.subheader("Your Registered Properties")

        c1, c2, c3 = st.columns(3)

        c1.metric("Your Listings", len(seller_df))

        c2.metric(
            "Available",
            int((seller_df["status"] == "Available").sum()),
        )

        c3.metric(
            "No Longer Available",
            int(
                seller_df["status"].isin(
                    ["Sold Privately", "Withdrawn from Sale"]
                ).sum()
            ),
        )

        show_listings(seller_df)

        # NEW FEATURE: Sellers can view document review status.
        st.divider()
        st.subheader("Document Verification Status")

        try:
            all_document_records = get_document_records()

            my_document_records = all_document_records[
                all_document_records["phone"].astype(str)
                == st.session_state.seller_phone
            ]

            if my_document_records.empty:
                st.info(
                    "No document status is available for your listings."
                )
            else:
                for _, record in my_document_records.iterrows():

                    with st.container(border=True):

                        st.markdown(
                            f"**Listing #{int(record['id'])} — "
                            f"{record['location']}**"
                        )

                        st.write(f"District: {record['district']}")

                        st.write(
                            f"Document status: "
                            f"**{record['document_status']}**"
                        )

                        note = str(
                            record["document_review_note"] or ""
                        ).strip()

                        if note:
                            st.write(f"Officer's note: {note}")
                        else:
                            st.caption(
                                "No review note has been added."
                            )

                        reviewed_at = str(
                            record["document_reviewed_at"] or ""
                        ).strip()

                        if reviewed_at:
                            st.caption(f"Last reviewed: {reviewed_at}")

        except Exception as error:
            st.error(
                "Could not load your document verification status."
            )
            st.exception(error)

        st.download_button(
            "Download My Listings as CSV",
            data=seller_df.to_csv(index=False).encode("utf-8"),
            file_name="my_bhoomicon_listings.csv",
            mime="text/csv",
        )


    # =====================================================
    # 12. EDIT LISTING DETAILS
    # =====================================================

    elif page == "Edit Listing":

        st.subheader("Edit Your Property Details")

        selected_id = st.selectbox(
            "Select listing ID to edit",
            seller_df["id"].tolist(),
        )

        selected = seller_df[
            seller_df["id"] == selected_id
        ].iloc[0]

        with st.form("edit_land_form"):

            owner_name = st.text_input(
                "Owner name",
                value=str(selected["owner_name"]),
            )

            district = st.text_input(
                "District",
                value=str(selected["district"]),
            )

            location = st.text_input(
                "Land location",
                value=str(selected["location"]),
            )

            col1, col2 = st.columns(2)

            unit_options = [
                "Acres",
                "Cents",
                "Square Feet",
                "Square Metres",
                "Hectares",
            ]

            current_unit = str(selected["area_unit"])

            with col1:
                land_area = st.number_input(
                    "Land area",
                    min_value=0.01,
                    value=max(float(selected["land_area"]), 0.01),
                    step=0.5,
                )

                if current_unit not in unit_options:
                    unit_options.append(current_unit)

                area_unit = st.selectbox(
                    "Area unit",
                    unit_options,
                    index=unit_options.index(current_unit),
                )

            with col2:
                price = st.number_input(
                    "Asking price (₹)",
                    min_value=0.0,
                    value=max(float(selected["price"]), 0.0),
                    step=50000.0,
                )

                type_options = [
                    "Agricultural",
                    "Residential",
                    "Commercial",
                    "Industrial",
                    "Mixed Use",
                    "Other",
                ]

                current_type = str(selected["land_type"])

                if current_type not in type_options:
                    type_options.append(current_type)

                land_type = st.selectbox(
                    "Land type",
                    type_options,
                    index=type_options.index(current_type),
                )

            description = st.text_area(
                "Description",
                value=str(selected["description"] or ""),
            )

            save_changes = st.form_submit_button(
                "Save Listing Changes",
                use_container_width=True,
            )

        if save_changes:

            if not all([
                owner_name.strip(),
                district.strip(),
                location.strip(),
            ]):
                st.error(
                    "Owner name, district, and location cannot be empty."
                )

            else:
                try:
                    updated = update_land_details(
                        selected_id,
                        st.session_state.seller_phone,
                        owner_name,
                        district,
                        location,
                        land_area,
                        area_unit,
                        price,
                        land_type,
                        description,
                    )

                    if updated:
                        st.success("Your listing has been updated.")
                        st.rerun()
                    else:
                        st.error(
                            "The listing could not be updated. "
                            "Verify the listing and registered phone."
                        )

                except Exception as error:
                    st.error("Could not save your changes.")
                    st.code(str(error))


    # =====================================================
    # 13. MANAGE AVAILABILITY
    # =====================================================

    elif page == "Manage Availability":

        st.subheader("Update Your Land Availability")

        st.markdown(
            """
            Change the listing status when your plans change.
            For example, mark it **Sold Privately** if you have
            sold it to another private buyer, or **Withdrawn from Sale**
            if you no longer wish to sell it.
            """
        )

        selected_id = st.selectbox(
            "Select listing",
            seller_df["id"].tolist(),
            format_func=lambda value: (
                f"Listing #{value} — "
                f"{seller_df.loc[seller_df['id'] == value, 'location'].iloc[0]}"
            ),
        )

        selected = seller_df[
            seller_df["id"] == selected_id
        ].iloc[0]

        st.write(f"**Current status:** {selected['status']}")

        if selected["status"] in ["Under Review", "Approved", "Rejected"]:
            st.info(
                "This listing has a government review status. "
                "Changing availability will replace that status in this "
                "prototype's single status field."
            )

        current_status = str(selected["status"])
        status_options = SELLER_AVAILABILITY.copy()

        if current_status not in status_options:
            status_options.append(current_status)

        default_index = (
            status_options.index(current_status)
            if current_status in status_options else 0
        )

        new_status = st.selectbox(
            "Choose new availability",
            status_options,
            index=default_index,
        )

        if new_status == "Sold Privately":
            st.warning(
                "This will mark the listing as no longer available "
                "for a government project in the matching feature."
            )

        elif new_status == "Withdrawn from Sale":
            st.info("This marks the property as withdrawn from the market.")

        if st.button("Update Availability", use_container_width=True):

            try:
                updated = update_availability(
                    selected_id,
                    st.session_state.seller_phone,
                    new_status,
                )

                if updated:
                    st.success(
                        f"Listing #{selected_id} is now '{new_status}'."
                    )
                    st.rerun()
                else:
                    st.error(
                        "The listing was not updated. "
                        "Please verify it and try again."
                    )

            except Exception as error:
                st.error("Could not update availability.")
                st.code(str(error))


# =========================================================
# 14. FOOTER
# =========================================================

st.divider()

st.caption(
    "BhoomiCon | Connecting Land. Enabling Development."
)

st.caption(
    "Academic prototype only. Phone-number verification is not "
    "strong authentication. A status update does not verify a sale, "
    "prove legal ownership, or transfer property rights."
)
