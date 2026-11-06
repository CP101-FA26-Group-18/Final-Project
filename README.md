# CP101 Project - Group 18

project github can be found at: [github](https://github.com/CP101-FA26-Group-18/Final-Project)

---

## Project directory

CP101_project_18
    data
        processed  (all cleaned datasets live here)
        raw
            acs
            boundaries
            lodes
    notebooks
    visualizations
    analysis (.py file that defines functions in here)
    README.md (This file; instructions)
    requirements.txt (indicates required python libraries for all notebooks)

---

## Data aquisition

### ACS
ACS files can be accessed via a user-friendly web interface at https://data.census.gov/table/ACSDT1Y2023.B08301?q=b08301&g=050XX00US06001,06013,06041,06055,06075,06081,06085,06095,06097. That link will take you directly to the census table data explorer for table B08301 (means of transportation) filtered for the 9 Bay Area counties.

### LODES 
LEHD Origin destination Employment Statistics (LODES) files can be accessed directly from https://lehd.ces.census.gov/data/lodes/LODES8/ca/od/ (We use the most current publication in our analysis, LODES 8)

### Shapefiles (boundaries)
Shapefiles can be accessed from the TIGER/Line Shapefile web interface at https://www.census.gov/cgi-bin/geo/shapefiles/index.php

#### Notes on data aquisition
All thses files were dowloaded in compressed form manually for the purposes of the midterm project milestone submission. All of these data sources are courtesy of the United States Census Beureu, and they do provide methods for aquiring all three data sources through APIs or downoald scripts. These raw input data files were manually uploaded in compressed form in the `data/raw` folder.

---

## Data cleaning methodology and logging

in the data folder are two informational files: DATA_CLEANING_DESC.md explains the rational behind our decisions and DATA_CLEANING_LOG.txt compiles the dataset cleaning summaries that main_analysis.ipynb generates. NOTE ON MANUAL CHANGES THAT MUST BE MADE: if you want the notebook to produce these summaries present in the log text file, you have to change the year manulally in the notebook (you will recieve it being already set to 2023).

---
    
## Instruction on how to run analysis

### First, Data Cleaning
Once raw data files are placed in their respective folders, run the main_analysis.ipynb notebook found in the `notebooks` folder. This notebooks first process the LODES datasets into csv files where each row represents a unique work location and home location pair, and the 'commuters' column indicated the number of workers corresponding to that pair. The notebooks return these csv files, one each for census tract, administrative city, and county spatial granularities seperately. Then the notebook cleans ACS means of transportation table and returns a summary table that indicates the proportion of people who work from home for each bay area county. Cleaned csv files are placed in the `data/processed` folder.

#### Note on LODES Data Cleaning
Please keep in mind that each LODES dataset requires about 1 GB of RAM, and the entire main_analysis notebook uses approximately 10 GB RAM. The dataset cleaninig code has been previously executed and the cleaned output CSVs is provided in `/data/processed`.

#### Note on ACS Cleaning
There are some missing values in the dataset for Napa county, which was was discovered by manually checking. for now we deal with it by hardcoding a solution; later we will write functions to fix this missing value problem.

### Second, Visualizations
Once the cleaned csv files are generated in the main_analysis.ipynb notebook, run the visual.ipynb notebook in the same `notebooks` folder to produce the visualizations. Any outputted visualization (PNGs, etc.) are found in the `visualizations/figures` folder.