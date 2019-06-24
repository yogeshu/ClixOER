
import datetime
import time
import subprocess
import re
import ast
import string
import json
import locale

from bson import ObjectId

def get_node_by_id(node_id):
    '''
        Takes ObjectId or objectId as string as arg
            and return object
    '''
    if node_id:
        q = eval("Q('match', id = node_id)")

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute()
        return s2[0]

        # return node_collection.one({'_id': ObjectId(node_id)})
    else:
        # raise ValueError('No object found with id: ' + str(node_id))
        return None

def get_nodes_by_ids_list(node_id_list):
    '''
        Takes list of ObjectIds or objectIds as string as arg
            and return list of object
    '''
    # try:
    #     node_id_list = map(ObjectId, node_id_list)
    # except:
    #     node_id_list = [ObjectId(nid) for nid in node_id_list if nid]
    if node_id_list:
        q = eval("Q('terms', id = node_id_list)")
        print q
        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute()
        return s2
        # return node_collection.find({'_id': {'$in': node_id_list}})
    else:
        return None


def get_node_obj_from_id_or_obj(node_obj_or_id, expected_type):
    # confirming arg 'node_obj_or_id' is Object or oid and
    # setting node_obj accordingly.
    node_obj = None

    if node_obj_or_id.type == expected_type:
        node_obj = node_obj_or_id
    elif isinstance(node_obj_or_id,ObjectId):
        q = eval("Q('match', id = node_id)")

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute() 
        node_obj = s2[0]
    else:
        # error raised:
        raise RuntimeError('No Node class instance found with provided arg for get_node_obj_from_id_or_obj(' + str(node_obj_or_id) + ', expected_type=' + str(expected_type) + ')')

    return node_obj

def get_group_name_id(group_name_or_id, get_obj=False):
    '''
      - This method takes possible group name/id as an argument and returns (group-name and id) or group object.

      - If no second argument is passed, as method name suggests, returned result is "group_name" first and "group_id" second.

      - When we need the entire group object, just pass second argument as (boolian) True. In the case group object will be returned.

      Example 1: res_group_name, res_group_id = get_group_name_id(group_name_or_id)
      - "res_group_name" will contain name of the group.
      - "res_group_id" will contain _id/ObjectId of the group.

      Example 2: res_group_obj = get_group_name_id(group_name_or_id, get_obj=True)
      - "res_group_obj" will contain entire object.

      Optimization Tip: before calling this method, try to cast group_id to ObjectId as follows (or copy paste following snippet at start of function or wherever there is a need):
      try:
          group_id = ObjectId(group_id)
      except:
          group_name, group_id = get_group_name_id(group_id)

    '''
    # if cached result exists return it
    if not get_obj:
        slug = slugify(group_name_or_id)
        # for unicode strings like hindi-text slugify doesn't works
        cache_key = 'get_group_name_id_' + str(slug) if slug else str(abs(hash(group_name_or_id)))
        cache_result = cache.get(cache_key)

        if cache_result:
            return (cache_result[0], ObjectId(cache_result[1]))
    # ---------------------------------

    # case-1: argument - "group_name_or_id" is ObjectId
    if ObjectId.is_valid(group_name_or_id):
        q = eval("Q('match', id = node_id)")

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute() 
        group_obj = s2[0]
        # group_obj = node_collection.one({"_id": ObjectId(group_name_or_id)})

        # checking if group_obj is valid
        if group_obj:
            # if (group_name_or_id == group_obj._id):
            group_id = group_name_or_id
            group_name = group_obj.name

            if get_obj:
                return group_obj
            else:
                # setting cache with both ObjectId and group_name
                cache.set(cache_key, (group_name, group_id), 60 * 60)
                cache_key = u'get_group_name_id_' + slugify(group_name)
                cache.set(cache_key, (group_name, group_id), 60 * 60)
                return group_name, group_id

    # case-2: argument - "group_name_or_id" is group name
    else:
        q = eval("Q('bool',must =[Q('match', name = group_name_or_id), Q('terms', type = [Group, Author])]")

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute() 
        group_obj = s2[0]
        # group_obj = node_collection.one(
        #     {"_type": {"$in": ["Group", "Author"]}, "name": unicode(group_name_or_id)})

        # checking if group_obj is valid
        if group_obj:
            # if (group_name_or_id == group_obj.name):
            group_name = group_name_or_id
            group_id = group_obj._id

            if get_obj:
                return group_obj
            else:
                # setting cache with both ObjectId and group_name
                cache.set(cache_key, (group_name, group_id), 60*60)
                cache_key = u'get_group_name_id_' + slugify(group_name)
                cache.set(cache_key, (group_name, group_id), 60*60)
                return group_name, group_id

    if get_obj:
        return None
    else:
        return None, None