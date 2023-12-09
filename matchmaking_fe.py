import streamlit as st
import pandas as pd
from matchmaking import check_input, MatchMaking
from enum import Enum
from faker import Faker


class InputChoice(Enum):
    NADA = 1
    MANUAL = 2
    CSV = 3
    FAKE = 4


DF_WIDTH = 300
DF_HEIGHT = 300
FAKE_DATA_LENGTH = 16


#################### Funcions ####################


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


###################################################


st.title("Matchmaking")
st.markdown(
    """
    A little matchmaking algorithm to create balanced teams based 
    on the players' skillratings. It works for any team size. All you 
    need is a csv file, which contains:

    * the column `player` with the player names
    * the column `skill` with the player's skill rating as a number
        
    The skill rating has been evaluated with ranges around 500 - 2500. If you have 
    very small values and are getting problems, try multiplying your values by 1000.
    """
)

### init session state
# Initialization
if "input_field_hidden" not in st.session_state:
    st.session_state["input_field_visibility"] = "hidden"

if "input_field_disabled" not in st.session_state:
    st.session_state["input_field_disabled"] = True

if "max_team_size" not in st.session_state:
    st.session_state["max_team_size"] = 2

if "df_teams" not in st.session_state:
    st.session_state["df_teams"] = None

if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(
        columns=["player", "skill"],
        # dtype=[str, float]
    )

if "input_choice" not in st.session_state:
    st.session_state["input_choice"] = InputChoice.NADA

if "fake_data" not in st.session_state:
    st.session_state["fake_data"] = generate_fake_data()

if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None

### Data Input Choice Buttons

choice_col_1, choice_col_2, choice_col_3 = st.columns(3)

if choice_col_1.button(
    label="Load Example Data",
    type="primary",
    # disabled=button_disabled,
    use_container_width=False,
):
    st.session_state["input_choice"] = InputChoice.FAKE

if choice_col_2.button(
    label="Manual Data Input",
    type="primary",
    # disabled=button_disabled,
    use_container_width=False,
):
    st.session_state["input_choice"] = InputChoice.MANUAL

if choice_col_3.button(
    label="Upload CSV file",
    type="primary",
    # disabled=button_disabled,
    use_container_width=False,
):
    st.session_state["input_choice"] = InputChoice.CSV

################ CSV file upload ################
if st.session_state["input_choice"] == InputChoice.CSV:
    ### File Uploader
    st.session_state["uploaded_file"] = st.file_uploader("Choose a file")
    if st.session_state["uploaded_file"] is not None:
        # read csv
        df = pd.read_csv(st.session_state["uploaded_file"])
        err_msg = check_input(df)
        print(f"AFTER UPLOADING uploaded file {st.session_state.uploaded_file}")
        st.write(f"df shape in csv ", df.shape)
        if err_msg:
            print(f"err msg {err_msg}")
            st.warning(err_msg)
        else:
            print(f"else")
            st.session_state["df"] = df
            # st.dataframe(st.session_state["df"], width=DF_WIDTH, height=DF_HEIGHT)
    else:
        st.warning("You need to upload a csvfile.")
    print(f"uploaded file {st.session_state.uploaded_file}")
    print(f"csv df session state {st.session_state.df}")
    st.write("WTF2")

################ Manual Data Input ################
elif st.session_state["input_choice"] == InputChoice.MANUAL:
    ### Data Editor
    st.data_editor(
        st.session_state["df"],
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
    print(f"manual df session state {st.session_state.df}")

################ Fake Data ################
elif st.session_state["input_choice"] == InputChoice.FAKE:
    st.session_state["df"] = st.session_state["fake_data"]
    # st.dataframe(st.session_state["df"], width=DF_WIDTH, height=DF_HEIGHT)

st.write("INPUT CHOICe", st.session_state["input_choice"])
st.write("df shape", st.session_state["df"].shape)
print(f"outside df session state {st.session_state.df}")

if not st.session_state["df"].empty:
    st.dataframe(st.session_state["df"], width=DF_WIDTH, height=DF_HEIGHT)

if st.session_state["input_choice"] != InputChoice.NADA:
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
        disabled=False,  # st.session_state["input_field_disabled"],
        label_visibility="visible",  # st.session_state["input_field_visibility"],
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
        st.session_state["df_teams"] = run_optimization(
            df=st.session_state["df"], teamsize=team_size
        )


@st.cache_data
def convert_df(df):
    return df.to_csv().encode("utf-8")


if st.session_state["df_teams"] is not None:
    display_teams(st.session_state["df_teams"])
    csv = convert_df(st.session_state["df_teams"])

    st.download_button(
        label="Download teams as CSV",
        data=csv,
        file_name="teams.csv",
        mime="text/csv",
    )
