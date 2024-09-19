import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time, date

conn = sqlite3.connect('data.db')
c = conn.cursor()

# Function to fetch all relevant data from the database
def fetch_all_data():
    with sqlite3.connect('data.db') as conn:
        # Fetch all tables
        trainings_df = pd.read_sql_query("SELECT * FROM trainings", conn)
        bookings_df = pd.read_sql_query("SELECT * FROM bookings", conn)
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        restricted_times_df = pd.read_sql_query("SELECT * FROM restricted_times", conn)
    return trainings_df, bookings_df, users_df, restricted_times_df 

# Fetch data
trainings_df, bookings_df, users_df, restricted_times_df = fetch_all_data()

# Get the current date and time
now = datetime.today()

# write title
st.title("Book Træning")

# Date picker
start_date = st.date_input('Vælg dato', min_value=now+timedelta(days=1))
# Time picker
start_time = st.time_input('Vælg tidspunkt')
        
# Training options
training_choice = st.selectbox('Vælg træning', trainings_df['name'])

# Create a datetime.datetime object from the time and date
start_datetime = datetime.combine(start_date, start_time)
# Compute the end datetime by adding the duration
end_datetime = start_datetime + timedelta(hours=1, minutes=30)

# List of weekday names
weekday_names = ['mandag', 'tirsdag', 'onsdag', 'torsdag', 'fredag', 'lørdag', 'søndag']
# Extract the weekday
weekday_name = weekday_names[start_datetime.weekday()]

# Retrieve opening hours for that day
closing_time = datetime.strptime(restricted_times_df.loc[restricted_times_df['day_of_week'] == start_datetime.weekday(), 'time_start'].values[0], "%H:%M").time()
opening_time = datetime.strptime(restricted_times_df.loc[restricted_times_df['day_of_week'] == start_datetime.weekday(), 'time_end'].values[0], "%H:%M").time()

# Retrieve the training info
training_description = trainings_df.loc[trainings_df['name'] == training_choice, 'description'].values[0]
training_id = trainings_df.loc[trainings_df['name'] == training_choice, 'trainingID'].values[0]
training_price = trainings_df.loc[trainings_df['name'] == training_choice, 'price'].values[0]

# Check if it is whitin restricted times:
open =  end_datetime.time() <= closing_time or start_datetime.time() >= opening_time

# Check if it is free:
day_bookings = bookings_df[bookings_df['date'] == start_date.strftime('%Y-%m-%d')]
free = not ((day_bookings['time_start'] < end_datetime.strftime('%H:%M')) & (day_bookings['time_end'] > start_datetime.strftime('%H:%M'))).any()

if open and free:
    st.write(f"Der er ledigt til {training_description} på {weekday_name} den {start_datetime.day}/{start_datetime.month} fra klokken {start_datetime.hour:02d}:{start_datetime.minute:02d} til klokken {end_datetime.hour:02d}:{end_datetime.minute:02d}.")
    st.write(f"**Pris per deltager:** {training_price} kr")
    with st.form("my_form"):
        navn = st.text_input('Navn')
        nummer = st.text_input('Telefonnummer')
        submitted = st.form_submit_button("Book")
        if submitted:
            if navn and nummer:
                # Check if the phone number exists
                exists = (users_df['number'] == nummer).any()

                if exists:
                    userID = users_df.loc[users_df['number'] == nummer, 'userID'].values[0]
                else:
                    # Insert new user
                    c.execute('INSERT INTO users (name, number) VALUES (?, ?)', (navn, nummer))
                    conn.commit()
                    # Refresh users table
                    users_df = pd.read_sql_query("SELECT * FROM users", conn)
                    userID = users_df.loc[users_df['number'] == nummer, 'userID'].values[0]

                # Insert booking into the database
                c.execute('INSERT INTO bookings (userID, trainingID, date, time_start, time_end) VALUES (?, ?, ?, ?, ?)', 
                          (userID, training_id, start_date.strftime('%Y-%m-%d'), start_datetime.strftime('%H:%M'), end_datetime.strftime('%H:%M')))
                conn.commit()
                
                st.write(f"Du vil modtage en SMS på {nummer}, når din booking er bekræftet.")
            else:
                st.error('Indtast venligst dit navn og telefonnummer.')
            
else:
    st.write('Vi har lukket, eller den ønskede tid er allerede booket.')

# Function to handle login
def login(username, password):
    if username == st.secrets.credentials["username"] and password == st.secrets.credentials["password"]:
        # Display bookings table
        st.sidebar.subheader("Bookings")
        st.sidebar.dataframe(bookings_df)
        # Display users table
        st.sidebar.subheader("Users")
        st.sidebar.dataframe(users_df)
    else:
        st.sidebar.error("Forkert brugernavn eller kodeord")

# login form
st.sidebar.subheader('Træner login')
username = st.sidebar.text_input('Username')
password = st.sidebar.text_input('Password', type='password')
login_button = st.sidebar.button('Log ind')
if login_button:
        login(username, password)
