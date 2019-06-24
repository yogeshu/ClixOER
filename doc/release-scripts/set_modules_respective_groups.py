'''
Script which updates the collection_set of the Groups defined for OER with the respective modules

'''
from gnowsys_ndf.ndf.models import node_collection,triple_collection,Node,GAttribute
from bson import ObjectId

OER_GROUPS = ['Mathematics','Science','English']
oer_grp_details = {}
for eachgrp in OER_GROUPS:
  nd_data = Node.get_name_id_from_type(eachgrp,'Group',True)
  oer_grp_details.update({str(nd_data.name):nd_data})

module_gst_id = Node.get_name_id_from_type('Module','GSystemType')[1]
allmodules_cur = node_collection.find({'_type':'GSystem','member_of':module_gst_id})

for each in all_modules_cur:
  attrbval = GAttribute.get_triples_from_sub_type_list(each._id,'educationalsubject')                                                            
          #print attrbval                                        
  if attrbval and attrbval['educationalsubject'] != None:
    sbjt = attrbval['educationalsubject']['object_value']
    print sbjt , each._id                                
    if sbjt in oer_grp_details.keys():                       
      oer_grp_details[sbjt].collection_set.append(each._id)
  else:                  
    pass

for each, nd in oer_grp_details.items():
  nd.save()