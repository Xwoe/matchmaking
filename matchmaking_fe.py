import streamlit as st
import pandas as pd
from matchmaking import check_input, MatchMaking


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


### File Uploader


df = pd.DataFrame()

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    # read csv
    df = pd.read_csv(uploaded_file)

    err_msg = check_input(df)
    if err_msg:
        st.warning(err_msg)
    else:
        st.session_state["input_field_visibility"] = "visible"
        st.session_state["input_field_disabled"] = False
        num_players = df.shape[0]
        # st.write(f"num players {num_players}")
        st.session_state["max_team_size"] = num_players // 2
        # st.write(df, width=500)
        st.dataframe(df, width=300, height=300)
else:
    st.warning("You need to upload a csvfile.")


### Team Size

tsize_label = "Team Size"
team_size = st.number_input(
    label=tsize_label,
    value=2,
    min_value=2,
    max_value=st.session_state["max_team_size"],
    step=1,
    format="%i",
    disabled=st.session_state["input_field_disabled"],
    label_visibility=st.session_state["input_field_visibility"],
)


def run_optimization(df, teamsize):
    my_mm = MatchMaking(df, teamsize=teamsize)
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


### Run optimization button

opti_label = "run matchmaking"
df_teams = None
button_disabled = df.empty or (team_size is None)
func_args = {"df": df, "teamsize": team_size}
if st.button(
    label=opti_label,
    type="primary",
    disabled=button_disabled,
    use_container_width=False,
):
    st.session_state["df_teams"] = run_optimization(df=df, teamsize=team_size)


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
