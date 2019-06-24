'''
Script which updates the collection_set of the Groups defined for OER with the respective modules

'''
from gnowsys_ndf.ndf.models import node_collection,triple_collection,Node,GAttribute
from bson import ObjectId

OER_GROUPS = ['Mathematics','Science','English']
oer_grp_details = {}

grp_gst_id = Node.get_name_id_from_type('Group','GSystemType')[1]

for eachgrp in OER_GROUPS:
  nd_data = Node.get_name_id_from_type(eachgrp,'Group',True)
  oer_grp_details.update({str(nd_data.name):nd_data})

for grpname,grpobj in oer_grp_details.items():
  grpobj.type_of.append(grp_gst_id)
  print grpobj.name,grpobj.type_of
  grpobj.save()