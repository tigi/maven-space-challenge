# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 15:02:03 2022

@author: vraag
"""

import pandas as pd
import dash
from dash import dcc
from dash import html

import plotly.express as px
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np
import statsmodels.api as sm #for the trendline?

#EXTRACT AND TRANSFORM
df_datadictionary = pd.read_csv("D:\\Studie\data-maven\maven-space-mission\Space+Missions\space_missions_data_dictionary.csv", encoding = "ISO-8859-1")
df_spacemissions_raw = pd.read_csv("D:\\Studie\data-maven\maven-space-mission\Space+Missions\space_missions.csv", encoding = "ISO-8859-1")
isoalpha = pd.read_excel("D:\\Studie\data-maven\maven-space-mission\Space+Missions\country_code_web.xls")


#making location string is enough to have the derived columns as stringtypes too##
df_spacemissions_raw = df_spacemissions_raw.astype({"Location": str}, errors='raise') 
#duplicates shows 1 duplicate record (4630 => 4629) and inspection shows it's a duplicate
df_spacemissions_raw = df_spacemissions_raw.drop_duplicates()
#duplicate location => location = where = better on map
#splitting location up in fields is only useful in plotly to map it to a map and
#the cleaned version of the data with country shows the hosting of launches by country.

df_spacemissions_raw['Location raw'] = df_spacemissions_raw.loc[:, 'Location']


#Russia Query#
#df_khazakhstanshit = df_spacemissions_raw.query('(Location.str.contains("Kazakh")) and (Date < "1991-12-16")')

#if < than Russia else Kazakhstan #

locationsplit=pd.DataFrame()
locationsplit[['Space Centersum','Country']]= df_spacemissions_raw['Location'].str.rsplit(',', n=1, expand=True)
locationsplit[['Launch site','Space Center','State','raar']]= locationsplit['Space Centersum'].str.split(',',  expand=True)



missions_sep_location = pd.merge(df_spacemissions_raw,locationsplit, left_index=True, right_index=True)
#splitting is done, remove location and Space Centersum
missions_data = missions_sep_location.drop(columns=['Location', 'Space Centersum'])

#it's a big vague when something is a str type or not after splitting.
#but they need to be strings to let the strip spaces work.

missions_data = missions_data.astype({"Launch site": str}, errors='raise') 
missions_data = missions_data.astype({"Space Center": str}, errors='raise') 
missions_data = missions_data.astype({"State": str}, errors='raise') 
missions_data = missions_data.astype({"Country": str}, errors='raise') 
missions_data = missions_data.astype({"raar": str}, errors='raise') 

#trim all string values in columns of type str.

missions_data[missions_data.columns] = missions_data.apply(lambda x: x.str.strip())


#USSR => 26 december 1991 (Russia)
#fix kodiak - alaska - USA => remove kodiak(city), column "raar" can be dropped after this action. 
#discovered by split expand, more columns than I thought.

missions_data.loc[(missions_data.raar == "Alaska"), ('State')] = missions_data['raar']

#fix Kazakhstan, before dec. 1991 was part of Russia, afterwards "Kazakhstan" as a republic. 
# step 1: if country = kazakhstan, set State kazakhstan
missions_data.loc[(missions_data.Country.str.contains("Kazakhstan")) ,'State'] = 'Kazakhstan'
#step 2: if state = kazakhstan and before 1-12-1991, set country = russia
missions_data.loc[(missions_data.State.str.contains("Kazakhstan")) & (missions_data.Date < "1991-12-16"),'Country'] = 'Russia'

#fix yellow sea as country, according to Google the launches are in China, only 3 records
missions_data.loc[(missions_data.Country.str.contains("Yellow")) ,'State'] = 'Yellow Sea'
missions_data.loc[(missions_data.State.str.contains("Yellow")) ,'Country'] = 'Yellow Sea'
#Shahrud Missile Test Site is Iran
missions_data.loc[(missions_data.Country.str.contains("Shahrud Missile Test Site")) ,'Space Center'] = 'Shahrud Missile Test Site'
missions_data.loc[(missions_data.Country.str.contains("Shahrud Missile Test Site")) ,'Country'] = 'Iran'
#Barents Sea Launch Area according to Google used by Russia
missions_data.loc[(missions_data.Country.str.contains("Barents Sea")) ,'State'] = 'Barents Sea'
missions_data.loc[(missions_data.Country.str.contains("Barents Sea")) ,'Country'] = 'Barents Sea'
#Pacific Missile Range Facility is Kaui, Hawai, USA => assign it to USA as initiator
missions_data.loc[(missions_data.Country.str.contains("Pacific Missile Range Facility")) ,'State'] = 'Hawai'
missions_data.loc[(missions_data.Country.str.contains("Pacific Missile Range Facility")) ,'Space Center'] = 'Pacific Missile Range Facility'
missions_data.loc[(missions_data.Country.str.contains("Pacific Missile Range Facility")) ,'Country'] = 'USA'
#country is Gran Canaria => state is GC and country is spain
missions_data.loc[(missions_data.Country.str.contains("Gran Canaria")) ,'State'] = 'Gran Canaria'
missions_data.loc[(missions_data.Country.str.contains("Gran Canaria")) ,'Country'] = 'Spain'
#country is New Mexico => state is NM and country is usa
missions_data.loc[(missions_data.Country.str.contains("New Mexico")) ,'State'] = 'New Mexico'
missions_data.loc[(missions_data.Country.str.contains("New Mexico")) ,'Country'] = 'USA'
#to get french guiana mapped correctly
#missions_data.loc[(missions_data.State.str.contains("French Guiana")) ,'Country'] = 'French Guiana'
#algeria
#missions_data.loc[(missions_data.State.str.contains("Algeria")) ,'Country'] = 'Algeria'

#The pacific ocean as a country is special, it's a launch location used by more companies from more countriesand
#does not belong to somebody. To make water launched comparable state is also pacific ocean
missions_data.loc[(missions_data.Country.str.contains("Pacific Ocean")) ,'State'] = 'Pacific Ocean'

#a significant amount of records has spacecenter as launch site and None as value for space center
missions_data.loc[(missions_data["Launch site"].str.contains("Center")) & (missions_data["Space Center"]=="None") ,'Space Center'] = missions_data["Launch site"]

#PowerBI loves the current country more so French Guinia, French becomes French Guinia, French Guinia
missions_data['Location raw'].str.replace("French Guiana, France", "French Guiana, French Guiana")

#only contained a few misplaced values, can be dropped.
mission_data_final = missions_data.drop(columns=['raar'])

##if I want to make a bubble diagram I have to use iso_alpha 2 or 3.
##I can not join on Country because sometimes it's the Country value that matches
##sometimes it's the code, let's do a loop know and make me more flexible 
##in the long run. The laptop has no problems with the dataframesize.
##let's follow a stackflow example, dat lukt niet zo dan een loopje


mission_data_final["Iso Alpha"] = None

country_arr = isoalpha[["Country","Alpha-3 code"]].to_numpy()


for index, row in mission_data_final.iterrows():

    isoindex =np.where(row["Country"] == country_arr )
    resultaat = country_arr[isoindex[0]]
    row["Iso Alpha"]=resultaat[0,1]

 

#CALCULATING DATAFRAMES TO DISPLAY ON SCREEN.#

total_launches = mission_data_final.count()
total_launches_success = mission_data_final.query("MissionStatus == 'Success'").shape[0]
total_launches_nosuccess = mission_data_final.query("MissionStatus != 'Success'").shape[0]

total_spacecenters_distinct = mission_data_final["Space Center"].nunique()
countrywater=("Pacific Ocean","Barents Sea","Yellow Sea")
#distinct values in a column, dit moet handiger kunnen
total_countries_distinct_water = mission_data_final.query("Country in @countrywater").nunique()
total_countries_distinct_land = mission_data_final.query("Country not in @countrywater").nunique()


#launches per country
missions_per_country = mission_data_final.groupby("Country").agg({"Mission":"count"}).sort_values(by="Mission", ascending=False).reset_index()
top10countrylist=missions_per_country["Country"].head(5)
missions_per_country_iso = mission_data_final.groupby("Iso Alpha").agg({"Mission":"count"}).sort_values(by="Mission", ascending=False).reset_index()



#launches per year
missions_per_year = mission_data_final.groupby([pd.to_datetime(mission_data_final['Date']).dt.year]).agg({"Mission":"count"}).reset_index()
#launches per year, status
missions_per_year_status = mission_data_final.groupby([pd.to_datetime(mission_data_final['Date']).dt.year, mission_data_final["MissionStatus"]]).agg({"Mission":"count"}).reset_index()
#succespercentage per year
missions_per_year_successperc = missions_per_year_status.loc[missions_per_year_status["MissionStatus"] == "Success"].join(missions_per_year, on="Date", how='left',lsuffix="_left")


#launches per year-country
missions_per_year_country = mission_data_final.groupby([pd.to_datetime(mission_data_final['Date']).dt.year, "Country"]).agg({"Mission":"count"})

#growth per year country = this year - previous year/ previous year

missions_per_year_country["Growth"] = missions_per_year_country.sort_values(["Country","Date"]).groupby('Country')["Mission"].pct_change().fillna('0')


#df.loc[str(int(index) - 1), 'S'], moet echt met een shift
missions_per_year_country["Alltimetotal"] = 0

missions_per_year_country_sorted = missions_per_year_country.sort_values(["Country","Date"]).reset_index()

#if you would visualize the above as cumulative over the years there are missing records for all time total if a country does nothing during
#the year.Like China in 2008, 2009 and it's 2007 alltimetotal is'nt counted for those years which creates a gap in the graph.



#ACCUMULATIVE PER COUNTRY PER YEAR

prev_country = ''
df_temp = pd.DataFrame(columns = ['Date', 'Country', 'Mission','Growth','Alltimetotal'])
my_dict = {'the_key': 'the_value'}
for index, row in missions_per_year_country_sorted.iterrows():

   if row['Country'] != prev_country and row['Alltimetotal'] == 0:
       #we change countries and start a new sequence or first row
       if row['Alltimetotal'] == 0:
           ##this is the first record for a country, start counting
           missions_per_year_country_sorted.loc[index,"Alltimetotal"] = row['Mission']
       #has the sequence for the previous country ended properly?
       if index > 1: 
           if missions_per_year_country_sorted.loc[index-1,"Date"] != 2022:
               #fill it tup
               rangebottoma = missions_per_year_country_sorted.loc[index-1,"Date"] +1
               for y in range(rangebottoma,2023):
                    for key in my_dict:
                       concatrow = {'Date' : y ,'Country' : missions_per_year_country_sorted.loc[index-1,"Country"], 'Mission' : 0,'Growth':0,'Alltimetotal':missions_per_year_country_sorted.loc[index-1,"Alltimetotal"]}
                       df_temp = pd.concat([df_temp,pd.DataFrame(concatrow, index=[key])], axis=0, ignore_index=True)

               

   else:
       #processing the rest of the records. Missing rows will be added to a second temp
       #df to merge later but to not disturb this process.
       #if a year-country row is missing in the sequence one or more rows will be appended
       #to the temp df with country, mission=0, alltime = last one from this one.
       #is this a gap? Check if the previous record was the previous year.
       if row['Date'] - missions_per_year_country_sorted.loc[index-1,"Date"] != 1:
           rangebottom = missions_per_year_country_sorted.loc[index-1,"Date"] +1
           rangetop = row['Date']
           for x in range(rangebottom, rangetop):
               for key in my_dict:
                   concatrow = {'Date' : x ,'Country' : row["Country"], 'Mission' : 0,'Growth':0,'Alltimetotal':missions_per_year_country_sorted.loc[index-1,"Alltimetotal"]}
                   df_temp = pd.concat([df_temp,pd.DataFrame(concatrow, index=[key])], axis=0, ignore_index=True)
           
       missions_per_year_country_sorted.loc[index,"Alltimetotal"] = row['Mission']  + missions_per_year_country_sorted.loc[index-1,"Alltimetotal"]


   prev_country = row['Country']


missions_cumulative_total= pd.concat([missions_per_year_country_sorted, df_temp], ignore_index=True, sort=False)

#FIRST AND LAST Launch, YEARS ACTIVE.
#np.ptp has a problem with one lauch, spain, 1997 => years active 0

missions_min_max_year = missions_per_year_country_sorted.groupby("Country").agg({"Date": ['min', 'max',np.ptp]})

#RUSSIA & KAZAKHSTA

all_russian_missions = mission_data_final.loc[(mission_data_final["Country"] == "Russia") | (mission_data_final["Country"] == "Kazakhstan")]
russian_missions_per_spacecenter=all_russian_missions.groupby(["Country", "State","Space Center", "Company"]).agg({"Mission":"count"})

#watery missions, location is sea, ocan

all_watery_missions= mission_data_final.loc[(mission_data_final.State.str.contains("Ocean")) | (mission_data_final.State.str.contains("Sea"))]


#distribution over months, time isna 127 out of 4000+
missions_per_month = mission_data_final.groupby([pd.to_datetime(mission_data_final['Date']).dt.month]).agg({"Mission":"count"})
missions_per_time = mission_data_final.groupby([pd.to_datetime(mission_data_final['Time']).dt.hour]).agg({"Mission":"count"}).reset_index()

#cleaned data
mission_data_final.to_csv("D:\\Studie\data-maven\maven-space-mission\Space+Missions\evenkieke2.csv")
#totals per country per year.
missions_cumulative_total.to_csv("D:\\Studie\data-maven\maven-space-mission\Space+Missions\missions_cumulative_total.csv")
#about activity
missions_min_max_year.to_csv("D:\\Studie\data-maven\maven-space-mission\Space+Missions\missions_min_max_range.csv")


distinct_spacecenters_year = mission_data_final.sort_values(by="Date").groupby([pd.to_datetime(mission_data_final['Date']).dt.year]).agg({"Space Center": pd.Series.nunique}).reset_index()
distinct_spacecenters_country_year = mission_data_final.sort_values(by="Date").groupby([pd.to_datetime(mission_data_final['Date']).dt.year, "Country"]).agg({"Space Center": pd.Series.nunique}).reset_index()


distinct_companies_year = mission_data_final.sort_values(by="Date").groupby([pd.to_datetime(mission_data_final['Date']).dt.year]).agg({"Company": pd.Series.nunique}).reset_index()




#some generic functions and styledefinitions, some css is added in /assets
#and is automatically loaded. Maybe putting everything in there would be better
#otherwise css below overrides the css file(s) as inline css, hence !important

def style_h3():
    layout_style={'textAlign': 'center'}
    return layout_style

def style_h2():
    layout_style={'textAlign': 'center'}
    return layout_style

def style_radiobuttons():
    layout_style={'display':'block','background-color': 'orange',
    'padding': '10px 5px',
    'border-radius': '4px',
    'margin': '4px',
    'cursor':'pointer'}
    return layout_style



################### PLOTLY DEFINITIONS#######################################

used_color_discrete_map={"USA": "#12B0FB","China": "#FF0000","Russia": "white","France": "#FFCC00"}
size = [20, 40, 60, 80, 100, 80, 60, 40, 20, 40]

def bar_chart_missionsuccess():
    alldata = missions_per_year_status.copy(deep=True)
    bar_chart_missionsuccess=px.bar(alldata, x='Date', y='Mission', text_auto='.2s',height=600,color="MissionStatus")
    return  bar_chart_missionsuccess


def bar_chart_past_cumulative():
    countrylist=("China","USA","Russia","France")
    alldata = missions_cumulative_total.query("Country.isin(@countrylist)").copy(deep=True)
    bar_chart_past_cumulative = px.bar(alldata, x='Date', y='Alltimetotal',hover_data=['Mission', 'Growth'], color='Country', color_discrete_map=used_color_discrete_map, labels=None,height=300, template="plotly_dark")
    bar_chart_past_cumulative.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
        
))
 
    return bar_chart_past_cumulative

def bar_chart_distinct_center_country_year():
    countrylist=("China","USA","Russia","France")
    alldata = distinct_spacecenters_country_year.query("Country.isin(@countrylist) and Date > 2016").copy(deep=True)
    bar_chart_distinct_center_country_year = px.bar(alldata, x='Date', y='Space Center', color = "Country",height=300,
                                                   color_discrete_map=used_color_discrete_map, template="plotly_dark")
    bar_chart_distinct_center_country_year.update_layout(barmode='group')
    bar_chart_distinct_center_country_year.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
        
))
    return bar_chart_distinct_center_country_year


def bar_missions_per_time():
    alldata = missions_per_time.sort_values(by="Time", ascending=True).copy(deep=True)   
    bar_chart_missions_time = px.bar(alldata, x="Time", y="Mission", template="plotly_dark")                           
    return bar_chart_missions_time

def map_missions_country_iso():
    alldata = missions_per_country_iso.sort_values("Mission").copy(deep=True)
    map_missions_country_iso = px.scatter_geo(alldata, locations="Iso Alpha", 
                     hover_name="Iso Alpha", size="Mission", color_discrete_map=used_color_discrete_map,
                     projection="natural earth")    
                             
    return map_missions_country_iso

def line_distinct_spacecenters():
    alldata = distinct_spacecenters_year.copy(deep=True)
    line_distinct_spacecenters = px.scatter(alldata, x="Date", y="Space Center", title=None ,trendline="ols",height=300, template="plotly_dark")  
                            
    return line_distinct_spacecenters  
 
def line_distinct_companies():
    alldata = distinct_companies_year.copy(deep=True)
    line_distinct_companies  = px.scatter(alldata, x="Date", y="Company", title=None,trendline="ols",height=300, template="plotly_dark")                              
    return line_distinct_companies 



#DASH LAYOUT

app=dash.Dash()
#load css bootstrap 5:
app = dash.Dash(external_stylesheets=[
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css',
     dbc.themes.CYBORG
])

app.layout = dbc.Container([
        
    dbc.Row([
        dbc.Col([      
            html.H1(children='A SHORT HISTORY OF SPACE CENTERS USED FOR SPACE MISSIONS (1957-AUG 2022)'),
            ],width=12),  
     ]),
    
    dbc.Row([
        dbc.Col([      
            html.H2(children='Summary',style=style_h2()),
            html.Div([
                html.Div([
                    html.H3(children='Space centers involved'),
                    html.P(f'{total_spacecenters_distinct}',className='card-summary-detail'),
                ],className="card-summary"),
                html.Div([
                    html.H3(children='Launches accomodated'),
                    #2 columns, right one has 2 rows for succes and failure
                    dbc.Row([
                    dbc.Col([
                        html.P(f'{total_launches["Mission"]}',className='card-summary-detail'),                        
                    ],width=6),
                    dbc.Col([
                        html.I(className="fa fa-thumbs-up  green"),
                        html.Span(f'{total_launches_success}'),
                        html.Br(),
                        html.I(className="fa fa-thumbs-down  red"),
                        html.Span(f'{total_launches_nosuccess}'),                       
                    ],width=6,className="card-summary-detail-zoom"),
                    ],className="card-summary-zoom"),                  
                ],className="card-summary"),

                html.Div([
                    html.H3(children='Countries hosting launches'),
                    dbc.Row([
                        dbc.Col([
                            html.P(f'{total_countries_distinct_land["Country"]}',className='card-summary-detail ditch_margins'),
                        ],width=6),
                        dbc.Col([
                            html.I(className="fa fa-tint  blue"),
                        html.Span(f'{total_countries_distinct_water["Country"]}',className='card-summary-detail'),
                        ],width=6),
                    ],className="card-summary-zoom"),
                    html.Br(),
                    html.H4('On countries and aqueous launch locations'),
                    html.P('The Pacific Ocean, Barents Sea and Yellow Sea are also mentioned as launching areas. Without mentioning a country it is not possible to assign a country to the launch location. ') ,       
                    html.Br(),
                    html.P('Although from an intuitive point of view the Barents Sea launches were probably done in the Russia part of this sea, logically it could have been the Norwegian part either. If the latter was the case the number of countries would increase because Norway has no used Space Centers for mission launches.'),
                ],className="card-summary"),
            
                ],className="column-summary")
            ],width=4),
        dbc.Col([
            html.H2(children='The past',style=style_h2()),
            html.Div([
                
               # dcc.Graph(id = 'map_missions_country_iso',figure=map_missions_country_iso()),
               html.Div([
                   html.H3(children='Number of space centers used'),
                   dcc.Graph(id = 'bar_chart_distinct_center_country_year',figure=bar_chart_distinct_center_country_year()),
                ],className="card-summary"),
                html.Div([
                    html.H3(children='Key insight', className="white"),
                    html.P('Although it is undeniable that Russia/USSR and the USA have dominated in tercms of the number of missions and space centres since the start, it seems that China is an emerging power when it comes to the number of space missions.'),
                    html.P('In the period 2017-2021 the total number of space missions accomplished from locations in China almost doubled. Apparently capacity is not the problem since the number of locations '),
                ],className="card-summary white"),
                html.Div([
                    html.H3(children='All time total launches'),
                    dcc.Graph(id = 'bar_chart_past_cumulative',figure=bar_chart_past_cumulative()) 
                ],className="card-summary"),
            ],className="column-past")
        ],width=4),
        dbc.Col([
            html.H2(children='The future',style=style_h2()),
            html.Div([
                html.Div([
                    html.H3(children='Trend used space centers a year'),
                    dcc.Graph(id = 'line_distinct_spacecenters',figure=line_distinct_spacecenters()), 
                ],className="card-summary"),
                html.Div([
                    html.H3(children='The future from a logical perspective', className="white"),
                    html.P('The trendlines for both the number of space centers in use per year and the number of active companies show a gradual increase. If nothing extreme happens this is very probable. The number of companies is important because commercial space missions have entered the arena.', className="white"),
                    html.H3(children='The future based on intuition', className="white"),
                    html.P('If you have experienced the "Cold war", the situation in the world with increasing climate, energy, war and poverty problems can make you think something extreme could easily happen. This makes the value of extrapolating trendlines or forecasts to the future very tricky, not to say unreliable.' , className="white"),
                ],className="card-summary"),
                    html.Div([                              
                        html.H3(children='Trend involved companies launch'),
                dcc.Graph(id = 'line_distinct_companies',figure=line_distinct_companies()),
                ],className="card-summary"),
            ],className="column-future")
            ],width=4),    
    ]),  
    
],
)

if __name__== '__main__':
    app.run_server()
    
    
