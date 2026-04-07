# main.py
import ai
import json
import random
import browser
import os
from datetime import datetime, timedelta
import time
import logging
from logging.handlers import RotatingFileHandler

# -------------------------------
# Global variables
# -------------------------------
CURRENT_CHANNEL_ID = ""
CURRENT_ID_CHAT_1 = ""
CURRENT_ID_CHAT_2 = ""
CURRENT_CONTEXT_SIZE = 0
CURRENT_CHAT_NAME = ""
CURRENT_PROMPT_DESC = ""

CURRENT_USER_ID = ""
CURRENT_USER_NAME = ""
CURRENT_USER_CHARACTER = ""
CURRENT_USER_TOKEN = ""

CURRENT_AI_ANSWER = ""

# -------------------------------
# Configuration files
# -------------------------------

CONFIG_FILE = "config.json"        # The main project configuration
BUFFER_FILE = "Bufer_config.json"  # buffer for timestamps


# -------------------------------
# Logging Configuration (Console + File)
# -------------------------------
logger = logging.getLogger("BotLogger")
logger.setLevel(logging.INFO)

# 1. Recording format (Date - Level - Message)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# 2. Handler for FILE (Max. size 100KB, store 1 backup file)
file_handler = RotatingFileHandler("bot_log.log", maxBytes=100000, backupCount=1, encoding="utf-8")
file_handler.setFormatter(formatter)

# 3. Handler for the CONSOLE (Screen)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Adding both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# -------------------------------
# Loading JSON file
# -------------------------------
def load_json(path):
    """
    Loads a JSON file.
    If the file does not exist — creates an empty one.
    If the file is corrupted — it resets.
    """
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        logger.info(f"{path} created (The file was missing)")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"{path} Damaged. File discarded..")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}


# -------------------------------
# Saving a JSON file
# -------------------------------
def save_json(path, data):
    """
    Saves data to a JSON file with pretty formatting
    with support for Russian characters.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error while saving {path}: {e}")


# -------------------------------
# Get today's date
# -------------------------------
def get_today():
    """
    Returns the date in the format YYYY-MM-DD
    """
    return datetime.now().strftime("%Y-%m-%d")


# -------------------------------
# Get the current day of the week
# -------------------------------
def get_day_key():
    """
    Returns the current day of the week in the format config.json:
    mon, tue, wed, thu, fri, sat, sun
    """
    return datetime.now().strftime("%a").lower()


# -------------------------------
# Generating random timestamps
# -------------------------------
def generate_time_marks(start_str, end_str, min_msg, max_msg):
    """
    Generates a list of random timestamps for publication.
    start_str и end_str — lines of the form "07:00"
    min_msg, max_msg — Minimum and maximum number of messages per day
    """
    messages_count = random.randint(min_msg, max_msg)  # random number of messages
    now = datetime.now()

    # convert strings to datetime
    start_time = datetime.strptime(start_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    end_time = datetime.strptime(end_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )

    # total duration of the interval in seconds
    total_seconds = int((end_time - start_time).total_seconds())

    if total_seconds <= 0:
        # if the interval is incorrect
        return []

    slot_size = total_seconds // messages_count  # size of one slot
    marks = []

    for i in range(messages_count):
        slot_start = start_time + timedelta(seconds=i * slot_size)
        random_time = slot_start + timedelta(seconds=random.randint(0, slot_size))
        marks.append(random_time.strftime("%H:%M"))

    marks.sort()  # Just in case, we sort it.
    return marks


# -------------------------------
# Selection of a random participant
# -------------------------------
def pick_random_participant(participants, last_user_id=None):
    """
    Selects a random participant, excluding the one who wrote last.
    """
    if not participants:
        return None
    
    # If there is more than one participant, create a list of available ones (excluding the last author).
    if len(participants) > 1 and last_user_id:
        available = [p for p in participants if p.get("id_user") != last_user_id]
        logger.info(f"We choose from {len(available)} participants (excluded: {last_user_id})")
    else:
        available = participants

    return random.choice(available)


# -------------------------------
# The main entry point for working with the browser and sending a message.
# -------------------------------
def run_browser_process():
    try:
        logger.info(f"--- LAUNCHING BROWSER for {CURRENT_CHAT_NAME} ---")
        
        # We are calling our new module
        chat_context = browser.get_context(
            CURRENT_USER_TOKEN, 
            CURRENT_ID_CHAT_1,
            CURRENT_ID_CHAT_2, 
            CURRENT_CONTEXT_SIZE,
            CURRENT_USER_ID
        )
        
        if chat_context:
            logger.info("Context successfully retrieved. Passing to AI....")
            return chat_context  # <--- IMPORTANT: Returning the data!
            # Here will be the AI challenge (ai_logic.py)
        else:
            logger.warning("Failed to retrieve context from the chat.")
            
    except Exception as e:
        logger.error(f"Error в run_browser_process: {e}")


# -------------------------------
# The main entry point for working with AI.
# -------------------------------
def run_ai_process(chat_context):
    global CURRENT_AI_ANSWER
    
    # We are assembling the prompt constructor
    full_prompt = (
        f"{CURRENT_PROMPT_DESC} {CURRENT_USER_NAME} {CURRENT_USER_CHARACTER} {chat_context}"
    )

    # --- OUTPUT THE FULL PROMPT TO THE SERVICE LOG ---
    logger.info("\n" + "#"*60 + "\nFINAL PROMPT FOR AI:\n" + "-"*60 + f"\n{full_prompt}\n" + "#"*60)

    logger.info("--- SENDING THE FORMED PROMPT TO AI ---")
    
    # Now we are passing not just chat_context, but our assembled full_prompt
    answer = ai.get_ai_answer(full_prompt)
    
    if answer:
        CURRENT_AI_ANSWER = answer
        logger.info(f"AI successfully responded to the user {CURRENT_USER_NAME}")
    else:
        logger.warning("The AI failed to prepare a response.")


# -------------------------------
# Updates global variables with the data of the current task.
# -------------------------------
def update_current_globals(channel, participant):
    """
    Updates global variables with data from the current task.
    """
    global CURRENT_CHANNEL_ID, CURRENT_ID_CHAT_1, CURRENT_ID_CHAT_2, \
           CURRENT_CONTEXT_SIZE, CURRENT_CHAT_NAME, CURRENT_PROMPT_DESC, \
           CURRENT_USER_ID, CURRENT_USER_NAME, CURRENT_USER_CHARACTER, CURRENT_USER_TOKEN

    CURRENT_CHANNEL_ID = channel.get("id_channel", "")
    CURRENT_ID_CHAT_1 = channel.get("id_chat_1", "")
    CURRENT_ID_CHAT_2 = channel.get("id_chat_2", "")
    CURRENT_CONTEXT_SIZE = channel.get("context_size", 0)
    CURRENT_CHAT_NAME = channel.get("name", "")
    CURRENT_PROMPT_DESC = channel.get("prompt_description", "")

    CURRENT_USER_ID = participant.get("id_user", "")
    CURRENT_USER_NAME = participant.get("name", "")
    CURRENT_USER_CHARACTER = participant.get("character", "")
    CURRENT_USER_TOKEN = participant.get("token", "")

    # --- VISUAL CONTROL (DASHBOARD) ---
    logger.info("\n" + "="*50)
    logger.info(f" DATA PREPARATION FOR THE CHANNEL: [{CURRENT_CHANNEL_ID}]")
    logger.info("-" * 50)
    logger.info(f" Work deadlines:    {channel.get('date_start')} >>> {channel.get('date_end')}")
    logger.info(f" CHAT 1 (Parsing):  {CURRENT_ID_CHAT_1}")
    logger.info(f" CHAT 2 (Posting):  {CURRENT_ID_CHAT_2}")
    logger.info(f" Context (message): {CURRENT_CONTEXT_SIZE}")
    logger.info(f" Chat name:        {CURRENT_CHAT_NAME}")
    logger.info(f" Channel prompt:   {CURRENT_PROMPT_DESC[:50]}...") # Showing the beginning of the prompt
    logger.info("-" * 30)
    logger.info(f" USER:            {CURRENT_USER_NAME} (ID: {CURRENT_USER_ID})")
    logger.info(f" Character:        {CURRENT_USER_CHARACTER[:50]}...")
    logger.info(f" Token:           {CURRENT_USER_TOKEN[:10]}***") # Hide the token tail for security
    logger.info("="*50 + "\n")

# Browser unification
def run_ai_process_and_return(chat_context):
    """A helper function that simply returns the text from the AI"""
    run_ai_process(chat_context) # Will fill CURRENT_AI_ANSWER
    return CURRENT_AI_ANSWER


# -------------------------------
# Main channel check
# -------------------------------
def check_channels():
    """
    The main logic of the scheduler:
    - check if the channel is enabled
    - checking the working day
    - Working hours check
    - Generation and verification of timestamps
    """
    config = load_json(CONFIG_FILE)
    buffer_data = load_json(BUFFER_FILE)

    today = get_today()
    day_key = get_day_key()
    now = datetime.now()
    now_time_str = now.strftime("%H:%M")

    for channel in config.get("channels", []):

        # -------------------------------
        # Checking channel activation
        # -------------------------------
        try:
            if not channel.get("enabled", False):
                continue

            # --- NEW BLOCK: DATE CHECK (INSERT HERE) ---
            date_start_str = channel.get("date_start")
            date_end_str = channel.get("date_end")

            if date_start_str and date_end_str:
                d_start = datetime.strptime(date_start_str, "%Y-%m-%d").date()
                d_end = datetime.strptime(date_end_str, "%Y-%m-%d").date()
                d_today = datetime.now().date()

                if not (d_start <= d_today <= d_end):
                    continue # If the date doesn't fit, we just move on to the next channel.
            # -----------------------------------------------

            channel_id = channel["id_channel"]
            schedule = channel.get("schedule", {})
        except Exception as e:
            logger.error(f"Error processing channel {channel.get('channel_id', 'unknown')}: {e}")

        # -------------------------------
        # Checking the working day
        # -------------------------------
        if day_key not in schedule:
            continue

        day_config = schedule[day_key]
        start_str = day_config["start"]
        end_str = day_config["end"]

        # Let's transform it into datetime
        start_time = datetime.strptime(start_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        end_time = datetime.strptime(end_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )

        # -------------------------------
        # Checking working hours
        # -------------------------------
        if not (start_time <= now < end_time):
            continue

        # -------------------------------
        # Working with buffer
        # -------------------------------
        if channel_id not in buffer_data:
            buffer_data[channel_id] = {}

        channel_buffer = buffer_data[channel_id]

        # -------------------------------
        # Generating timestamps if they have not been generated yet today
        # -------------------------------
        if channel_buffer.get("date") != today:
            min_msg = day_config["messages"]["min"]
            max_msg = day_config["messages"]["max"]

            marks = generate_time_marks(start_str, end_str, min_msg, max_msg)

            channel_buffer["date"] = today
            channel_buffer["time_marks"] = marks

            logger.info(f"[{channel_id}] Labels have been generated ({len(marks)} шт.): {marks}")

        # -------------------------------
        # Checking for the occurrence of a mark (with queue protection)
        # -------------------------------
        marks = channel_buffer.get("time_marks", [])
        if not marks:
            continue

        # Filtering labels: separating those that have already passed
        past_marks = []
        remaining_marks = []

        for m_str in marks:
            m_time = datetime.strptime(m_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if now >= m_time:
                past_marks.append(m_str)
            else:
                remaining_marks.append(m_str)


        # We find the beginning of the label processing block
        if past_marks:
            # --- NEW LINE: Retrieve the last user ID from the channel buffer ---
            last_user_id = channel_buffer.get("last_used_user_id")
            
            # We pass this ID to the selection function (we will fix it below)
            participant = pick_random_participant(channel["participants"], last_user_id)
            
            if participant:
                # 1. Environment setup
                update_current_globals(channel, participant)
                
                # 2. Launch of a unified session
                success = browser.get_full_session(
                    CURRENT_USER_TOKEN, 
                    CURRENT_ID_CHAT_1, 
                    CURRENT_ID_CHAT_2, 
                    CURRENT_CONTEXT_SIZE,
                    CURRENT_CHAT_NAME,
                    CURRENT_USER_ID,
                    CURRENT_USER_NAME,
                    CURRENT_CHANNEL_ID,
                    run_ai_process_and_return 
                )

                if success:
                    logger.info(f"[{channel_id}] The cycle has been successfully completed.")
                    channel_buffer["last_used_user_id"] = participant.get("id_user")
                    # REMOVE the label only upon actual success
                    channel_buffer["time_marks"] = remaining_marks 
                else:
                    logger.error(f"[{channel_id}] Publication error. The label remains for repetition.")
                    # We do NOT update time_marks so that on the next cycle the bot will try again.




    # We save the updated buffer.
    save_json(BUFFER_FILE, buffer_data)


# -------------------------------
# The main program loop
# -------------------------------
def main_loop():
    """
    Infinite loop with crash protection.
    """
    logger.info("The program has been launched.")
    while True:
        try:
            check_channels()
        except Exception as e:
            logger.error(f"Critical error in the main loop: {e}")
        time.sleep(10)


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    main_loop()