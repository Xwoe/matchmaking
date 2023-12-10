import streamlit as st
import pandas as pd
from matchmaking import check_input, MatchMaking
from enum import Enum
from faker import Faker


DF_WIDTH = 300
DF_HEIGHT = 300
FAKE_DATA_LENGTH = 16


#################### Funcions ####################
def get_empty_df():
    return pd.DataFrame(
        columns=["player", "skill"],
    )


def run_optimization(df, teamsize):
    df_ = df.copy()
    my_mm = MatchMaking(df_, teamsize=teamsize)
    df_teams = my_mm.optimize()
    df_teams = df_teams.sort_values("team")
    df_teams = df_teams.set_index("player")
    return df_teams


def display_teams(df_teams):
    st.header("Results of matchmaking")
    col_1, col_2 = st.columns(2)
    for i, team in df_teams.groupby("team"):
        if i % 2 == 1:
            col = col_1
        else:
            col = col_2
        team_skill = team["skill"].mean()
        col.subheader(f"Team {i}")
        col.caption(f"average skill {team_skill:.2f}")
        team = team[["skill"]]
        col.dataframe(team)
    st.divider()
    return df_teams[["team", "skill"]]


def generate_fake_data():
    fakr = Faker()
    players = [fakr.user_name() for _ in range(FAKE_DATA_LENGTH)]
    skills = [round(fakr.random.uniform(800, 2200)) for _ in range(FAKE_DATA_LENGTH)]
    return pd.DataFrame({"player": players, "skill": skills})


def reset_session_dfs():
    st.session_state["edit_df"] = get_empty_df()
    st.session_state["df"] = get_empty_df()
    st.session_state["team_df"] = None
    st.session_state["uploaded_file"] = None


def on_upload_click():
    st.session_state["fake_data_loaded"] = False


################ Fake Data ################
def input_fake():
    reset_session_dfs()
    st.session_state["edit_df"] = st.session_state["fake_data"]
    st.session_state["df"] = st.session_state["fake_data"]
    st.session_state["fake_data_loaded"] = True


###################################################


st.title("Matchmaking")
st.caption("by [Xwoe](https://github.com/Xwoe/matchmaking)")
st.markdown(
    """
    A little matchmaking algorithm to create balanced teams based 
    on the players' skillratings. The app will try to put the players
    into teams such that the average skill of each team is more or less
    the same.
    
    You can either upload a csv file, which must contain these two columns:

    * the column `player` with the player names
    * the column `skill` with the player's skill rating as a number

    You can also enter the data manually in the table below or
    if you just want to try it out, click the **Load Example Data** button, choose a
    team size and let it run.
    """
)

# Initialization
if "max_team_size" not in st.session_state:
    st.session_state["max_team_size"] = 2

if "df_teams" not in st.session_state:
    st.session_state["df_teams"] = None

if "df" not in st.session_state:
    st.session_state["df"] = get_empty_df()

if "edit_df" not in st.session_state:
    st.session_state["edit_df"] = get_empty_df()  # st.session_state["df"]

if "fake_data" not in st.session_state:
    st.session_state["fake_data"] = generate_fake_data()

if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None

if "fake_data_loaded" not in st.session_state:
    st.session_state["fake_data_loaded"] = None

### Data Input Choice Buttons

## File uploader
st.session_state["uploaded_file"] = st.file_uploader(
    "Choose a file", on_change=on_upload_click
)
if (st.session_state["uploaded_file"] is not None) and (
    not st.session_state["fake_data_loaded"]
):
    # read csv
    try:
        df = pd.read_csv(st.session_state["uploaded_file"])
        err_msg = check_input(df)
        if err_msg:
            st.warning(err_msg)
        else:
            st.session_state["df"] = df
            st.session_state["edit_df"] = df

    except pd.errors.ParserError:
        st.warning("Invalid CSV file, could not parse")

## Example data button
if st.button(
    label="Load Example Data",
    type="secondary",
    use_container_width=False,
):
    input_fake()


st.session_state["df"] = st.data_editor(
    st.session_state["edit_df"],
    width=DF_WIDTH,
    height=DF_HEIGHT,
    use_container_width=False,
    hide_index=None,
    column_order=None,
    column_config=None,
    num_rows="dynamic",
    disabled=False,
    key=None,
    on_change=None,
    args=None,
    kwargs=None,
)

####### Teamsize Input ###########
num_players = st.session_state["df"].shape[0]
st.session_state["max_team_size"] = max([num_players // 2, 2])
### Team Size
tsize_label = "Team Size"
team_size = st.number_input(
    label=tsize_label,
    value=2,
    min_value=2,
    max_value=st.session_state["max_team_size"],
    step=1,
    format="%i",
    disabled=False,
    label_visibility="visible",
)

### Run optimization button
opti_label = "Run Matchmaking"
button_disabled = st.session_state["df"].empty or (team_size is None)
if st.button(
    label=opti_label,
    type="primary",
    disabled=button_disabled,
    use_container_width=False,
):
    err_msg = check_input(st.session_state["df"])
    if err_msg:
        st.warning(err_msg)
    else:
        df = st.session_state["df"]
        st.session_state["df_teams"] = run_optimization(df=df, teamsize=team_size)


def convert_df(df):
    return df[["skill", "team"]].to_csv().encode("utf-8")


if st.session_state["df_teams"] is not None:
    display_teams(st.session_state["df_teams"])
    csv = convert_df(st.session_state["df_teams"])

    st.download_button(
        label="Download teams as CSV",
        data=csv,
        file_name="teams.csv",
        mime="text/csv",
    )
