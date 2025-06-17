import streamlit as st
import json
from openai import OpenAI
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import date

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# --- OpenAI Setup ---
client = OpenAI(api_key=st.secrets["openai_api_key"])

creds_dict = st.secrets["gcp_service_account"]
cost_code_mapping_text = """00030 - Financing Fees
00110 - Architectural Fees
00150 - Engineering Fees
00160 - Interior Design
01020 - First Aid/safety/Inspect/Carp./Lab
01025 - Safety Supplies
01028 - Safety Audit
01100 - Surveying
01200 - Hydro/Gas/Telus Services
01210 - Temp Hydro
01220 - Temporary Heat
01230 - Temporary Lighting & Security Lighting
01240 - Temporary Water
01250 - Temporary Fencing
01400 - Tree Protection
01520 - Sanitary Facilities
01560 - Project Construction Signs
01710 - Progressive Site Clean-up
01720 - Final Clean-up
01721 - Pressure Washing
01750 - Disposal Bins/Fees
01760 - Protect Finishes
01810 - Hoist/ crane/Scaffold rental
01820 - Winter Protection
01900 - Cash Allowance
02220 - Demolition
02225 - Demolition (secondary)
02270 - Erosion & Sediment Control
02300 - Site Services (Fence)
02310 - Finish Grading
02315 - Excavation & Backfill
02600 - Drainaige & Stormwater
02621 - Foundation Drain Tile
02700 - Exterior Hardscape
02705 - Exterior Decking
02773 - Curbs & Gutters & Sidewalk
02820 - Fencing & Gates (Fnds, Stone & Alumn)
02900 - Landscaping
02910 - Irrigation Systems
03050 - Concrete Material
03100 - Formwork Material
03150 - Foundation Labor (Form, Rebar, Hardware)
03210 - Reinforcing Steel Material and Hardware
03350 - Concrete Placing/Finishing
03351 - Concrete Pumping
03360 - Special Concrete Finishes
03800 - Cutting & Coring
04200 - Masonry
04400 - Stone Veneer
05090 - Exterior Railing and Guardrail
05095 - Driveway Gates & Fencing
05100 - Steel Beams
05700 - Metal Chimney Cap
05710 - Deck Flashing
06060 - Framing Lumber
06110 - Framing Labor/backframing Labor
06175 - Wood Trusses
06200 - Interior Finishing Material
06220 - Finishing Labor
06410 - Custom Cabinets
06415 - Bath Vanity
06420 - Stone/Countertop - Material
06425 - Stone/Countertop - Fabrication
06430 - Interior Railings
06450 - Fireplace Mantels
07200 - Interior Waterproofing/Shower pan
07210 - Building Insulation
07220 - Building Exterior Waterproofing/Vapour Barrier
07311 - Roofing System
07450 - Siding/Trims - Material
07460 - Siding/Trims - Labor
07465 - Stucco
07500 - Torch & Decking
07600 - Metal Roofing - Prepainted Aluminum
07714 - Gutter & Downspouts
07920 - Sealants & Caulking
08210 - Interior Doors
08215 - Exterior Doors
08216 - Front/Entrance Door
08220 - Closet Doors - Bifolds
08360 - Garage Door
08560 - Window Material
08570 - Window Installation
08580 - Window Waterproofing
08600 - Skylights
08700 - Cabinetry and finish hardware
08800 - Door hardware
09200 - Drywall Systems
09300 - Exterior Tile Work- Material
09310 - Exterior Tile Work- Installation
09640 - Wood Flooring - Material
09645 - Wood Flooring - Installation
09650 - Interior Tile Work- Material
09655 - Interior Tile Work - Installation
09680 - Carpeting - Material
09690 - Carpeting - Labor
09900 - Painting Exterior
09905 - Painting Interior
09910 - Wallpaper Material
09920 - Wallpaper Labor
10810 - Residential Washroom Accessories
10820 - Shower Enclosures
10830 - Bathroom Mirrors
10840 - Mirror and Glazing
10850 - Wine Rack
10900 - Closet Specialties
11450 - Appliances
11452 - Appliance Installation
11455 - Built-in Vacuum
11460 - Outdoor Kitchen BBQ & Sink
12490 - Window Treatment
12500 - Furniture
13150 - Swimming Pools
13160 - Generator
13170 - Dry Sauna
13180 - Hot Tubs
15015 - Plumbing Rough in
15300 - Fire Protection (Sprinklers)
15410 - Plumbing Fixtures
15500 - Radiant Heating
15610 - Wine Cellar Cooling Unit
15700 - Air Conditioning/HRV
15750 - Fire Place Inserts
16050 - General Electrical
16100 - Solar System
16500 - Fixtures
16800 - Low Voltage (Security, Internet)
16900 - Sound and Audio"""

# --- Dropdown Options ---
properties = ["Coto", "Milford", "647 Navy", "645 Navy", 'Sagebrush', 'Paramount', '126 Scenic', 'San Marino', 'King Arthur', 'Via Sanoma', 'Highland', 'Channel View', 'Paseo De las Estrellas']
payable_parties = ["Christian Granados (Vendor)", "Jessica Ajtun", "Andres De Jesus"]

# --- Cost Code Assignment Function ---
def assign_cost_code(description: str) -> str:
    prompt = (
        "Choose the most appropriate cost code for the project description below, based on this mapping:\n\n"
        + cost_code_mapping_text +
        "\n\nDescription:\n"
        f"{description}\n\n"
        "Respond only with a single cost code string in the format 'CODE - Description'."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return response.choices[0].message.content.strip()
    except:
        return "Uncategorized"

# --- Streamlit UI ---
st.title("Subcontractor Payment")

with st.form("subcontractor_payment_form"):
    date_invoiced = st.date_input("Date Invoiced", value=date.today())
    property_selected = st.selectbox("Property", properties)
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    payable_party = st.selectbox("Payable Party", payable_parties)
    description = st.text_area("Project Description")

    submitted = st.form_submit_button("Submit Payment")

if submitted:
    if not description:
        st.error("Please fill out the project description.")
    else:
        with st.spinner("Processing..."):
            cost_code = assign_cost_code(description)

            result = {
                "Date Invoiced": date_invoiced.strftime("%Y-%m-%d"),
                "Property": property_selected,
                "Amount": amount,
                "Payable Party": payable_party,
                "Project Description": description,
                "Cost Code": cost_code
            }

            

            df = pd.DataFrame([result])

            df['Date Paid'] = None
            df['Unique ID'] = None
            df['Item Name'] = None
            df['Hours'] = None
            df['Worker Name'] = None
            df['Claim Number'] = None
            df['QB Property'] = None
            df['Invoice Number'] = None
            df['Payment Method'] = None
            df['Status'] = None
            df['Form'] = "Subcontractor"
            df['Drive Link'] = None
            final_df = df[["Date Paid", "Date Invoiced", "Unique ID", "Claim Number", "Worker Name", "Hours", "Item Name", "Property", "QB Property", "Amount", 'Payable Party', 'Project Description', "Invoice Number", "Cost Code", 'Payment Method', "Status", "Form", "Drive Link"]]
            
            

            def upload_to_google_sheet(df):
                    from gspread.utils import rowcol_to_a1

                    
                    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                    creds_dict = st.secrets["gcp_service_account"]
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                    client = gspread.authorize(creds)
                    sheet = client.open("BSD MASTER DATA")
                    worksheet = sheet.worksheet("TEST")

                    existing = worksheet.get_all_values()

                    # If empty, write headers first
                    if not existing:
                        worksheet.append_row(df.columns.tolist(), value_input_option="USER_ENTERED") 
                        start_row = 2
                    else:
                        start_row = len(existing) + 1

                    # Write all rows in one batch
                    data = df.values.tolist()
                    end_row = start_row + len(data) - 1
                    end_col = len(df.columns)
                    cell_range = f"A{start_row}:{rowcol_to_a1(end_row, end_col)}"

                    worksheet.update(cell_range, data, value_input_option="USER_ENTERED")

            upload_to_google_sheet(final_df)

            st.success("✅ Payment entry processed.")
   

