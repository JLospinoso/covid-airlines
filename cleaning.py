import csv
import itertools
import pandas as pd
import datetime
import networkx as nx


def get_state_lookup(path="states.csv"):
    return {x['State']: x['Code'] for x in csv.DictReader(open(path))}


def get_vaccinations(path="vaccinations.csv"):
    return csv.DictReader(open(path))


def get_cases(path="cases.csv"):
    return csv.DictReader(open(path))


def get_airline(path="airlines.csv"):
    return csv.DictReader(open(path))


def get_population(path="state-population.csv"):
    return csv.DictReader(open(path))

def get_quarter(x):
    if x < 4:
        return 1
    if x < 7:
        return 2
    if x < 10:
        return 3
    return 4


def format_str_to_int(x):
    if x == '':
        return 0
    return int(x.replace(',', ''))


def format_str_to_float(x):
    if x == '':
        return 0
    return float(x.replace(',', ''))


def get_lagged_lookup_key(x):
    year, quarter, state = x[0:3]
    if quarter == 1:
        quarter = 4
        year -= 1
    else:
        quarter -= 1
    return year, quarter, state


state = get_state_lookup()
states = state.values()

populations = {}
for entry in get_population():
    abbrev = state.get(entry['State'][1:])
    if not abbrev:
        print(f"Warning: Skipping locale f{entry['State']}")
        continue
    pop_2020 = format_str_to_int(entry['2020'])
    pop_2021 = format_str_to_int(entry['2021'])
    increment = (pop_2021 - pop_2020) / 4
    offset = 0
    for year, quarter in itertools.product([2020, 2021], [1, 2, 3, 4]):
        populations[(year, quarter, abbrev)] = {
            'year': year,
            'quarter': quarter,
            'state': abbrev,
            'population': int(pop_2020 + offset)
        }
        offset += increment

populations_df = pd.DataFrame(populations.values())
with open('populations-out.csv', 'w') as f:
    populations_df.to_csv(f)

cases = {x: {
    'year': x[0],
    'quarter': x[1],
    'state': x[2],
    'n_deaths': 0,
    'n_cases': 0
} for x in itertools.product([2020, 2021], [1, 2, 3, 4], states)}


for entry in get_cases():
    state = entry['state']
    if state not in states:
        continue
    date = datetime.datetime.strptime(entry['submission_date'], '%m/%d/%Y')
    year = date.year
    if date.month == 3:
        quarter = 1
    elif date.month == 6:
        quarter = 2
    elif date.month == 9:
        quarter = 3
    elif date.month == 12:
        quarter = 4
    else:
        continue
    key = (year, quarter, state)
    deaths = format_str_to_int(entry['tot_death'])
    cases[key]['n_deaths'] += deaths
    n_cases = format_str_to_int(entry['tot_cases'])
    cases[key]['n_cases'] += n_cases

for key in cases:
    lagged = get_lagged_lookup_key(key)
    if lagged not in cases:
        continue
    cases[key]['increase_deaths'] = cases[key]['n_deaths'] - cases[lagged]['n_deaths']
    cases[key]['increase_cases'] = cases[key]['n_cases'] - cases[lagged]['n_cases']

cases_df = pd.DataFrame(cases.values())
with open('cases-out.csv', 'w') as f:
    cases_df.to_csv(f)


vaccinations = {x: {
    'year': x[0],
    'quarter': x[1],
    'state': x[2],
    'n_vaccinated': 0,
    'n_fully_vaccinated': 0
} for x in itertools.product([2020, 2021], [1, 2, 3, 4], states)}

for entry in get_vaccinations():
    state = entry['Location']
    if state not in states:
        continue
    date = datetime.datetime.strptime(entry['Date'], '%m/%d/%Y')
    year = date.year
    if date.month == 3:
        quarter = 1
    elif date.month == 6:
        quarter = 2
    elif date.month == 9:
        quarter = 3
    elif date.month == 12:
        quarter = 4
    else:
        continue
    key = (year, quarter, state)
    fully_vaccinated = format_str_to_int(entry['Series_Complete_Cumulative'])
    vaccinations[key]['n_fully_vaccinated'] = fully_vaccinated
    dose_1 = format_str_to_int(entry['Admin_Dose_1_Cumulative'])
    vaccinations[key]['n_vaccinated'] = dose_1


vaccinations_df = pd.DataFrame(vaccinations.values())
with open('vaccinations-out.csv', 'w') as f:
    vaccinations_df.to_csv(f)

travel = {x: {
    'year': x[0],
    'quarter': x[1],
    'source': x[2],
    'dest': x[3],
    'passengers_per_day': 0
} for x in itertools.product([2020, 2021], [1, 2, 3, 4], states, states) if x[2] != x[3]}


def parse_state_code(x):
    return x[-22:-20] if x.endswith('Area)') else x[-2:]


ignored = 0
ignored_passengers = 0
for entry in get_airline():
    source = parse_state_code(entry['city1'])
    dest = parse_state_code(entry['city2'])
    year = format_str_to_int(entry['Year'])
    quarter = format_str_to_int(entry['quarter'])
    key = (year, quarter, source, dest)
    passengers = format_str_to_int(entry['passengers'])
    if key in travel:
        travel[key]['passengers_per_day'] += passengers
    else:
        ignored += 1
        ignored_passengers += passengers
        if year in [2020, 2021] and source != dest:
            print(f'Warning: Ignoring {source} -> {dest}')
print(f'Ignored {ignored} airline travel reports totaling {ignored_passengers} passengers.')

travel_data_df = pd.DataFrame(travel.values())
with open('travel-out.csv', 'w') as f:
    travel_data_df.to_csv(f)

graphs = {}
centralities = {}
for year, quarter in itertools.product([2020, 2021], [1, 2, 3, 4]):
    graphs[(year, quarter)] = nx.DiGraph()
    graphs[(year, quarter)].add_nodes_from(states)
    for i, j in itertools.product(states, states):
        if i == j or travel[(year, quarter, i, j)]['passengers_per_day'] <= 0:
            continue
        weight = travel[(year, quarter, i, j)]['passengers_per_day']
        graphs[(year, quarter)].add_edge(i, j, weight=weight)
    ev_centrality = nx.eigenvector_centrality(graphs[(year, quarter)], weight='weight', max_iter=100000)
    between = nx.betweenness_centrality(graphs[(year, quarter)], weight='weight')

    for state in states:
        centralities[(year, quarter, state)] = {
            "year": year,
            "quarter": quarter,
            "state": state,
            "eigenvector": ev_centrality[state],
            "betweenness": between[state]
        }
centralities_df = pd.DataFrame(centralities.values())
with open('centralities-out.csv', 'w') as f:
    centralities_df.to_csv(f)

panel = {x: {
    'year': x[0],
    'quarter': x[1],
    'state': x[2],
    'population': populations[x]['population'],
    'covid_cases': cases[x]['n_cases'],
    'covid_deaths': cases[x]['n_deaths'],
    'd_covid_cases': cases[x].get('increase_cases'),
    'd_covid_deaths': cases[x].get('increase_deaths'),
    'vaccinated': vaccinations[x]['n_vaccinated'],
    'fully_vaccinated': vaccinations[x]['n_fully_vaccinated'],
    'eigenvector_centrality': centralities[x]['eigenvector'],
    'betweenness_centrality': centralities[x]['betweenness'],
} for x in itertools.product([2020, 2021], [1, 2, 3, 4], states) if x[2]}


for entry in panel:
    destination = panel[entry]['state']
    panel[entry]['aggregate_inbound_cases'] = 0
    panel[entry]['aggregate_inbound_deaths'] = 0
    for source in states:
        if source == destination:
            continue
        key = (panel[entry]['year'], panel[entry]['quarter'], source, destination)
        passengers_from_source = travel[key]['passengers_per_day']
        alter_lookup_key = get_lagged_lookup_key(key)
        alter_panel = panel.get(alter_lookup_key)
        if not alter_panel or not alter_panel.get('d_covid_cases'):
            continue
        panel[entry]['aggregate_inbound_cases'] += passengers_from_source * alter_panel['d_covid_cases'] / alter_panel['population']
        panel[entry]['aggregate_inbound_deaths'] += passengers_from_source * alter_panel['d_covid_deaths'] / alter_panel['population']

panel_df = pd.DataFrame(panel.values())
with open('panel-out.csv', 'w') as f:
    panel_df.to_csv(f)

with pd.ExcelWriter('covid-airline.xlsx') as writer:
    cases_df.to_excel(writer, sheet_name='Cases')
    panel_df.to_excel(writer, sheet_name='Panel')
    populations_df.to_excel(writer, sheet_name='Populations')
    travel_data_df.to_excel(writer, sheet_name='Travel')
    vaccinations_df.to_excel(writer, sheet_name='Vaccinations')
    centralities_df.to_excel(writer, sheet_name='Centralities')

