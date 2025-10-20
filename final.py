import streamlit as st
import datetime
import re
import subprocess
import sys
import os
import platform


# Import your existing workout modules (make sure these imports match your project)
from lunges import run_lunges
from pushups import run_pushups
from squats import run_squats
from crunches import run_crunches
from sidelyinglegraises import run_sidelying_leg_raises as run_side_lying_leg_raises
from plank import run_plank
from yoga_pose_classifier import run_yoga_pose
from ninjastar import run_orbit_game

if "workout_status" not in st.session_state:
    st.session_state.workout_status = "running"  # can be "running", "paused", "exit"
if "pause_message_shown" not in st.session_state:
    st.session_state.pause_message_shown = False
    
# -------------------- SCHEDULE DATA --------------------
SCHEDULES = {
    "Beginner": {
        "Monday": ["Squats – 3 sets of 15 reps", "Pushups – 3 sets of 10 reps", "Tree Pose – 30 sec"],
        "Tuesday": ["Crunches – 3 sets of 15 reps", "Plank – 30 sec", "Warrior Pose – 30 sec"],
        "Wednesday": ["Lunges – 3 sets of 10 reps", "Side-lying leg raises – 3 sets of 12 reps", "Chair Pose – 30 sec"],
        "Thursday": ["Rest or gentle Yoga"],
        "Friday": ["Squats – 4 sets of 15 reps", "Pushups – 3 sets of 12 reps", "Tree Pose – 30 sec"],
        "Saturday": ["Crunches – 4 sets of 20 reps", "Plank – 45 sec", "Warrior Pose – 30 sec"],
        "Sunday": ["Rest or gentle Yoga"]
    },
    "Intermediate": {
        "Monday": ["Squats – 4 sets of 20 reps", "Pushups – 4 sets of 15 reps", "Tree Pose – 45 sec"],
        "Tuesday": ["Crunches – 4 sets of 20 reps", "Plank – 45 sec", "Warrior Pose – 45 sec"],
        "Wednesday": ["Lunges – 4 sets of 15 reps", "Side-lying leg raises – 4 sets of 15 reps", "Chair Pose – 45 sec"],
        "Thursday": ["Yoga Flow: Tree → Warrior → Chair Pose (hold 1 min each)"],
        "Friday": ["Squats – 5 sets of 20 reps", "Pushups – 4 sets of 20 reps", "Plank – 1 min"],
        "Saturday": ["Crunches – 5 sets of 25 reps", "Plank – 1 min", "Warrior Pose – 1 min"],
        "Sunday": ["Rest or full-body Yoga flow"]
    },
    "Advanced": {
        "Monday": ["Squats – 5 sets of 25 reps", "Pushups – 5 sets of 20 reps", "Plank – 90 sec"],
        "Tuesday": ["Crunches – 5 sets of 30 reps", "Lunges – 5 sets of 20 reps", "Chair Pose – 90 sec"],
        "Wednesday": ["Side-lying leg raises – 5 sets of 20 reps", "Warrior Pose – 90 sec", "Tree Pose – 90 sec"],
        "Thursday": ["Pushups – 6 sets of 25 reps", "Squats – 5 sets of 30 reps", "Plank – 120 sec"],
        "Friday": ["Crunches – 5 sets of 35 reps", "Lunges – 6 sets of 25 reps", "Warrior Pose – 90 sec"],
        "Saturday": ["Chair Pose – 120 sec", "Tree Pose – 120 sec", "Plank – 120 sec"],
        "Sunday": ["Rest or advanced Yoga flow"]
    }
}

# Map exercise names to functions (and specify how to call)
EXERCISE_MAP = {
    "Squats": ("reps", run_squats),
    "Pushups": ("reps", run_pushups),
    "Lunges": ("reps", run_lunges),
    "Crunches": ("reps", run_crunches),
    "Side-lying leg raises": ("reps", run_side_lying_leg_raises),
    "Plank": ("time_seconds", run_plank),
    # Yoga poses: mark as time_seconds_pose and call run_yoga_pose directly
    "Tree Pose": ("time_seconds_pose", lambda **kwargs: run_yoga_pose(**kwargs)),
    "Warrior Pose": ("time_seconds_pose", lambda **kwargs: run_yoga_pose(**kwargs)),
    "Chair Pose": ("time_seconds_pose", lambda **kwargs: run_yoga_pose(**kwargs))
}

# -------------------- Helpers --------------------
def go_to(page):
    st.session_state.page = page
    st.rerun()

def launch_game_script(script_relpath):
    """
    Launch a Python script as a new process. script_relpath is relative to project root.
    Returns the subprocess.Popen object or None.
    """
    # Get the directory of the current Streamlit script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_relpath)
    if not os.path.exists(script_path):
        st.error(f"Game script not found: {script_path}")
        return None

    game_dir = os.path.dirname(script_path)
    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen([sys.executable, script_path],
                                    cwd=game_dir,
                                    creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            proc = subprocess.Popen([sys.executable, script_path], cwd=game_dir)

        st.session_state['game_proc'] = proc
        return proc
    except Exception as e:
        st.error(f"Failed to launch game: {e}")
        return None

# Ensure session_state key exists
if 'game_proc' not in st.session_state:
    st.session_state['game_proc'] = None


def parse_target_from_text(text):
    """
    Given a schedule item e.g. "Squats – 3 sets of 15 reps" or "Plank – 45 sec",
    return (value, type) where type is 'reps' or 'seconds'.
    """
    if not text or "rest" in text.lower():
        return None, None
    lower = text.lower()
    # minutes like "1.5 min" or "1 min"
    m = re.search(r'(\d+(\.\d+)?)\s*min', lower)
    if m:
        val = float(m.group(1))
        return int(val * 60), "seconds"
    # seconds like "45 sec" or "90 sec"
    m = re.search(r'(\d+)\s*sec', lower)
    if m:
        return int(m.group(1)), "seconds"
    # reps
    if "rep" in lower:
        nums = re.findall(r'\d+', text)
        if nums:
            return int(nums[-1]), "reps"
    nums = re.findall(r'\d+', text)
    if nums:
        return int(nums[-1]), "reps"
    return None, None

def get_exercise_name_and_target(item_text):
    """
    Splits "Squats – 3 sets of 15 reps" into ("Squats", "3 sets of 15 reps")
    """
    if "–" in item_text:
        parts = item_text.split("–", 1)
        return parts[0].strip(), parts[1].strip()
    if "-" in item_text:
        parts = item_text.split("-", 1)
        return parts[0].strip(), parts[1].strip()
    return item_text.strip(), ""

def normalize_pose_name(name):
    name = name.strip().lower()
    if "tree" in name:
        return "Tree Pose"
    if "warrior" in name:
        return "Warrior Pose"
    if "chair" in name:
        return "Chair Pose"
    return name.title()

def ensure_session_state():
    defaults = {
        "results": [],
        "page": "welcome",
        "video_path": 0,
        "mode": "Manual Workout",
        "exercise": None,
        "target_reps": None,
        "hold_time": None,
        "yoga_pose": None,
        "schedule_level": None,
        "schedule_day": None,
        "schedule_queue": None,
        "weight": 60,
        "current_schedule_item": None,
        "current_exercise_for_run": None,
        "current_target_value": None,
        "current_target_type": None,
        "daily_completed": [],
        "daily_calories": 0,
        "history": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

ensure_session_state()

# WELCOME
if st.session_state.page == "welcome":
    st.title("Welcome to GetUpGo! the Smart Fitness Tracker!")
    st.write("Track exercises and posture using vision-based pose detection!")
    st.session_state.video_path = 0
    # Center the three buttons
    col_spacer1, col1, col2, col3, col_spacer2 = st.columns([2, 3, 3, 3, 2])
    with col1:
        if st.button("🔹 Manual Workout", use_container_width=True):
            st.session_state.mode = "Manual Workout"
            go_to("select")
    with col2:
        if st.button("📅 Schedule Mode", use_container_width=True):
            st.session_state.mode = "Schedule Mode"
            go_to("schedule_select")
    with col3:
        if st.button("🎮 Fitness Games", use_container_width=True):
            go_to("fitness_games_page")


    # Make the buttons much larger
    st.markdown("""
        <style>
        div.stButton > button {
            height: 80px !important;
            font-size: 22px !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Quick History button in bottom-left
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    left_col, _ = st.columns([1, 4])
    with left_col:
        if st.button("📜 Quick History", use_container_width=False):
            go_to("result_history")


# FITNESS GAMES PAGE
elif st.session_state.page == "fitness_games_page":
    st.title("🎮 Fitness Games")
    st.write("Choose a game — each opens in its own window. Close the game window to return to Streamlit.")
    st.info("Make sure no other app is using the webcam before starting a game (only one process can open the camera at a time).")

    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        if st.button("🦕 Dinosaur(Dino) game"):
            proc = launch_game_script("Dinosaur_and_flappybird_fitness_games/DinosaurGame.py")
            if proc:
                st.success("Dinosaur launched (check new window).")
    with col2:
        if st.button("🐦Flappy Bird"):
            proc = launch_game_script("Dinosaur_and_flappybird_fitness_games/FlappyBird.py")
            if proc:
                st.success("Flappy Bird launched (check new window).")         
    with col3:
        if st.button("🔥Orbit game"):
            proc = launch_game_script("ninjastar.py")
            if proc:
                st.success("Orbit game launched (check new window).")
                
    with col3:
        if st.button("⬅️ Back"):
            go_to("welcome")

    st.divider()
    # Show running game info + Stop button
    proc = st.session_state.get('game_proc')
    if proc:
        st.write(f"🔵 Game running, PID: {getattr(proc, 'pid', 'unknown')}")
        if st.button("⛔ Stop running game"):
            try:
                proc.kill()
                proc.wait(timeout=2)
                st.session_state['game_proc'] = None
                st.success("Game stopped.")
            except Exception as e:
                st.error(f"Could not stop game: {e}")
    else:
        st.write("No game process currently running.")



# MANUAL SELECT
elif st.session_state.page == "select":
    st.title("Select Your Workout (Manual Mode)")
    option = st.selectbox("Choose an exercise", ["Lunges", "Pushups", "Squats","Crunches", "Side-Lying Leg Raises", "Plank", "Yoga"])
    st.session_state.exercise = option
    st.session_state.weight = st.number_input("Enter your weight (kg)", min_value=30, max_value=150, value=st.session_state.weight)

    if option == "Yoga":
        yoga_pose = st.selectbox("Select Yoga Pose", ["Tree Pose", "Warrior II Pose", "Chair Pose"])
        st.session_state.yoga_pose = yoga_pose
        hold_time = st.number_input("Target hold time (in seconds)", min_value=5, max_value=600, value=st.session_state.hold_time or 30)
        st.session_state.hold_time = hold_time
    elif option == "Plank":
        hold_time = st.number_input("Target hold time (in seconds)", min_value=5, max_value=600, value=st.session_state.hold_time or 30)
        st.session_state.hold_time = hold_time
    else:
        target_reps = st.number_input("Target repetitions", min_value=1, max_value=100, value=st.session_state.target_reps or 5)
        st.session_state.target_reps = target_reps

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Exercise"):
            st.session_state.manual_workout_done = False
            go_to("workout")
    with col2:
        if st.button("Back"):
            go_to("welcome")

# SCHEDULE SELECT
elif st.session_state.page == "schedule_select":
    st.title("📅 Workout Schedule Mode")
    level = st.selectbox(
        "Select your plan:",
        list(SCHEDULES.keys()),
        index=list(SCHEDULES.keys()).index(st.session_state.schedule_level) if st.session_state.schedule_level else 0
    )
    st.session_state.schedule_level = level

    today_name = datetime.datetime.today().strftime("%A")
    day_choice = st.selectbox(
        "Select Day:",
        list(SCHEDULES[level].keys()),
        index=list(SCHEDULES[level].keys()).index(st.session_state.schedule_day) if st.session_state.schedule_day else list(SCHEDULES[level].keys()).index(today_name)
    )
    st.session_state.schedule_day = day_choice

    todays_workout = SCHEDULES[level].get(day_choice, ["Rest or gentle Yoga"])
    st.write(f"### Plan for {day_choice} ({level})")
    for i, item in enumerate(todays_workout, 1):
        st.write(f"{i}. {item}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Day's Schedule"):
            st.session_state.schedule_queue = todays_workout.copy()
            st.session_state.daily_completed = []
            st.session_state.daily_calories = 0
            go_to("run_schedule")
    with col2:
        if st.button("Back"):
            go_to("welcome")

# RUN SCHEDULE: pop next item and show announcement (DO NOT start immediately)
elif st.session_state.page == "run_schedule":
    queue = st.session_state.get("schedule_queue") or []
    if not queue:
        st.success(f"All exercises done for {st.session_state.schedule_day} ({st.session_state.schedule_level}).")
        st.write(f"Total calories today: {st.session_state.get('daily_calories', 0):.2f} cal")
        level = st.session_state.schedule_level
        if level == "Beginner":
            if st.button("Do Intermediate/Medium Exercise of this day"):
                st.session_state.schedule_level = "Intermediate"
                st.session_state.schedule_queue = SCHEDULES["Intermediate"].get(st.session_state.schedule_day, []).copy()
                st.session_state.daily_completed = []
                st.session_state.daily_calories = 0
                go_to("run_schedule")
        elif level == "Intermediate":
            if st.button("Do Advanced of this day"):
                st.session_state.schedule_level = "Advanced"
                st.session_state.schedule_queue = SCHEDULES["Advanced"].get(st.session_state.schedule_day, []).copy()
                st.session_state.daily_completed = []
                st.session_state.daily_calories = 0
                go_to("run_schedule")
        else:  # Advanced completed
            st.write("You completed Advanced. You may:")
            if st.button("Pick any manual workout"):
                st.session_state.mode = "Manual Workout"
                go_to("select")
            if st.button("Choose another day"):
                go_to("schedule_select")
        if st.button("Back to Home Page"):
            go_to("welcome")
    else:
        # pop the next item and prepare the announcement
        next_item = queue[0]
        st.session_state.current_schedule_item = next_item
        ex_name, target_text = get_exercise_name_and_target(next_item)
        ex_key = normalize_pose_name(ex_name)
        st.session_state.current_exercise_for_run = ex_key
        val, typ = parse_target_from_text(target_text)
        if ex_key.lower() == "plank":
            typ = "seconds"
        st.session_state.current_target_value = val
        st.session_state.current_target_type = typ
        # go to announcement page BEFORE running the exercise
        go_to("scheduled_announce")

# SCHEDULED ANNOUNCEMENT PAGE (shows details and waits for user to start)
elif st.session_state.page == "scheduled_announce":
    st.title("🔔 Next Exercise — Announcement")
    item = st.session_state.current_schedule_item or "Unknown"
    st.write(f"**Upcoming:** {item}")
    ex_name = st.session_state.current_exercise_for_run or "Unknown"
    st.write(f"**Exercise:** {ex_name}")
    val = st.session_state.current_target_value
    typ = st.session_state.current_target_type
    if val and typ:
        if typ == "seconds":
            st.write(f"**Target Hold Time:** {val} seconds")
        else:
            st.write(f"**Target Repetitions:** {val}")
    st.write("When you're ready press **Start Exercise** to begin tracking.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Exercise"):
             # Remove current item from queue now
            q = st.session_state.get("schedule_queue") or []
            if q and q[0] == st.session_state.current_schedule_item:
              q.pop(0)  # remove the current item
              st.session_state.schedule_queue = q
            # move to actual runner which will call the corresponding function
            go_to("workout_scheduled_run")
    with col2:
        if st.button("Cancel / Back to Schedule"):
            # # push the current item back to the front of the queue (so it isn't lost)
            # q = st.session_state.get("schedule_queue") or []
            # st.session_state.schedule_queue = [st.session_state.current_schedule_item] + q
            go_to("run_schedule")

# WORKOUT RUN (manual)
elif st.session_state.page == "workout":
    st.title(f"🏃 Starting (Manual) {st.session_state.exercise}!")
    col1, col2, col3 = st.columns(3)
    with col1:
      if st.button("⏸ Pause"):
        st.session_state.workout_status = "paused"
    with col2:
      if st.button("▶️ Resume"):
        st.session_state.workout_status = "running"
    with col3:
      if st.button("❌ Exit"):
        st.session_state.workout_status = "exit"
    result = None
    error_message=None
    try:
        ex = st.session_state.exercise
        if ex == "Lunges":
            result = run_lunges(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_reps=st.session_state.target_reps)
        elif ex == "Pushups":
            result = run_pushups(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_reps=st.session_state.target_reps)
        elif ex == "Squats":
            result = run_squats(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_reps=st.session_state.target_reps)
        elif ex == "Crunches":
            result = run_crunches(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_reps=st.session_state.target_reps)    
        elif ex == "Side-Lying Leg Raises":
            result = run_side_lying_leg_raises(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_reps=st.session_state.target_reps)
        elif ex == "Plank":
            result = run_plank(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_seconds=st.session_state.hold_time)
        elif ex == "Yoga":
            result = run_yoga_pose(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_time=st.session_state.hold_time, pose_name=st.session_state.yoga_pose)
    except ImportError as e:
        error_message = f"Import error - check if yoga_pose_classifier.py exists: {e}"
        st.error(error_message) 
    except Exception as e:
        st.error(f"Error running workout: {e}")
        result = {"status": "Failed", "error": str(e)}
    if error_message:
        result = {"status": "Failed", "error": error_message}
    elif result is None:
        result = {"status": "Failed", "error": "Function returned None"}
    result = result or {"status": "Failed"}
    result_meta = {
        "exercise": st.session_state.exercise,
        "mode": "Manual",
        "timestamp": datetime.datetime.now().isoformat()
    }
    if isinstance(result, dict):
        result.update(result_meta)
    st.session_state.results.append(result)
    st.session_state.history.append(result)
    go_to("result_manual")

# WORKOUT RUN FOR SCHEDULED ITEM
elif st.session_state.page == "workout_scheduled_run":
    st.title(f"🏃 Starting (Scheduled) {st.session_state.current_exercise_for_run}!")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏸ Pause"):
            st.session_state.workout_status = "paused"
            st.session_state.pause_message_shown = False
    with col2:
        if st.button("▶️ Resume"):
            st.session_state.workout_status = "running"
            st.session_state.pause_message_shown = False
    with col3:
        if st.button("❌ Exit"):
            st.session_state.workout_status = "exit"

    # Show pause/exit messages
    if st.session_state.workout_status == "paused" and not st.session_state.pause_message_shown:
        st.warning("⏸ Workout Paused. Press Resume to continue.")
        st.session_state.pause_message_shown = True

    if st.session_state.workout_status == "exit":
        st.info("❌ Workout exited.")
        go_to("schedule_select") 

    result = None
    try:
        ex_key = st.session_state.current_exercise_for_run
        kwargs = {
            "user_weight": st.session_state.weight,
            "video_path": st.session_state.video_path
        }
        val = st.session_state.current_target_value
        typ = st.session_state.current_target_type

        # find best match key in EXERCISE_MAP
        found_key = None
        for k in EXERCISE_MAP.keys():
            if k.lower() == ex_key.lower():
                found_key = k
                break
        if not found_key:
            for k in EXERCISE_MAP.keys():
                if k.lower() in ex_key.lower() or ex_key.lower() in k.lower():
                    found_key = k
                    break

        if not found_key:
            raise ValueError(f"Exercise '{ex_key}' not supported by EXERCISE_MAP")

        call_type, func = EXERCISE_MAP[found_key]

        if call_type == "reps":
            if val is None:
                val = st.session_state.get("target_reps", 10)
            kwargs["target_reps"] = val
            result = func(**kwargs)
        elif call_type == "time_seconds":
            if val is None:
                val = st.session_state.get("hold_time", 30)
            kwargs["target_seconds"] = val
            result = func(**kwargs)
        elif call_type == "time_seconds_pose":
            if val is None:  # fallback if parsing failed
              val = 30
            pose_name = found_key
            result = run_yoga_pose(user_weight=st.session_state.weight,
                           video_path=st.session_state.video_path,
                           target_time=val,
                           pose_name=pose_name)
    
        # elif call_type == "time_seconds_pose":
        #     if val is None:
        #         val = st.session_state.get("hold_time", 30)
        #     pose_name = found_key
        #     result = run_yoga_pose(user_weight=st.session_state.weight, video_path=st.session_state.video_path, target_time=val, pose_name=pose_name)
        else:
            result = func(user_weight=st.session_state.weight, video_path=st.session_state.video_path)
    except Exception as e:
        st.error(f"Error running scheduled workout: {e}")
        result = {"status": "Failed", "error": str(e)}

    result = result or {"status": "Failed"}
    metadata = {
        "exercise": st.session_state.current_exercise_for_run,
        "target_value": st.session_state.current_target_value,
        "target_type": st.session_state.current_target_type,
        "day": st.session_state.schedule_day,
        "level": st.session_state.schedule_level,
        "timestamp": datetime.datetime.now().isoformat()
    }
    if isinstance(result, dict):
        result.update(metadata)
    st.session_state.results.append(result)
    st.session_state.history.append(result)

    # update daily accumulators
    calories = result.get("calories", 0) if isinstance(result, dict) else 0
    st.session_state.daily_calories = st.session_state.get("daily_calories", 0) + (calories or 0)
    st.session_state.daily_completed = st.session_state.get("daily_completed", []) + [st.session_state.current_schedule_item]

    # go to scheduled result page
    go_to("scheduled_result")

# SCHEDULED RESULT PAGE (custom result for scheduled flows)
elif st.session_state.page == "scheduled_result":
    res = st.session_state.history[-1] if st.session_state.history else {}
    st.title("✅ Exercise Completed (Scheduled)")
    st.write(f"**DAY:** {st.session_state.schedule_day}  |  **PLAN:** {st.session_state.schedule_level}")
    ex_name = res.get("exercise", st.session_state.current_exercise_for_run)
    st.write(f"**Exercise:** {ex_name}")

    target_v = st.session_state.get("current_target_value")
    target_t = st.session_state.get("current_target_type")
    if target_v and target_t:
        if target_t == "seconds":
            st.write(f"**Target Hold Time:** {target_v} seconds")
        else:
            st.write(f"**Target Repetitions:** {target_v}")

    if isinstance(res, dict):
        if 'reps' in res:
            st.write(f"**Reps counted:** {res['reps']}")
        if 'time' in res:
            st.write(f"**Time recorded:** {res['time']} seconds")
        if 'calories' in res:
            st.write(f"**Calories Burned:** {res['calories']} cal")

    remaining = st.session_state.get("schedule_queue") or []
    if remaining:
        st.subheader("📝 Remaining exercises for today")
        for i, r in enumerate(remaining, 1):
            st.write(f"{i}. {r}")
    else:
        st.info("No remaining exercises for today.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if remaining and st.button("✅ Next Exercise"):
            # run_schedule will pop next item and then show announcement
            go_to("run_schedule")
    with col2:
        if remaining and st.button("⏭️ Skip This Exercise"):
            # skip current (already popped), continue to next
            go_to("run_schedule")
    with col3:
        if st.button("🏁 Finish Day"):
            # will take to run_schedule which detects empty queue
            st.session_state.schedule_queue = []
            go_to("run_schedule")

# MANUAL RESULT PAGE
elif st.session_state.page == "result_manual":
    result = st.session_state.history[-1] if st.session_state.history else {}
    st.title("✅ Workout Completed (Manual)")
    if isinstance(result, dict) and result.get("status") == "Success":
        st.success("Great job! You completed your workout.")
        if 'reps' in result:
            st.write(f"Repetitions: {result['reps']}")
        if 'calories' in result:
            st.write(f"Calories Burned: {result['calories']} cal")
        if 'time' in result:
            st.write(f"Hold Time: {result['time']} seconds")
    else:
        st.error("Workout failed or returned no result.")

    if st.button("Do another workout (manual)"):
        go_to("select")
    if st.button("Back to Welcome"):
        go_to("welcome")

# RESULT HISTORY
elif st.session_state.page == "result_history":
    st.title("📚 Workout History")
    history = st.session_state.get("history", [])
    if not history:
        st.info("No workouts yet.")
    else:
        for i, item in enumerate(history[::-1], 1):
            st.markdown(f"### Session {i}")
            st.write(item)
            st.divider()
    if st.button("Back"):
        go_to("welcome")

# Fallback
else:
    st.write("Unknown page. Returning to welcome.")
    go_to("welcome")

