"""
Cassini Technical Assignment
Paul Lunkenheimer

Performs following task:
    For the second part, your objectives are to create a script that performs a full descriptive statistics for the flight delay in San Francisco.
    Try to offload as much of the calculations as possible to the database level
    and investigate what the most common factors (Cause of Delay) for a departure flight delay at the San Francisco airport (SFO) are.
    Analyse if there is a significant difference of delay between the carriers at the San Francisco airport in 2019.
    If so, which carriers are better and which worse? Conduct a complete analysis for this part (including centrality, variability and shape).
    Please write a reproducible report (a report that generates at compilation a document with output based on provided data).
    (...)
    The raw files need to be able to compile on any given computer that has the languages and dependencies installed.
"""

#-----------------------------------------------------------------------------
# Libraries
#-----------------------------------------------------------------------------
import pandas as pd                 # Used as Python Data Analysis Library
import matplotlib.pyplot as plt     # Used for visualization
import matplotlib as mpl            # Used for adding seperator ',' for 10^3 steps
from load_data import load_data     # Used to load raw flight data from web

#-----------------------------------------------------------------------------
# User input
#-----------------------------------------------------------------------------
is_saved = False                                                               # Prepared pandas dataframe already saved locally?
save_name = "cotp_save.feather"                                                # Filename of local save

url_path = 'https://transtats.bts.gov/PREZIP/'                                 # 1st part of URL to prezipped data
zip_start = 'On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2019_' # 2nd part of URL to prezipped data - start of name of zip-files
zip_it = [str(i) for i in range(1, 13)]                                        # 3rd part of URL to prezipped data - iterator over months in name of zip-files
zip_end = '.zip'                                                               # 4th part of URL to prezipped data - end of name of zip-files

#-----------------------------------------------------------------------------
# Load and prepare data
#-----------------------------------------------------------------------------
if not is_saved:
    # Load data from web
    # 'cotp' stands for 'Carrier On Time Performance'
    pd_cotp = load_data(url_path, zip_start, zip_it, zip_end)

    # Reduce database to necessary data
    print('Delete unnecessary data to reduce size. This might take a while.')
    # Delete cancelled flights
    # They are interesting, but do not play a role when investigating departure delay!
    row_rmv_mask = (pd_cotp['Cancelled'] != 0)
    pd_cotp.drop(index=pd_cotp[row_rmv_mask].index, inplace=True)
    pd_cotp.reset_index(drop=True, inplace=True)
    # Delete diverted flights that did not reach their destination
    # They are interesting, but the problem/interesting part is not the delay
    # It rather is the fact that they did not reach their destination
    row_rmv_mask = (pd_cotp['DivReachedDest'] == 0)
    pd_cotp.drop(index=pd_cotp[row_rmv_mask].index, inplace=True)
    pd_cotp.reset_index(drop=True, inplace=True)
    # Note: Use 'DepDelayMinutes' over 'DepDelay' as latter shows early departures with negative numbers
    #       When computing sum, mean, etc. this could distort result as early departures would make up for delays
    col_rmv = ['Year', 'DOT_ID_Reporting_Airline', 'IATA_CODE_Reporting_Airline', 'Tail_Number', 'Flight_Number_Reporting_Airline', 'OriginAirportSeqID',
               'Origin', 'OriginState', 'OriginStateFips', 'OriginWac', 'DestAirportSeqID', 'Dest', 'DestState', 'DestStateFips', 'DestWac',
               'DepDelay', 'DepartureDelayGroups', 'ArrDelayMinutes', 'ArrivalDelayGroups', 'FirstDepTime',
               'TotalAddGTime', 'LongestAddGTime', 'Unnamed: 109', 'Cancelled', 'CancellationCode', 'DivReachedDest']
    pd_cotp.drop(columns=col_rmv, inplace=True)
    col_rmv = ['Div1Airport', 'Div1AirportID', 'Div1AirportSeqID', 'Div1WheelsOn', 'Div1TotalGTime', 'Div1LongestGTime', 'Div1WheelsOff', 'Div1TailNum',
               'Div2Airport', 'Div2AirportID', 'Div2AirportSeqID', 'Div2WheelsOn', 'Div2TotalGTime', 'Div2LongestGTime', 'Div2WheelsOff', 'Div2TailNum',
               'Div3Airport', 'Div3AirportID', 'Div3AirportSeqID', 'Div3WheelsOn', 'Div3TotalGTime', 'Div3LongestGTime', 'Div3WheelsOff', 'Div3TailNum',
               'Div4Airport', 'Div4AirportID', 'Div4AirportSeqID', 'Div4WheelsOn', 'Div4TotalGTime', 'Div4LongestGTime', 'Div4WheelsOff', 'Div4TailNum',
               'Div5Airport', 'Div5AirportID', 'Div5AirportSeqID', 'Div5WheelsOn', 'Div5TotalGTime', 'Div5LongestGTime', 'Div5WheelsOff', 'Div5TailNum', 
               'DivAirportLandings', 'DivDistance']
    pd_cotp.drop(columns=col_rmv, inplace=True)

    # If flight was diverted, 'ActualElapsedTime' and 'ArrDelay' are NULL
    # Data is instead kept in columns 'DivActualElapsedTime' and 'DivArrDelay'
    pd_cotp_mask = (pd_cotp['Diverted'] != 0)
    pd_cotp.loc[pd_cotp_mask, 'ActualElapsedTime'] = pd_cotp.loc[pd_cotp_mask, 'DivActualElapsedTime']
    pd_cotp.loc[pd_cotp_mask, 'ArrDelay'] = pd_cotp.loc[pd_cotp_mask, 'DivArrDelay']
    pd_cotp.drop(columns=['DivActualElapsedTime', 'DivArrDelay'], inplace=True)

    # Add derived data columns
    print('Add derived data of interest.')
    # Is flight delayed at all?
    pd_cotp['DepDel0'] = (pd_cotp['DepDelayMinutes'] > 0)
    # Percentage of delayed minutes of the scheduled time for the flight
    pd_cotp['DepDelayMinutesPerc'] = 100*pd_cotp['DepDelayMinutes']/pd_cotp['CRSElapsedTime']

    # Save pandas dataframe to local file
    pd_cotp.to_feather(save_name)
    print('Preparation of data done.')

else:
    # Load pandas dataframe from local save
    pd_cotp = pd.read_feather(save_name)

#-----------------------------------------------------------------------------
# Get overview over possible factors for delay of departures
# Toggle comments, change factor variable,
# restrict to specific airline in order to "play with the data"
#-----------------------------------------------------------------------------
# Modify factor variable to investigate different possible factors
# Options: 'Quarter' 'Month' 'DayofMonth' 'DayOfWeek' 'Reporting_Airline'
#          'OriginAirportID' 'OriginCityMarketID' 'OriginCityName' 'OriginStateName'
#          'DestAirportID' 'DestCityMarketID' 'DestCityName' 'DestStateName'
#          'DepTimeBlk' 'ArrTimeBlk' 'DistanceGroup'
factor = 'Reporting_Airline'

# Reduce data to specific airline?
# airline = 'AA'
# row_rmv_mask = (pd_cotp['Reporting_Airline'] != airline)
# pd_cotp.drop(index=pd_cotp[row_rmv_mask].index, inplace=True)
# pd_cotp.reset_index(drop=True, inplace=True)

# Total sum
# delay_sum_by_fac = pd_cotp.groupby(factor)[['DepDelayMinutes', 'DepDel0', 'DepDel15', 'DepDelayMinutesPerc']].sum()
# print('Total sum:')
# print(delay_sum_by_fac)
# print('')

# Max - look for outliers (problems with raw data?)
# delay_max_by_fac = pd_cotp.groupby(factor)[['DepDelayMinutes', 'DepDelayMinutesPerc']].max()
# print('Max:')
# print(delay_max_by_fac)
# print('')

# Mean
# delay_mean_by_fac = pd_cotp.groupby(factor)[['DepDelayMinutes', 'DepDelayMinutesPerc']].mean()
# print('Mean:')
# print(delay_mean_by_fac)
# print('')

# Variance
# delay_var_by_fac = pd_cotp.groupby(factor)[['DepDelayMinutes', 'DepDelayMinutesPerc']].var()
# print('Variance:')
# print(delay_var_by_fac)
# print('')

# Percentage of flights delayed
# delay_perc_by_fac = 100*pd_cotp.groupby(factor)['DepDel15', 'DepDel0'].mean()
# print('Percentage of flights delayed >= 15 minutes:')
# print(delay_perc_by_fac)
# print('')

# Median taken only over flights delayed >= 15 minutes
# delay_median_by_fac = pd_cotp.loc[(pd_cotp['DepDel15'] != 0), :].groupby(factor)[['DepDelayMinutes', 'DepDelayMinutesPerc']].median()
# print('Mediantaken only over flights delayed >= 15 minutes:')
# print(delay_median_by_fac)
# print('')

# Covariance of delayed minutes, if flight was delayed, if flight was delayed >=15m, percentage of delayed minutes with other columns
# delay_cov = pd_cotp.cov()[['DepDelayMinutes', 'DepDel0', 'DepDel15', 'DepDelayMinutesPerc']]
# print('Covariance of different delay measures with other data columns:')
# print(delay_cov)
# print('')

# Correlation of delayed minutes, if flight was delayed, if flight was delayed >=15m, percentage of delayed minutes with other columns
# delay_corr = pd_cotp.corr()[['DepDelayMinutes', 'DepDel0', 'DepDel15', 'DepDelayMinutesPerc']]
# print('Correlation of different delay measures with other data columns:')
# print(delay_corr)
# print('')

#-----------------------------------------------------------------------------
# Produce exportable figures showing interesting finds
#-----------------------------------------------------------------------------
# Prepare data
delay_sum_by_airline = pd_cotp.groupby('Reporting_Airline')[['DepDelayMinutes', 'DepDel15', 'DepDelayMinutesPerc', 'DepDel0']].sum()
delay_mean_by_airline = pd_cotp.groupby('Reporting_Airline')[['DepDelayMinutes', 'DepDel15', 'DepDelayMinutesPerc', 'DepDel0']].mean()
delay_mean_by_airline_0 = pd_cotp.loc[pd_cotp['DepDel0'], ['Reporting_Airline', 'DepDelayMinutes']].groupby('Reporting_Airline').mean()
delay_mean_by_airline_15 = pd_cotp.loc[(pd_cotp['DepDel15'] != 0), ['Reporting_Airline', 'DepDelayMinutes']].groupby('Reporting_Airline').mean()
delay_mean_by_airline_0_15 = pd.concat([delay_mean_by_airline_0, delay_mean_by_airline_15], axis=1)
delay_mean_by_departure_time_AA = pd_cotp.loc[(pd_cotp['Reporting_Airline'] != 'AA'), ['DepTimeBlk', 'DepDelayMinutes', 'DepDel15', 'DepDelayMinutesPerc', 'DepDel0']].groupby('DepTimeBlk').mean()
delay_sum_by_cause = pd_cotp[['CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay']].sum()
labels_cause = ['CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay']
delay_mean_by_cause = [pd_cotp.loc[(pd_cotp[cause] > 0), cause].mean() for cause in labels_cause]
pos_AA = delay_sum_by_airline.index.get_loc('AA')
plt.grid(linestyle='--')

# Total number of delayed flights
colors = {'DepDel0': '#888888', 'DepDel15': 'w'}
ax_by_airline = delay_sum_by_airline[['DepDel0', 'DepDel15']].plot.bar(xlabel='Airline', ylabel='Number of delayed flights', grid=True, color=colors, alpha=0.8, legend=False)
ax_by_airline.patches[pos_AA].set_facecolor('#aa3333')
ax_by_airline.get_yaxis().set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))   # Add seperator ',' for ticks on y-axis
plt.close(fig=1)
plt.show()

# Total number of delayed flights - delayed >0m and >=15m
colors = {'DepDel0': '#888888', 'DepDel15': 'k'}
ax_by_airline = delay_sum_by_airline[['DepDel0', 'DepDel15']].plot.bar(xlabel='Airline', ylabel='Number of delayed flights', grid=True, color=colors, alpha=0.8, legend=False)
ax_by_airline.patches[pos_AA].set_facecolor('#aa3333')
ax_by_airline.patches[delay_sum_by_airline.shape[0]+pos_AA].set_facecolor('#762424')
ax_by_airline.get_yaxis().set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))   # Add seperator ',' for ticks on y-axis
plt.show()
# 'WN'  is 'Southwest Airlines Co.'

# Number of flights reported by AA
print(pd_cotp.groupby('Reporting_Airline').size())
print('')
# 3rd highest number of reported flights (926.481)

# Percentage of delayed flights - delayed >0m and >=15m
colors = {'DepDel0': '#888888', 'DepDel15': 'k'}
ax_by_airline = delay_mean_by_airline[['DepDel0', 'DepDel15']].plot.bar(xlabel='Airline', ylabel='Percentage of delayed flights', grid=True, color=colors, alpha=0.8, legend=False)
ax_by_airline.patches[pos_AA].set_facecolor('#aa3333')
ax_by_airline.patches[delay_mean_by_airline.shape[0]+pos_AA].set_facecolor('#762424')
plt.show()

# Mean delay
colors = '#888888'
ax_by_airline = delay_mean_by_airline['DepDelayMinutes'].plot.bar(xlabel='Airline', ylabel='Mean Delay in m', grid=True, color=colors, alpha=0.8, legend=False)
ax_by_airline.patches[pos_AA].set_facecolor('#aa3333')
plt.show()

# Mean delay >0m and >=15m
colors = '#888888'
ax_by_airline = delay_mean_by_airline_0_15.plot.bar(xlabel='Airline', ylabel='Mean Delay in m', grid=True, color=colors, alpha=0.8, legend=False)
ax_by_airline.patches[pos_AA].set_facecolor('#aa3333')
ax_by_airline.patches[delay_mean_by_airline_0_15.shape[0]+pos_AA].set_facecolor('#CE8686')
plt.show()

# Mean delay in percentage of scheduled flight time
colors = '#888888'
ax_by_airline = delay_mean_by_airline['DepDelayMinutesPerc'].plot.bar(xlabel='Airline', ylabel='Mean Delay in Percentage of scheduled flight time', grid=True, color=colors, alpha=0.8, legend=False)
ax_by_airline.patches[pos_AA].set_facecolor('#aa3333')
plt.show()

# Mean delay of AA by departure time
# Correlation with DepTime:
# DepDelayMinutes   DepDel0  DepDel15  DepDelayMinutesPerc
#        0.117539  0.228763  0.212300             0.119499
colors = '#888888'
ax_by_dep_time = delay_mean_by_departure_time_AA['DepDelayMinutes'].plot.bar(xlabel='Departure Time', ylabel='Mean Delay in m', grid=True, color=colors, alpha=0.8, legend=False)
plt.show()
# Number of flights by AA at different departure times
print(pd_cotp.loc[(pd_cotp['Reporting_Airline'] != 'AA'), :].groupby('DepTimeBlk').size())
print('')

# Pie Plot of total delay due to different delay causes for AA
# Of course: Huge correlation of delay with delay causes!
delay_sum_by_cause.transpose().plot.pie(ylabel='')
plt.show()

# Pie Plot of mean delay due to different delay causes for AA
# Of course: Huge correlation of delay with delay causes!
plt.pie(delay_mean_by_cause, labels=labels_cause)
plt.show()















# 'Quarter' 'Month' 'DayofMonth' 'DayOfWeek' 'FlightDate'
#  'Reporting_Airline'
#  'OriginAirportID'
#  'OriginCityMarketID' 'OriginCityName'
#  'OriginStateName' 'DestAirportID'
#  'DestCityMarketID' 'DestCityName' 
#  'DestStateName' 'CRSDepTime' 'DepTime'
#  'DepDelayMinutes' 'DepDel15' 'DepTimeBlk'
#  'TaxiOut' 'WheelsOff' 'WheelsOn' 'TaxiIn' 'CRSArrTime'
#  'ArrTime' 'ArrDelay' 'ArrDel15' 'ArrTimeBlk'
#  'Diverted' 'CRSElapsedTime'
#  'ActualElapsedTime' 'AirTime' 'Flights' 'Distance' 'DistanceGroup'
#  'CarrierDelay' 'WeatherDelay' 'NASDelay' 'SecurityDelay'
#  'LateAircraftDelay'

# 'Year' 'Quarter' 'Month' 'DayofMonth' 'DayOfWeek' 'FlightDate'
#  'Reporting_Airline' 'DOT_ID_Reporting_Airline'
#  'IATA_CODE_Reporting_Airline' 'Tail_Number'
#  'Flight_Number_Reporting_Airline' 'OriginAirportID' 'OriginAirportSeqID'
#  'OriginCityMarketID' 'Origin' 'OriginCityName' 'OriginState'
#  'OriginStateFips' 'OriginStateName' 'OriginWac' 'DestAirportID'
#  'DestAirportSeqID' 'DestCityMarketID' 'Dest' 'DestCityName' 'DestState'
#  'DestStateFips' 'DestStateName' 'DestWac' 'CRSDepTime' 'DepTime'
#  'DepDelay' 'DepDelayMinutes' 'DepDel15' 'DepartureDelayGroups'
#  'DepTimeBlk' 'TaxiOut' 'WheelsOff' 'WheelsOn' 'TaxiIn' 'CRSArrTime'
#  'ArrTime' 'ArrDelay' 'ArrDelayMinutes' 'ArrDel15' 'ArrivalDelayGroups'
#  'ArrTimeBlk' 'Cancelled' 'CancellationCode' 'Diverted' 'CRSElapsedTime'
#  'ActualElapsedTime' 'AirTime' 'Flights' 'Distance' 'DistanceGroup'
#  'CarrierDelay' 'WeatherDelay' 'NASDelay' 'SecurityDelay'
#  'LateAircraftDelay' 'FirstDepTime' 'TotalAddGTime' 'LongestAddGTime'
#  'DivAirportLandings' 'DivReachedDest' 'DivActualElapsedTime'
#  'DivArrDelay' 'DivDistance' 'Div1Airport' 'Div1AirportID'
#  'Div1AirportSeqID' 'Div1WheelsOn' 'Div1TotalGTime' 'Div1LongestGTime'
#  'Div1WheelsOff' 'Div1TailNum' 'Div2Airport' 'Div2AirportID'
#  'Div2AirportSeqID' 'Div2WheelsOn' 'Div2TotalGTime' 'Div2LongestGTime'
#  'Div2WheelsOff' 'Div2TailNum' 'Div3Airport' 'Div3AirportID'
#  'Div3AirportSeqID' 'Div3WheelsOn' 'Div3TotalGTime' 'Div3LongestGTime'
#  'Div3WheelsOff' 'Div3TailNum' 'Div4Airport' 'Div4AirportID'
#  'Div4AirportSeqID' 'Div4WheelsOn' 'Div4TotalGTime' 'Div4LongestGTime'
#  'Div4WheelsOff' 'Div4TailNum' 'Div5Airport' 'Div5AirportID'
#  'Div5AirportSeqID' 'Div5WheelsOn' 'Div5TotalGTime' 'Div5LongestGTime'
#  'Div5WheelsOff' 'Div5TailNum' 'Unnamed: 109'