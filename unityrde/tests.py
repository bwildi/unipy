from unityrde import *
from copy import copy
import pandas as pd
import sys

def test_setup(project_id, api_key):

    # check methods for setting up the class work identically
    
    udi1 = UnityDataImporter(project_id, api_key)
    udi2 = UnityDataImporter()
    udi2.set_keys(project_id, api_key)

    for udi in [udi1, udi2]:
        assert udi.pid == project_id
        assert udi.key == api_key
        assert udi.base_url == f'https://analytics.cloud.unity3d.com/api/v2/projects/{project_id}/rawdataexports'

    pass_fail = 1

    # Check that methods fail appropriately
    # when setup has not properly been completed
    for i in range(7):
        udi_clone = copy(udi1)
        if i < 4: udi_clone.pid = None
        if i % 4 < 2: udi_clone.key = None
        if i % 2 == 0: udi_clone.base_url = None

        try:
            udi_clone.check_setup()
            pass_fail = 0
        except ValueError: pass
        
        assert pass_fail == 1

    # return udi for next test
    return udi1

def test_create_export(udi, params):
    params['format'] = 'json'

    # Check for formats
    for i in range(3):
        if i == 1: del params['format']
        elif i == 2: params['format'] = 'tsv'

        # check that a standard query works
        assert udi.create_export(params, return_value=True).status_code == 200
    

if __name__ == '__main__':
    pid = sys.argv[1]
    api_key = sys.argv[2]
    exp_id = sys.argv[3]
    udi = test_setup(pid, api_key)

    params = dict(startDate='2019-08-24',
              endDate='2019-08-25',
              format='json',
              dataset='appStart')

    test_create_export(udi, params)

    print(udi.list_data_exports())

    data = udi.get_data_export(export_id=exp_id, output='data')
    print(pd.DataFrame(data))