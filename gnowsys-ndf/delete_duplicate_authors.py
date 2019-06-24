from gnowsys_ndf.ndf.views.methods import delete_node
from gnowsys_ndf.ndf.models import *
ag = node_collection.collection.aggregate([{'$match': {'_type': 'Author'}}, {'$group': {'_id': {'created_by': '$created_by',  }, 'objs': {'$push': '$$CURRENT'}, 'count': {'$sum': 1} }}, {'$match': {'count': {'$gt': 1}}},  ])
j = [x for sl in (i.get('objs') for i in ag['result']) for x in sl]
auth_dec = {}

for i in j:
    try:
        if i['created_at'] < auth_dec[i['created_by']]['old'].keys()[0]:
            auth_dec[i['created_by']]['new'].extends(auth_dec[i['created_by']]['old'])
            auth_dec[i['created_by']]['old'] = {i['created_at']: i['_id']}
        else:
            auth_dec[i['created_by']]['new'][i['created_at']] = i['_id']
    except:
        auth_dec[i['created_by']] = {'old': {i['created_at']: i['_id']}, 'new': {} }
         
for each_node_to_del_id in ([ sl for x in (i['new'].values() for i in auth_dec.values()) for sl in x ]):
    delete_node(each_node_to_del_id, deletion_type=1)
