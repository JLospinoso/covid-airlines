import csv
import itertools
import pandas as pd
import datetime


def get_state_lookup(path="states.csv"):
    return {x['State']: x['Code'] for x in csv.DictReader(open(path))}


def get_vaccinations(path="vaccinations.csv"):
    return csv.DictReader(open(path))


def get_infections(path="infections.csv"):
    return csv.DictReader(open(path))


def get_airline(path="airlines.csv"):
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


state = get_state_lookup()
states = state.values()

infections = {x: {
    'year': x[0],
    'quarter': x[1],
    'state': x[2],
    'n_deaths': 0,
    'n_cases': 0,
    # 'population_size': 0
} for x in itertools.product([2020, 2021], [1, 2, 3, 4], states)}


for entry in get_infections():
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
    infections[key]['n_deaths'] += deaths
    n_cases = format_str_to_int(entry['tot_cases'])
    infections[key]['n_cases'] += n_cases

infections_df = pd.DataFrame(infections.values())

vaccinations = {x: {
    'year': x[0],
    'quarter': x[1],
    'state': x[2],
    'n_vaccinated': 0,
    'n_fully_vaccinated': 0,
    # 'population_size': 0
} for x in itertools.product([2020, 2021], [1, 2, 3, 4], states)}

for entry in get_vaccinations():
    state = entry['Recip_State']
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
    fully_vaccinated = format_str_to_int(entry['Series_Complete_Yes'])
    vaccinations[key]['n_fully_vaccinated'] = fully_vaccinated
    dose_1 = format_str_to_int(entry['Administered_Dose1_Recip'])
    vaccinations[key]['n_vaccinated'] = dose_1
    # percent = format_str_to_float(entry['Administered_Dose1_Pop_Pct']) / 100
    # vaccinations[key]['population_size'] += dose_1 / percent if percent else dose_1


vaccinations_df = pd.DataFrame(vaccinations.values())

travel_data = {x: {
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
    if key in travel_data:
        travel_data[key]['passengers_per_day'] += passengers
    else:
        ignored += 1
        ignored_passengers += passengers
        if year in [2020, 2021] and source != dest:
            print(f'Warning: Ignoring {source} -> {dest}')
print(f'Ignored {ignored} airline travel reports totaling {ignored_passengers} passengers.')

travel_data_df = pd.DataFrame(travel_data.values())



