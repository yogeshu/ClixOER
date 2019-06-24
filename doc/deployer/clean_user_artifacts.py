from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from gnowsys_ndf.ndf.models import node_collection, triple_collection, filehive_collection, counter_collection, GSystemType
from gnowsys_ndf.settings import GSTUDIO_DATA_ROOT, GSTUDIO_LOGS_DIR_PATH, MEDIA_ROOT, GSTUDIO_INSTITUTE_ID, GSTUDIO_INSTITUTE_ID
from export_logic import create_log_file, write_md5_of_dump, get_counter_ids, dump_node
from gnowsys_ndf.ndf.views.methods import delete_node,get_group_name_id

UNIT_IDS = []
UNIT_NAMES = []
log_file_path = None

def call_exit():
    print "\nExiting..."
    os._exit(0)   

def delete_user_artifacts(user_ids_list):
    user_ids_list = map(int, user_ids_list)
    all_nodes = node_collection.find({'_type': 'GSystem', 'created_by': {'$in': user_ids_list}, 'group_set': {'$in': UNIT_IDS}}),
    print "\nArtifacts: ", all_nodes.count()
    for each_node in all_nodes:
        print ".",
        log_file.write("deleting the artifact node {0} created by {1}".format(each_node._id,each_node.created_by))
        delete_node(node=each_node,collection_name=node_collection,deletion_type=1)

# def get_and_delete_counter_ids(group_id=None, group_node=None, user_ids=None):
#     '''
#     Fetch all the Counter instances of the exporting Group
#     '''
#     if group_id:
#         counter_collection_cur = counter_collection.find({'group_id':ObjectId(group_id)})
#     elif group_node:
#         counter_collection_cur = counter_collection.find({'group_id':ObjectId(group_node._id)})
#     elif user_ids:
#         counter_collection_cur = counter_collection.find({'user_id': {'$in': user_ids}})

#     if counter_collection_cur :
#         for each_obj in counter_collection_cur :
#             delete_user_artifacts(node=each_obj,collection_name=counter_collection, variables_dict=GLOBAL_DICT)


class Command(BaseCommand):
    def handle(self, *args, **options):
        global UNIT_IDS
        global UNIT_NAMES
        global log_file
        global log_file_path
        print "\nUSER DATA CLEANING FOR : ", GSTUDIO_INSTITUTE_ID
        ann_unit_gst_name, ann_unit_gst_id = GSystemType.get_gst_name_id(u"announced_unit")
        if args:
          try:
            args_ids = map(ObjectId,args)
          except Exception as e:
            print "\n\nPlease enter Valid ObjectId."
            call_exit()
          all_ann_units_cur = node_collection.find({'_id': {'$in': args_ids}})
          for each_un in all_ann_units_cur:
            UNIT_IDS.append(each_un._id)
            UNIT_NAMES.append(each_un.name)
        else:
          all_ann_units_cur = node_collection.find({'member_of': ann_unit_gst_id})
          print "\nTotal Units : ", all_ann_units_cur.count()
          for ind, each_ann_unit in enumerate(all_ann_units_cur, start=1):
              unit_selection = raw_input("\n\t{0}. Unit: {1} \n\tEnter y/Y to select: ".format(ind, each_ann_unit.name))
              if unit_selection in ['y', 'Y']:
                  print "\t Yes"
                  UNIT_IDS.append(each_ann_unit._id)
                  UNIT_NAMES.append(each_ann_unit.name)
              else:
                  print "\t No"

        print "\nUser Artifacts Cleaning of following Units:"
        print ("\n\t".join(["{0}. {1}".format(i,unit_name) for i, unit_name in enumerate(UNIT_NAMES, 1)]))

        proceed_flag = raw_input("\nEnter y/Y to Confirm: ")
        if proceed_flag:
          try:

            datetimestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file_name = 'artifacts_dump_' + str(GSTUDIO_INSTITUTE_ID) + "_"+ str(datetimestamp)

            TOP_PATH = os.path.join(GSTUDIO_DATA_ROOT, 'data_export',  log_file_name)
            SCHEMA_MAP_PATH = TOP_PATH

            log_file_path = create_log_file(log_file_name)
            setup_dump_path()


            log_file = open(log_file_path, 'w+')
            log_file.write("\n######### Script ran on : " + str(datetime.datetime.now()) + " #########\n\n")
            log_file.write("User Artifacts Data Cleaning for Units: " + str(UNIT_IDS))

            query = {'member_of': ann_unit_gst_id}
            rec = node_collection.collection.aggregate([
              { "$match": query },
              {  "$group":   {
              '_id': 0,
              'count': { '$sum': 1 } ,
              "author_set": {
                "$addToSet":    "$author_set"
              },
              "group_admin": {
                "$addToSet":    "$group_admin"
              }
              },},

              {  "$project": {
              '_id': 0,
              'total': '$count',
              "user_ids": {
                  "$cond":    [
                      {
                          "$eq":  [
                              "$author_set",
                              []
                          ]
                      },
                      [],
                      "$author_set"
                  ]
              },
              "admin_ids": {
                  "$cond":    [
                      {
                          "$eq":  [
                              "$group_admin",
                              []
                          ]
                      },
                      [],
                      "$group_admin"
                  ]
              }

              }
              }
            ])

            for e in rec['result']:
                print e
                user_ids_lists = e['user_ids']
                admin_ids_lists = e['admin_ids']

            user_id_list = reduce(operator.concat, user_ids_lists)
            
            admin_id_list = reduce(operator.concat, admin_ids_lists)
            non_admin_user_id_list = list(set(user_id_list) - set(admin_id_list))
            non_admin_user_id_list = [x for x in non_admin_user_id_list if x is not None]
            print "user_ids", non_admin_user_id_list
            
            if non_admin_user_id_list:
              log_file.write("Users ids: " + str(non_admin_user_id_list))
            
            log_file.write("\n********************************")
            log_file.write("delete_user_artifacts getting triggered")
            delete_user_artifacts(non_admin_user_id_list)
              #get_counter_ids(user_ids=user_id_list)
              
            else:
              log_file.write("No users with non-admin rights found.")
          except Exception as user_artifacts_cleaning_err:
            log_file.write("Error occurred: " + str(user_artifacts_cleaning_err))
            pass
          finally:
            log_file.write("\n*************************************************************")
            log_file.write("\n######### Script Completed at : " + str(datetime.datetime.now()) + " #########\n\n")
            print "\nSTART : ", str(datetimestamp)
            print "\nEND : ", str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            print "*"*70
            print "\n Log will be found at: ", log_file_path
            print "*"*70
            log_file.close()
            call_exit()
        else:
          call_exit()



# Pending:
# - check for grelation `profile_pic` and other to take decision of which object to keep