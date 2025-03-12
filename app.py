import streamlit as st
import yaml
import pandas as pd
import os
import matplotlib.pyplot as plt
from yaml.loader import SafeLoader

# File storage paths
CONFIG_PATH = "C:/Users/sooriya.poomalai/OneDrive - Agilisium Consulting India Private Limited/Sooriya/Think_solution/config.yaml"
UPLOAD_DIR = "uploaded_files"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load YAML Config
def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)

def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        yaml.dump(config, file, default_flow_style=False)

config = load_config()

# Ensure 'tasks' key exists
if "tasks" not in config:
    config["tasks"] = {}

# Session State for Login
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

# Page Title
st.title("Login Page")

# Select Login Type (Admin / Candidate)
login_type = st.radio("Select Login Type:", ["Admin", "Candidate"])

# ---- ADMIN LOGIN ----
if login_type == "Admin":
    st.subheader("Admin Login")
    admin_email = st.text_input("Email")
    admin_password = st.text_input("Password", type="password")

    if st.button("Login as Admin"):
        admin_data = config["credentials"]["usernames"].get("admin_user")
        if admin_data:
            if admin_email == admin_data["email"] and admin_password == admin_data["password"]:
                st.session_state["authentication_status"] = True
                st.session_state["username"] = "admin_user"
                st.success("Welcome Admin!")
            else:
                st.error("Invalid Admin Credentials!")
        else:
            st.error("Admin user not found in config!")

# ---- CANDIDATE LOGIN ----
elif login_type == "Candidate":
    st.subheader("Candidate Login")
    emp_id = st.text_input("Employee ID")
    emp_email = st.text_input("Email")
    emp_password = st.text_input("Password", type="password")

    if st.button("Login as Candidate"):
        if emp_id in config["credentials"]["usernames"]:
            user_data = config["credentials"]["usernames"][emp_id]
            if user_data["email"] == emp_email and user_data["password"] == emp_password and user_data["role"] == "candidate":
                st.session_state["authentication_status"] = True
                st.session_state["username"] = emp_id
                st.success(f"Welcome Candidate: {emp_id}")
            else:
                st.error("Invalid Candidate Credentials!")
        else:
            st.error("Employee ID not found!")

# ---- AFTER SUCCESSFUL LOGIN ----
if st.session_state["authentication_status"]:
    username = st.session_state["username"]

    # ---- ADMIN DASHBOARD ----
    if config["credentials"]["usernames"][username]["role"] == "admin":
        st.header("Admin Dashboard")
        
        # Create New Employee
        st.subheader("Create New Employee")
        with st.form(key="create_employee"):
            new_emp_id = st.text_input("New Employee ID")
            new_emp_email = st.text_input("New Employee Email")
            submit_button = st.form_submit_button(label="Create Employee")

        if submit_button:
            if new_emp_email.endswith("@agilisium.com"):
                default_password = "agsm123"
                config["credentials"]["usernames"][new_emp_id] = {
                    "email": new_emp_email,
                    "name": new_emp_id,
                    "password": default_password,
                    "role": "candidate",
                    "tasks_completed": 0,
                    "tasks_pending": 0
                }
                save_config(config)
                st.success(f"Employee {new_emp_id} created successfully! Default Password: {default_password}")
            else:
                st.error("Email must end with @agilisium.com")
        
        # ---- USER REPORTS & VISUALIZATION ----
        st.subheader("User Reports & Progress Visualization")

        user_data = []
        for emp, details in config["credentials"]["usernames"].items():
            if details["role"] == "candidate":
                assigned_tasks = len(config["tasks"].get(emp, {}))
                completed_tasks = sum(1 for t in config["tasks"].get(emp, {}).values() if "submitted_file" in t)
                pending_tasks = assigned_tasks - completed_tasks

                details["tasks_completed"] = completed_tasks
                details["tasks_pending"] = pending_tasks
                user_data.append([emp, completed_tasks, pending_tasks])

        save_config(config)

        df = pd.DataFrame(user_data, columns=["Employee ID", "Tasks Completed", "Tasks Pending"])
        st.dataframe(df)

        if not df.empty:
            selected_emp = st.selectbox("Select Candidate to View Progress", df["Employee ID"].tolist())

            # Get selected candidate's progress
            selected_row = df[df["Employee ID"] == selected_emp].iloc[0]
            completed = selected_row["Tasks Completed"]
            pending = selected_row["Tasks Pending"]

            # Show Pie Chart only for selected candidate
            if completed + pending > 0:
                fig, ax = plt.subplots()
                ax.pie(
                    [completed, pending],
                    labels=["Completed", "Pending"],
                    autopct="%1.1f%%",
                    colors=["#4CAF50", "#FF5733"],
                    startangle=90,
                    wedgeprops={"edgecolor": "black"}
                )
                ax.set_title(f"Task Progress for {selected_emp}")
                st.pyplot(fig)
            else:
                st.warning(f"No tasks assigned yet for {selected_emp}.")

        # ---- TASK ASSIGNMENT ----
        st.subheader("Task Assignment")
        selected_emp = st.selectbox("Assign to Employee", df["Employee ID"].tolist() + ["All Users"])
        task_topic = st.text_input("Task Topic")
        task_description = st.text_area("Enter Task Description")
        due_date = st.date_input("Due Date")
        time_limit = st.number_input("Time Limit (hours)", min_value=1, max_value=24, value=2)
        
        if st.button("Assign Task"):
            task_id = f"task_{len(config['tasks'].get(selected_emp, {})) + 1}"
            if selected_emp not in config["tasks"]:
                config["tasks"][selected_emp] = {}
            config["tasks"][selected_emp][task_id] = {
                "topic": task_topic,
                "description": task_description,
                "due_date": str(due_date),
                "time_limit": time_limit
            }
            save_config(config)
            st.success(f"Task Assigned to {selected_emp}")

    # ---- CANDIDATE DASHBOARD ----
    elif config["credentials"]["usernames"][username]["role"] == "candidate":
        st.header("Candidate Dashboard")
        st.write(f"Welcome to the Candidate Portal, {username}!")

        personal_tasks = config["tasks"].get(username, {})
        global_tasks = config["tasks"].get("All Users", {})

        task_data = {**global_tasks, **personal_tasks}

        if task_data:
            for task_id, details in task_data.items():
                st.subheader(f"Task: {details.get('topic', 'N/A')}")
                st.write(f"**Description:** {details.get('description', 'No Description')}")
                st.write(f"**Due Date:** {details.get('due_date', 'N/A')}")
                st.write(f"**Time Limit:** {details.get('time_limit', 'N/A')} hours")

                uploaded_file = st.file_uploader(f"Upload file for {task_id}", type=["py", "ipynb", "txt", "csv"])

                if uploaded_file:
                    task_folder = os.path.join(UPLOAD_DIR, username, task_id)
                    os.makedirs(task_folder, exist_ok=True)
                    file_path = os.path.join(task_folder, uploaded_file.name)

                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    config["tasks"][username][task_id]["submitted_file"] = file_path
                    save_config(config)
                    st.success(f"File submitted successfully for {task_id}!")

        else:
            st.warning("No tasks assigned yet.")
