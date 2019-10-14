import json
import pandas as pd
import gzip
from io import BytesIO
import requests
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

    def set_keys(self, project_id, api_key):
        '''
        Set the project_id, api_key and base url to make queries.
        This method is not required if project_id and api_key are defined
        from the outset.
        
        Paramaters:
        project_id: str id of the project
        api_key: str api key required to download data
        ''' 
        self.pid = project_id
        self.key = api_key
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

        Note that single exports cannot be longer than 31 days by default     
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
