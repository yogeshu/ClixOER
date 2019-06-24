'''
Script which updates the reources with corresponding group_id

'''


from gnowsys_ndf.ndf.models import node_collection,triple_collection,Node
from bson import ObjectId

OER_GROUPS = ['Mathematics','Science','English']
grp_gst_id = Node.get_name_id_from_type('Group','GSystemType')[1]

oergrp_nds = node_collection.find({'_type':'Group','member_of':grp_gst_id,'name':{'$in':OER_GROUPS}})

for eachnd in  oergrp_nds:
	units_under_modules = Node.get_tree_nodes(eachnd._id,'collection_set',2,True)
	for each_unit in units_under_modules:
		

