import json
import pandas as pd
import gzip
from io import BytesIO
import requests
import time
import warnings

class UnityDataImporter:
    '''
    Class for creating and reading raw data exports from the
    Unity API. Manual: https://docs.unity3d.com/Manual/UnityAnalyticsRawDataExport.html

    Can be initialised with a project_id and api_key (strings).
    '''
    def __init__(self, project_id=None, api_key=None):
        self.pid = project_id
        self.key = api_key
        self.export_id = None
        if project_id != None:
            self.base_url = f'https://analytics.cloud.unity3d.com/api/v2/projects/{project_id}/rawdataexports'

    def set_keys(self, project_id=None, api_key=None):
        '''
        Update the project_id, api_key and base url used to make queries.
        
        Paramaters:
        project_id: str id of the project
        api_key: str api key required to download data
        ''' 
        if api_key:
            self.key = api_key
        if project_id:
            self.pid = project_id
            self.base_url = f'https://analytics.cloud.unity3d.com/api/v2/projects/{project_id}/rawdataexports'

    def check_setup(self):
        '''
        Checks that project_id, api_key and base_url have all been set up.
        '''
        if not self.pid or not self.key or not self.base_url:
            raise ValueError('Project id, api_key and/or base_url are not defined.'
                                + '\n' + 'Please run set_keys first.')

    def create_export(self, params, return_value=False):
        '''
        Creates a new data export. Requires project_id, api_key and base_url
        to be defined (see set_keys to do this). Executing this function will
        also set a value for the export_id parameter.

        Note that single exports cannot be longer than 31 days by default.

        Parameters:
        params: dict dictionary of the arguments for the request.
            Arguments are:
            startDate: str, required unless continueFrom is specified. 
                Inclusive start data of the export in YYYY-MM-DD format.
            endDate: str, required. Exclusive end date of export in YYYY-MM-DD format.
            format: str, optional. Default is JSON, alternative is tsv.
                There is no reason to edit this, given that this only produces metadata.
            dataset: str, required. One of the following event types:
                appStart, appRunning, deviceInfo, custom or transaction
            continueFrom: str, optional. Raw data export ID of a previously created data
                export. Incompatible with startDate.
        return_value: bool, optional, default False. Option to return the request.
            If False, then the response status code is printed. 
        '''
        self.check_setup()

        if not 'format' in list(params.keys()):
            params['format'] = 'json'
        
        r = requests.post(self.base_url, json=params, auth=(self.pid, self.key))
        try: self.export_id = r.json()['id']
        except KeyError:
            raise requests.HTTPError('Request failure:', r.content)
            

        if return_value:
            return r
    
    def list_data_exports(self):
        '''
        Lists all available raw data export metadata. 
        
        Returns: json of all available data export metadata.
        '''
        self.check_setup()
        return requests.get(self.base_url, auth=(self.pid, self.key)).json()
    
    def get_data_export(self, export_id=None, output='data'):
        '''
        Get an existing data_export data/metadata with a specific id.

        Parameters:
        export_id: str, optional, if not specified, the id used is the export_id.
            If the export_id has not been set, then this will return an error.
            If this is used, then the export_id attribute will be updated on execution.
        output: str, options are 'data', 'metadata' or 'both' with 'data as the default.
            Determines what values to produce on the function return. 

        Returns: dict of metadata/list of dicts of data for each day according to the output argument. 
            If output is 'both', then output is a tuple of the data and metadata.
        '''
        self.check_setup()

        if not output in ['data','metadata','both']:
            raise ValueError(f'Invalid output argument {output}')

        if export_id == None:
            if self.export_id == None:
                raise ValueError('Export id was not provided and it has not been set.')
        else:
            self.export_id = export_id
       
        md = requests.get(self.base_url + f'/{self.export_id}', auth=(self.pid, self.key)).json()
        
        if output == 'metadata':
            return md
        
        else:
            if md['status'] == 'running': raise KeyError('Export has been created, but is not ready yet.')
            
            out = []
            try: md['result']['fileList']
            except KeyError:
                if output == 'data':
                    warnings.warn('No data found, return value is None')
                    return None
                else:
                    warnings.warn('No data found, only metadata will be returned')
                    return md
            for f in md['result']['fileList']:
                data_url = f['url']
                data_req = requests.get(data_url)
                data_string = gzip.open(BytesIO(data_req.content)).read().decode('utf-8')
                data_string = str(data_string).split('\n')

                data = []
                for d in data_string:
                    if d == '': pass
                    else: 
                        data.append(json.loads(d))
                
                out.append(data)

            if output == 'data':
                return out

            else:
                return out, md
    
    def create_and_get_export(self, params):
        '''
        Performs the create_export and get_data_export functions in one go.
        Note that single exports cannot be longer than 31 days by default.
        You can use make_long_df to make larger exports in one go.

        Parameters:
        params: dict dictionary of the arguments for the request.
            Arguments are:
            startDate: str, required unless continueFrom is specified. 
                Inclusive start data of the export in YYYY-MM-DD format.
            endDate: str, required. Exclusive end date of export in YYYY-MM-DD format.
            dataset: str, required. One of the following event types:
                appStart, appRunning, deviceInfo, custom or transaction
            continueFrom: str, optional. Raw data export ID of a previously created data
                export. Incompatible with startDate.

        returns:
        A json of the data from the request
    
        '''
        self.create_export(params)

        # Need to wait until export is ready
        counter = 0
        while True:
            status = self.get_data_export(output='metadata')['status']
            if status == 'completed':
                break
            dot = '.' * (counter % 4)
            counter += 1
            
            print(f'Creating {params["dataset"]} export from {params["startDate"]} to {params["endDate"]}{dot}   ', end='\r')
            time.sleep(0.5)
        print()
        print('Data export ready')
        data = self.get_data_export(output='data')
        return data

    def make_long_df(self, params):
        '''
        Same as make_df, but can be used to create data exports longer than 31 days.
        Works by creating multiple data exports and aggregating them together.

        Parameters:
        params: dict dictionary of the arguments for the request.
            Arguments are:
            startDate: str, required. continueFrom will not work here 
                Inclusive start data of the export in YYYY-MM-DD format.
            endDate: str, required. Exclusive end date of export in YYYY-MM-DD format.
            dataset: str, required. One of the following event types:
                appStart, appRunning, deviceInfo, custom or transaction

        returns:
        A pandas dataframe of the data from the request
        '''
        start_date, end_date = params['startDate'], params['endDate']
        start_year, start_month = int(start_date[:4]), int(start_date[5:7])
        end_year, end_month = int(end_date[:4]), int(end_date[5:7])
        months = end_month - start_month + 12 * (end_year - start_year)
        if months < 0:
            raise ValueError(f'The given start date {start_date} is later than the end date {end_date}')

        if months == 0:
            df = convert_to_pandas(self.create_and_get_export(params))
        
        else:
            for month in range(months + 1):
                if month == 0:
                    m = ((start_month + month - 1) % 12) + 1
                    y = (start_month + month - 1) // 12
                    if m == 12:
                        ed = f'{start_year + y + 1}-01-01'
                    else:
                        ed = f'{start_year + y}-{(m+1):02}-01'
                    params['endDate'] = ed
                    df = convert_to_pandas(self.create_and_get_export(params))

                    # Prevent an error if the end-date is on the first of a month
                    if ed == end_date: break
                    continue 

                elif month == months:
                    sd = f'{end_year}-{end_month:02}-01'
                    params['startDate'] = sd
                    params['endDate'] = end_date
                    df_ = convert_to_pandas(self.create_and_get_export(params))

                else:
                    m = ((start_month + month - 1) % 12) + 1
                    y = (start_month + month - 1) // 12
                    sd = f'{start_year + y}-{m:02}-01'
                    if m == 12:
                        ed = f'{start_year + y + 1}-01-01'
                    else:
                        ed = f'{start_year + y}-{(m+1):02}-01'
                    params['startDate'] = sd
                    params['endDate'] = ed
                    df_ = convert_to_pandas(self.create_and_get_export(params))
                    # Prevent an error if the end-date is on the first of a month
                    if ed == end_date: break
        
                if isinstance(df_, pd.DataFrame): 
                    if isinstance(df, pd.DataFrame):
                        df = df.append(df_, ignore_index=True, sort=False)
                    else:
                        df = df_
        return df

def convert_to_pandas(data):
    '''
    Converts the json file provided by Unity into a pandas DataFrame.

    Parameters:
        data: dict, the return value of UnityDataImporter.create_export

    Returns:
        A pandas dataframe version of the json file.
    '''
    if data == None:
        return None
    df = pd.DataFrame(data[0])
    if len(data) > 1:
        for day in data[1:]:
            df = df.append(pd.DataFrame(day), ignore_index=True, sort=False)
    return df