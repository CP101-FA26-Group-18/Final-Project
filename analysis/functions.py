#import libraries
import gc # garbage collector for RAM conservation
import numpy as np
import pandas as pd
import geopandas as gpd

# for importing and cleaning lodes data
def load_and_clean_lodes_od(year, lodes_path, bay_area_county_FIPS, state='ca'): # year must be integer
    """
    takes a year (2017-2023) and loads the LODES dataset for that year into the notebook. 
    returns a dataframe.
    NOTE: deletes the raw dataframe from notebook memory to save space
    NOTE: state param defaults to 'ca' for California but can be assigned to any lowercase state code (done for reproducibility)
    """
    
    filename = f"{state}_od_main_JT00_{year}.csv.gz"
    filepath = lodes_path+'/'+filename

    df_raw = pd.read_csv(filepath,
        compression="gzip",
        dtype={"w_geocode": str, "h_geocode": str, "S000": int}, # we need S000 column because it tells us how many workers are in that OD pair
        usecols=["w_geocode", "h_geocode", "S000"])

    # filter out non bay area rows
    bay_fips = tuple(bay_area_county_FIPS)  # this need a tuple
    mask_bay = df_raw["w_geocode"].str.startswith(bay_fips) & df_raw["h_geocode"].str.startswith(bay_fips) # ONLY keep workers who work and live in the bay
    df_bay = df_raw[mask_bay].copy()

    # delete the non-bay area (raw) dataframe from memory
    del df_raw
    gc.collect() # taught in data 100

    return df_bay

# adds tracts and counties using gecode columns
def lodes_county_tracts_adder(df_raw):
    """
    adds counties and tracts columns for origins and destinations.
    does not return anything, edits inputted dataframe in place.
    """
    
    df_raw["w_county"] = df_raw["w_geocode"].str.slice(0, 5)
    df_raw["h_county"] = df_raw["h_geocode"].str.slice(0, 5)
    df_raw["w_tract"] = df_raw["w_geocode"].str.slice(0, 11)
    df_raw["h_tract"] = df_raw["h_geocode"].str.slice(0, 11)

# groups into tract-level (and deletes block-level to save memory space)
def lodes_tract_grouper(lodes_df):
    '''
    input the dataframe returned by load_and_clean_lodes_od to bin it into tract-level
    returns tract + county level dataframe
    NOTE: deletes the input dataframe, to save RAM
    '''
    df_tract_od = lodes_df.groupby(["w_tract", "h_tract", "w_county", "h_county"], as_index=False)["S000"].sum()
    df_tract_od = df_tract_od.rename(columns={"S000": "commuters"}) # rename s000 to make it less esoteric

    del lodes_df
    gc.collect()
    
    return df_tract_od

# groups into county-level
def lodes_county_grouper(lodes_df):
    '''
    input should be what lodes_tract_grouper returns
    returns dataframe with county level granularity only
    '''
    df_county_od = lodes_df.groupby(["w_county", "h_county"], as_index=False)["commuters"].sum()

    return df_county_od

# maps tracts to cities using largest share rule
def place_mapper_dict_maker(tracts_gpd,places_gpd,epsg_=2227):
    """
    uses largest share rule to produce dict used for 1-to-1 mapping tracts to cities (lab9)
    input bay_tracts and CA_places geodataframes, returns a dictionary that maps tracts to cities
    """
    # overlay places onto tracts, keeps only places that are relevant
    tract_city_pieces = gpd.overlay(tracts_gpd, places_gpd, how="intersection")
    tract_city_pieces.to_crs(epsg=epsg_)

    # keep the city that covers a given tract the most (the lookup var), then assign that tract to that city
    tract_city_pieces["piece_area_sqft"] = tract_city_pieces.geometry.area
    largest_share_city_lookup = (tract_city_pieces.sort_values("piece_area_sqft", ascending=False).drop_duplicates(subset=["tract_geoid"])[["tract_geoid", "city_name", "place_geoid"]].copy())
    bay_tracts = tracts_gpd.merge(largest_share_city_lookup, on="tract_geoid", how="left") # left keeps all the bay area tracts and discards the unused non-bay area cities

    # tracts in unincorporated areas (pieces outside any official city/place boundary)
    bay_tracts["city_name"] = bay_tracts["city_name"].fillna("Unincorporated")
    bay_tracts["place_geoid"] = bay_tracts["place_geoid"].fillna("Unincorporated")

    # this dictionary maps tracts in bay_tracts to cities in bay tracts
    tract_to_city = bay_tracts.copy().set_index("tract_geoid")["city_name"].to_dict()
    return tract_to_city

# groups into city-level using the tract_to_city dict
def lodes_city_adder_grouper(lodes_df,tract_to_city):
    '''
    input should be what lodes_tract_grouper returns
    adds columns for workplace and home cities to the dataframe
    '''
    lodes_df_temp = lodes_df.copy()

    lodes_df_temp["w_city"] = lodes_df["w_tract"].map(tract_to_city)
    lodes_df_temp["h_city"] = lodes_df["h_tract"].map(tract_to_city)

    lodes_df_temp["w_city"] = lodes_df_temp["w_city"].fillna("Unincorporated")
    lodes_df_temp["h_city"] = lodes_df_temp["h_city"].fillna("Unincorporated")

    df_city_od = lodes_df_temp.groupby(["w_city", "h_city"], as_index=False)["commuters"].sum()

    return df_city_od

# changes the county column from using fips codes to using actual names
def county_fips_to_name_mapper(LODES_year_county, county_fips_to_name):
    """
    input county LODES df and county fips mapper dict
    returns the LODES df with county names instead of fips codes
    """
    LODES_year_county['w_county'] = LODES_year_county['w_county'].map(county_fips_to_name)
    LODES_year_county['h_county'] = LODES_year_county['h_county'].map(county_fips_to_name)
    return LODES_year_county

# for acs data
def acs_col_desc_cleaner(acs_df):
    """ 
    input: acs df
    returns: acs df with margin of error columns removed and first row removed
    """
    acs_df_cleaned = acs_df.loc[:, ~acs_df.columns.str.contains('M$')].loc[lambda df: df['GEO_ID'] != 'Geography']
    return acs_df_cleaned

def acs_county_extractor(acs_year, county_fips_to_name):
    '''
    extract county code from full fips code in geo_id col
    returns acs_year but with county as name col
    '''
    acs_year_w_county = acs_year.copy()
    acs_year_w_county['FIPS'] = acs_year['GEO_ID'].str.slice(-5)
    acs_year_w_county['county'] = acs_year_w_county['FIPS'].map(county_fips_to_name)
    return acs_year_w_county

def acs_wfh_adder(acs_year_w_county):
    '''
    first returns the df that has three cols: county fips, county name, and WFH prop
    second return the proportion of wfh
    '''
    prop_wfh = acs_year_w_county['B08301_021E'].astype(int) / acs_year_w_county['B08301_001E'].astype(int)
    acs_year_wfh = acs_year_w_county.copy()
    acs_year_wfh['WFH prop'] = prop_wfh
    return acs_year_wfh, prop_wfh