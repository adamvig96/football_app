#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import requests
import pandas as pd
import networkx as nx
import pyvis

from pyvis.network import Network


# In[6]:


match_url = "https://borza-hotelcom-data.s3.eu-central-1.amazonaws.com/whoscored-match-1376105.json"


# In[7]:


dic = json.loads(requests.get(match_url).content)


# # Adatmaszírozás

# In[8]:


match_title = (
    f'{dic["home"]["name"]} {dic["score"]} {dic["away"]["name"]}'
)


# In[9]:


passes = []
for i in range(len(dic["events"])):
    if (
        dic["events"][i]["type"]["displayName"] == "Pass"
        and dic["events"][i]["outcomeType"]["displayName"] == "Successful"
        and dic["events"][i]["teamId"] == dic["events"][i + 1]["teamId"]
    ):
        dic["events"][i]["recieverId"] = dic["events"][i + 1]["playerId"]
        passes.append(dic["events"][i])

passes_df_big = pd.DataFrame(passes)

passes_df = passes_df_big[["playerId", "recieverId", "teamId"]]

passes_df["passes"] = "huh"

test_df = passes_df.groupby(["playerId", "recieverId", "teamId"]).count().reset_index()

test_df = test_df[test_df["playerId"] != test_df["recieverId"]].reset_index(drop=True)

test_df["color"] = test_df.apply(
    lambda x: "red" if x["teamId"] == dic["home"]["teamId"] else "blue", axis=1
)


# In[10]:


sub_1=passes_df_big[["playerId", "recieverId", "x", "y", 'endX', "endY"]]

sub_2=pd.DataFrame()

sub_2['playerId']=sub_1['recieverId']
sub_2['recieverId']=sub_1['playerId']
sub_2['x']=sub_1['endX']
sub_2['y']=sub_1['endY']
sub_2['endX']=sub_1['x']
sub_2['endY']=sub_1['y']

sub=pd.concat([sub_1,sub_2])

sub=sub.drop_duplicates(subset=['playerId'])

coordinates=sub[['playerId', 'x', 'y']]


# In[11]:


players = []
for i in dic["home"]["players"]:
    if i["playerId"] in list(test_df["playerId"]) or i["playerId"] in list(
        test_df["recieverId"]
    ):
        players.append(
            [
                i["playerId"],
                i["name"],
                i["shirtNo"],
                i["position"],
                i["height"],
                i["weight"],
                i["age"],
                i["stats"]["ratings"].popitem()[1],
            ]
        )
players = pd.DataFrame.from_records(players).rename(
    columns={
        0: "playerId",
        1: "playerName",
        2: "shirtNo",
        3: "position",
        4: "height",
        5: "weight",
        6: "age",
        7: "rating",
    }
)
home_players = players.copy()

players = []
for i in dic["away"]["players"]:
    if i["playerId"] in list(test_df["playerId"]) or i["playerId"] in list(
        test_df["recieverId"]
    ):
        players.append(
            [
                i["playerId"],
                i["name"],
                i["shirtNo"],
                i["position"],
                i["height"],
                i["weight"],
                i["age"],
                i["stats"]["ratings"].popitem()[1],
            ]
        )
players = pd.DataFrame.from_records(players).rename(
    columns={
        0: "playerId",
        1: "playerName",
        2: "shirtNo",
        3: "position",
        4: "height",
        5: "weight",
        6: "age",
        7: "rating",
    }
)
away_players = players

players = pd.concat([home_players, away_players]).reset_index().drop("index", axis=1)



# In[13]:


test_df["playerName"] = "huh"
test_df["recieverName"]= "huh"
for i in range(len(test_df["playerId"])):
    test_df["playerName"][i] = (
        players["playerName"]
        .loc[players["playerId"] == test_df["playerId"][i]]
        .reset_index(drop=True)[0]
    )
    test_df["recieverName"][i] = (
        players["playerName"]
        .loc[players["playerId"] == test_df["recieverId"][i]]
        .reset_index(drop=True)[0]
    )


# In[14]:


G = nx.DiGraph()
for i in range(1, (len(test_df))):
    G.add_edge(
        test_df.loc[i, "playerName"],
        test_df.loc[i, "recieverName"],
        weight=test_df.loc[i, "passes"],
    )

cc = nx.closeness_centrality(G, u=None, distance=None, wf_improved=False)
for i in list(cc.keys()):
    cc[i] = round(cc[i], 2)

CC_df = pd.DataFrame.from_dict(cc, orient="index", columns=["closeness centrality"])

players = players.merge(CC_df, how="left", left_on="playerName", right_index=True)
players = (
    pd.merge(players, test_df[["playerId", "color"]], how="left")
    .drop_duplicates()
    .reset_index(drop=True)
)
test_df = test_df.merge(CC_df, how="left", left_on="playerName", right_index=True)


# In[15]:


test_df=test_df.merge(coordinates)




# # háló


# ### csapat logók
#
# sevilla_logo  = "https://www.logofootball.net/wp-content/uploads/Sevilla-FC-Logo.png"
# espanyol_logo = "https://upload.wikimedia.org/wikipedia/en/thumb/d/d6/Rcd_espanyol_logo.svg/1200px-Rcd_espanyol_logo.svg.png"
#
# test_df['logo']=test_df.apply(lambda x: espanyol_logo if x['teamId']==70 else sevilla_logo, axis=1 )

# ### info táblák

# In[18]:


nev_lista = list(players["playerName"])
faszom = players.transpose().set_axis(nev_lista, axis=1, inplace=False).drop(index="playerName")
faszom=faszom.set_axis(list("<br>"+faszom.index+":"), axis=0, inplace=False).drop(["<br>playerId:"])


# In[19]:


key_list=list(faszom.index)
key_list[0] = "<br>shirt number:"


# In[20]:


info_dic = {}
for j in range(len(nev_lista)):
    global_shit=""
    value_list=list(faszom[nev_lista[j]])
    for i in range(len(key_list)):
        global_shit=global_shit+key_list[i]+" "+str(value_list[i])
        info_dic[nev_lista[j]]=global_shit


# ### hálógeneráló fgv

# In[21]:


def pass_net(df, height="800px", width="100%", name="team"):
    pass_net = Network(
        height=height,
        width=width,
        bgcolor="FFFFFF",
        font_color="black",
        directed=True,
        notebook=False,
    )
    pass_net.barnes_hut()
    sources = df["playerName"]
    targets = df["recieverName"]
    weights = df["passes"]
    size = 2*df["closeness centrality"]
    color = df["color"]

    edge_data = zip(sources, targets, weights, size, color)
    for e in edge_data:
        src = str(e[0])
        dst = str(e[1])
        w = e[2]
        s = e[3]
        c = e[4]
        pass_net.add_node(src, src, title=src, size=s, color=c)
        pass_net.add_node(dst, dst, title=dst, size=s, color=c)
        pass_net.add_edge(src, dst, value=w)
        neighbor_map = pass_net.get_adj_list()

    for node in pass_net.nodes:
        node["title"] += info_dic[node["title"]]
        node["value"] = len(neighbor_map[node["id"]])

    pass_net.set_options(
        """
    var options = {
      "nodes": {
        "borderWidth": 2,
        "color": {
          "highlight": {
            "background": "rgba(217,255,50,1)"
          }
        },
        "font": {
          "size": 50,
          "face": "tahoma"
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": false
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -80000,
          "springLength": 250,
          "springConstant": 0.001
        },
        "minVelocity": 0.75
      }
    }
    """
    )

    pass_net.show("pass_network_" + name + ".html")


# In[22]:


team_id_dic = {
   dic[v]["teamId"]: f"{v} - {dic[v]['name']}" for v in ["home", "away"]
}


# In[23]:


#team_1 = test_df.loc[test_df["teamId"] == list(team_id_dic.keys())[0]]

#pass_net(team_1,height="380px",name="team1")


# In[24]:


#team_2 = test_df.loc[test_df["teamId"] == list(team_id_dic.keys())[1]]

#pass_net(team_2,height="380px",name="team2")


# In[ ]:





# # Dash

# In[ ]:


import dash
import dash_html_components as html
import dash_core_components as dcc
from dash_html_components import Div, H3, H1, Link
import plotly.express as px

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = "Pass network"

app.scripts.config.serve_locally = True

# correl plot
fig = px.scatter(
    players,
    x="rating",
    y="closeness centrality",
    trendline="ols",
    hover_name="playerName",
)
fig.update_layout(title_text="Closeness centrality and rating of players")

#layout
app.layout = html.Div(
    children=[
        H1(
            children=f"{match_title} pass network",
            style={
                "color": "black",
                "backgroundColor": "ffffff",
                "text-align": "center",
            },
        ),
        html.Div(
            children=[
                html.H3(children="blablabla", className="six columns"),
                html.Div(
                    html.Iframe(
                        srcDoc=open("pass_network_team1.html").read(),
                        style={"height": "100%", "width": "100%"},
                    ),
                    style={"height": "400px"},
                    className="six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[dcc.Graph(id="correl-graph", figure=fig),],
                    className="six columns",
                ),
                html.Div(
                    html.Iframe(
                        srcDoc=open("pass_network_team2.html").read(),
                        style={"height": "100%", "width": "100%"},
                    ),
                    style={"height": "400px"},
                    className="six columns",
                ),
            ],
            className="row",
        ),
    ]
)


server = app.server

if __name__ == "__main__":

    app.run_server(debug=True)
