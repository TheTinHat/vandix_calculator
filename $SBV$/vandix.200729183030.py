import geopandas as gpd
import pandas as pd
import numpy as np
import requests
import zipfile
import os
import io
from time import sleep
import shapely
import fiona
import fiona.schema
import fiona._shim

def vandix(shapefile='', pruid='', cduid='', cmapuid=''):
    # Ask user for options
    if shapefile == '' and pruid == '' and cduid == '' and cmapuid == '':
        area_type = int(input('How would you like to select the area that VANDIX will be calculated for?\n1) Based on PRUID,\n2) Based on CDUID,\n3) Based on CMAPUID\n4) Based on the geometry of a shapefile\n5) All of Canada\n(Enter 1, 2, 3, 4, or 5): '))
        if area_type == 1:
            pruid = int(input('Enter PRUID: '))
        elif area_type == 2:
            cduid = int(input('Enter CDUID: '))
        elif area_type == 3:
            cmapuid = int(input('Enter CMAPAUID: '))
        elif area_type == 4:
            shapefile = input('Enter path to shapefile (.shp): ') 
        elif area_type == 5:
            pass

    # Get census boundary shapefiles
    
    if os.path.exists('census_data/lda_000b16a_e.shp') is False:
        print("Downloading census boundaries...")
        r = requests.get('https://osf.io/369v7/download')
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall('census_data')

    # Get census variables
    if os.path.exists('census_data/census_variables.csv') is False:
        print("Downloading census variables...")
        r = requests.get('https://osf.io/tj4hp/download')
        open('census_data/census_variables.csv', 'wb').write(r.content)
    
    print("Calculating VANDIX...")

    # Clean up the census boundaries
    census_das = gpd.read_file('census_data/lda_000b16a_e.shp')
    census_das['DAUID'] = census_das['DAUID'].astype(int)
    census_das = census_das.loc[:,['DAUID', 'geometry', 'PRUID', 'CDUID', 'CCSUID', 'CMAPUID']]


    # Clean up the census variables
    census_table = pd.read_csv('census_data/census_variables.csv')
    census_table = census_table.dropna()
    census_table = census_table.loc[census_table['totalfamilies'] != 0, :]

    # Select DAs based on shapefile
    if shapefile != '':
        selection_area = gpd.read_file(shapefile)
        census_das = census_das.to_crs(selection_area.crs)
        selection_area = shapely.ops.unary_union(selection_area.geometry)
        bbox = selection_area.bounds
        census_das = census_das.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        census_das = census_das[census_das.intersects(selection_area)]
        filename = 'shapefile'

    # Select DAs based on PRUID
    elif pruid != '':
        census_das = census_das.loc[census_das['PRUID'] == str(pruid), :]
        filename = pruid

    # Select DAs based on CDUID
    elif cduid != '':
        census_das = census_das.loc[census_das['CDUID'] == str(cduid), :]
        filename = cduid


    # Select DAs based on CMAPUID
    elif cmapuid !='':
        census_das = census_das.loc[census_das['CMAPUID'] == str(cmapuid), :]
        filename = cmapuid

    # Join the table to the boundaries
    census_das = census_das.merge(census_table, on='DAUID')

    # Calculate rates
    census_das['noedu_pct'] = census_das.apply(lambda x: (x['noedu'] / x['totaledu']) *  100, axis=1)
    census_das['university_pct'] = census_das.apply(lambda x: (x['university'] / x['totaledu']) * 100, axis=1)
    census_das['loneparent_pct'] = census_das.apply(lambda x: (x['loneparent'] / x['totalfamilies']) * 100, axis=1)
    census_das['owners_pct'] = census_das.apply(lambda x: (x['owners'] / x['totaldwel']) * 100, axis=1)

    z_score_dict = {
        'z_noedu' : 'noedu_pct',
        'z_university' : 'university_pct',
        'z_loneparent' : 'loneparent_pct',
        'z_owners' : 'owners_pct',
        'z_income' : 'income',
        'z_unemployment' : 'unemployment',
        'z_participation' : 'participation',
    }
    w_score_dict = {
        'w_noedu' : ('z_noedu', 0.25),
        'w_university' : ('z_university', -0.179),
        'w_loneparent' : ('z_loneparent', 0.143),
        'w_owners' : ('z_owners', -0.089),
        'w_income' : ('z_income', -0.089),
        'w_unemployment' : ('z_unemployment', 0.214),
        'w_participation' : ('z_participation', -0.036),
    }

    # Calculate zscores
    for key, value in z_score_dict.items():
        census_das[key] = census_das.apply(lambda x: (x[value] - np.mean(census_das[value])) / np.std(census_das[value]), axis=1)

    # Weight the zscores
    for key, value in w_score_dict.items():
        census_das[key] = census_das.apply(lambda x: x[value[0]] * value[1], axis=1)

    # Add scores to create VANDIX
    columns = [column for column in w_score_dict.keys()]
    census_das['vandix'] = census_das.apply(lambda x: sum([x[column] for column in columns]), axis=1)


    # Delete unnecessary columns
    [columns.append(column) for column in z_score_dict.keys()]
    [columns.append(column) for column in z_score_dict.values()]
    columns.extend(['noedu', 'totaledu', 'university', 'loneparent', 'owners', 'totalfamilies', 'totaldwel'])
    census_das = census_das.drop(columns, axis=1)

    # Export shapefile
    if os.path.exists('/vandix') is False:
        os.mkdir('/vandix')
    filename = '/vandix/' + str(filename) + '_vandix.shp'
    census_das.to_file(filename)
    print("Done! VANDIX shapefile saved to " + str(filename))
    return census_das

if __name__ == '__main__':
    vandix()
    sleep(30)