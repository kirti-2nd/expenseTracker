import streamlit as st
from main import GroupExpenseTracker
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import os


credentials_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

# Define the scope for the Google Sheets and Google Drive API
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate using the service account file
credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)

# Connect to Google Sheets
client = gspread.authorize(credentials)

# Open the sheet by name or URL
sheet = client.open_by_key("1Mc8IYS05ktJZWuSas8fagHY1_f7NLj6vzscdRZrT6Pg").sheet1
if "expense_tracker" not in st.session_state:
    st.session_state.expense_tracker = GroupExpenseTracker(sheet)



# Streamlit configuration
st.set_page_config(page_title="Group Expense Tracker", page_icon="💸")
st.title("")  # Clear the default title

# Path Settings
current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
css_file = current_dir / "styles" / "main.css"

with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

# Create a session state object
session_state = st.session_state

# Check if the 'expense_tracker' object exists in the session state
if "expense_tracker" not in session_state:
    # If not, create and initialize it
    session_state.expense_tracker = GroupExpenseTracker()

# Center-align the heading using HTML
st.markdown(
    '<h1 style="text-align: center;">Group Expense Tracker</h1>',
    unsafe_allow_html=True,
)

# Navigation Menu
selected = option_menu(
    menu_title=None,
    options=["Details", "Overview", "Distribution"],
    icons=[
        "pencil-fill",
        "clipboard2-data",
        "bar-chart-fill",
    ],  # https://icons.getbootstrap.com/
    orientation="horizontal",
)

# Access the 'expense_tracker' object from session state
expense_tracker = session_state.expense_tracker

if selected == "Details":
    st.header("Add Member")
    with st.expander("Add Member"):
        # Sidebar for adding family members
        member_name = st.text_input("Name").title()
        earning_status = st.checkbox("Earning Status")
        if earning_status:
            earnings = st.number_input("Earnings", value=1, min_value=1)
        else:
            earnings = 0

        if st.button("Add Member"):
            try:
                # Check if family member exists
                member = [
                    member
                    for member in expense_tracker.members
                    if member.name == member_name
                ]
                # If not exist add family member
                if not member:
                    expense_tracker.add_family_member(
                        member_name, earning_status, earnings
                    )
                    st.success("Member added successfully!")
                # Else, update it
                else:
                    expense_tracker.update_family_member(
                        member[0], earning_status, earnings
                    )
                    st.success("Member updated successfully!")
            except ValueError as e:
                st.error(str(e))

    # Sidebar for adding expenses
    st.header("Add Expenses")
    with st.expander("Add Expenses"):
        expense_category = st.selectbox(
            "Category",
            (
                "Groceries",
                "Rent",
                "Food",
                "Transportation",
                "Water",
                "Others",
            ),
        )
        expense_description = st.text_input("Description").title()
        expense_value = st.number_input("Amount", min_value=0)
        expense_date = st.date_input("Date", value="today")

        if st.button("Add Expense"):
            try:
                # Add the expense
                expense_tracker.merge_similar_category(
                    expense_value, expense_category, expense_description, expense_date
                )
                st.success("Expense added successfully!")
            except ValueError as e:
                st.error(str(e))
elif selected == "Overview":
    # Display family members
    if not expense_tracker.members:
        st.info(
            "No members added yet"
        )
    else:
        st.header("Members")
        (
            name_column,
            earning_status_column,
            earnings_column,
            family_delete_column,
        ) = st.columns(4)
        name_column.write("**Name**")
        earning_status_column.write("**Earning status**")
        earnings_column.write("**Earnings**")
        family_delete_column.write("**Action**")

        for member in expense_tracker.members:
            name_column.write(member.name)
            earning_status_column.write(
                "Earning" if member.earning_status else "Not Earning"
            )
            earnings_column.write(member.earnings)

            if family_delete_column.button(f"Delete {member.name}"):
                expense_tracker.delete_family_member(member)
                st.rerun()

        # Display expenses
        st.header("Expenses")
        if not expense_tracker.expense_list:
            st.info(
            "No expenses added yet"
        )
        else:
            (
                value_column,
                category_column,
                description_column,
                date_column,
                expense_delete_column,
            ) = st.columns(5)
            value_column.write("**Value**")
            category_column.write("**Category**")
            description_column.write("**Description**")
            date_column.write("**Date**")
            expense_delete_column.write("**Delete**")

            for expense in expense_tracker.expense_list:
                value_column.write(expense.value)
                category_column.write(expense.category)
                description_column.write(expense.description)
                date_column.write(expense.date)

                if expense_delete_column.button(f"Delete {expense.category}"):
                    expense_tracker.delete_expense(expense)
                    st.rerun()

        total_earnings = expense_tracker.calculate_total_earnings()               # Calculate total earnings
        total_expenditure = expense_tracker.calculate_total_expenditure()         # Calculate total expenditure
        remaining_balance = total_earnings - total_expenditure                    # Calculate remaining balance
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Earnings", f"{total_earnings}")          # Display total earnings
        col2.metric("Total Expenditure", f"{total_expenditure}")    # Display total expenditure 
        col3.metric("Remaining Balance", f"{remaining_balance}")    # Display remaining balance 

elif selected == "Distribution":
    # Create a list of expenses and their values
    expense_data = [
        (expense.category, expense.value) for expense in expense_tracker.expense_list
    ]
    if expense_data:
        # Calculate the percentage of expenses for the pie chart
        expenses = [data[0] for data in expense_data]
        values = [data[1] for data in expense_data]
        total = sum(values)
        percentages = [(value / total) * 100 for value in values]

        # Create a smaller pie chart with a transparent background
        fig, ax = plt.subplots(figsize=(3, 3), dpi=300)
        ax.pie(
            percentages,
            labels=expenses,
            autopct="%1.1f%%",
            startangle=140,
            textprops={"fontsize": 6, "color": "white"},
        )
        ax.set_title("Expense Distribution", fontsize=12, color="white")

        # Set the background color to be transparent
        fig.patch.set_facecolor("none")

        # Display the pie chart in Streamlit
        st.pyplot(fig)
    else:
        st.info(
            "No members added yet"
        )