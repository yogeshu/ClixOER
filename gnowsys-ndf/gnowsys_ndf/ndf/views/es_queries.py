
import datetime
import time
import subprocess
import re
import ast
import string
import json
import locale
from django.template.defaultfilters import slugify
from django.core.cache import cache
from bson import ObjectId
from gnowsys_ndf.ndf.gstudio_es.es import *

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
        q = eval("Q('bool',must =[Q('match', name = group_name_or_id), Q('terms', type = ['Group', 'Author'])])")

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
            group_id = group_obj.id

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

def get_group_type(group_id, user):
    """This function checks for url's authenticity
    
    """

    print "in get_group_type function"
    try:
        # Splitting url-content based on backward-slashes
        split_content = group_id.strip().split("/")

        # Holds primary key, group's ObjectId or group's name
        g_id = ""
        if split_content[0] != "":
            g_id = split_content[0]
        else:
            g_id = split_content[1]

        group_node = None

        if g_id.isdigit() and 'dashboard' in group_id:
            # User Dashboard url found
            u_id = int(g_id)
            user_obj = User.objects.get(pk=u_id)

            if not user_obj.is_active:
                error_message = "\n Something went wrong: Either url is invalid or such group/user doesn't exists !!!\n"
                raise Http404(error_message)

        else:
            # Group's url found
            if ObjectId.is_valid(g_id):
                # Group's ObjectId found
                q = eval("Q('bool',must =[Q('match', id = ObjectId(g_id)), Q('terms', type = ['Group', 'Author'])])")

                # q = Q('match',name=dict(query='File',type='phrase'))
                s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                s2 = s1.execute() 
                group_node = s2[0]
                
                # group_node = node_collection.one({'_type': {'$in': ["Group", "Author"]}, '_id': ObjectId(g_id)})

            else:
                # Group's name found

                q = eval("Q('bool',must =[Q('match', name = g_id), Q('terms', type = ['Group', 'Author'])])")

                # q = Q('match',name=dict(query='File',type='phrase'))
                s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                s2 = s1.execute()
                group_node = s2[0]
                # group_node = node_collection.one({'_type': {'$in': ["Group", "Author"]}, 'name': g_id})

            if group_node:
                # Check whether Group is PUBLIC or not
                if not group_node.group_type == u"PUBLIC":
                    # If Group other than Public one is found

                    if user.is_authenticated():
                        # Check for user's authenticity & accessibility of the group
                        if user.is_superuser or group_node.created_by == user.id or user.id in group_node.group_admin or user.id in group_node.author_set:
                            pass

                        else:
                            error_message = "\n Something went wrong: Either url is invalid or such group/user doesn't exists !!!\n"
                            raise PermissionDenied(error_message)

                    else:
                        # Anonymous user found which cannot access groups other than Public
                        error_message = "\n Something went wrong: Either url is invalid or such group/user doesn't exists !!!\n"
                        raise PermissionDenied(error_message)

            else:
                # If Group is not found with either given ObjectId or name in the database
                # Then compare with a given list of names as these were used in one of the urls
                # And still no match found, throw error
                if g_id not in ["online", "i18n", "raw", "r", "m", "t", "new", "mobwrite", "admin", "benchmarker", "accounts", "Beta", "welcome", "explore"]:
                    error_message = "\n Something went wrong: Either url is invalid or such group/user doesn't exists !!!\n"
                    raise Http404(error_message)

        return True

    except PermissionDenied as e:
        raise PermissionDenied(e)

    except Http404 as e:
        raise Http404(e)


def get_attribute_value(node_id, attr_name, get_data_type=False, use_cache=True):
    print "in get_attribute_value"
    cache_key = str(node_id) + 'attribute_value' + str(attr_name)
    cache_result = cache.get(cache_key)

    # if (cache_key in cache) and not get_data_type and use_cache:
    #     #print "from cache in module detail:", cache_result
    #     return cache_result

    attr_val = ""
    node_attr = data_type = None
    if node_id:
        # print "\n attr_name: ", attr_name
        # gattr = node_collection.one({'_type': 'AttributeType', 'name': unicode(attr_name) })
        
        q = eval("Q('bool',must =[Q('match', type = 'AttributeType'), Q('match', name = attr_name)])")

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute()

        gattr = s2[0]

        if get_data_type:
            data_type = gattr.data_type
        if gattr: # and node  :

            # node_attr = triple_collection.find_one({'_type': "GAttribute", "subject": ObjectId(node_id), 'attribute_type': gattr._id, 'status': u"PUBLISHED"})
            print node_id,gattr.id
            q = eval("Q('bool',must =[Q('match', type = 'GAttribute'), Q('match', subject = node_id), Q('match',attribute_type = gattr.id)])")

            # q = Q('match',name=dict(query='File',type='phrase'))
            s1 = Search(using=es, index='triples',doc_type="triple").query(q)
            s2 = s1.execute()
            print "s2:",s2
            node_attr = s2[0]
            print "node attr:",node_attr
    if node_attr:
        attr_val = node_attr.object_value
        print "\n here: ", attr_name, " : ", type(attr_val), " : ", attr_val
    if get_data_type:
        return {'value': attr_val, 'data_type': data_type}
    cache.set(cache_key, attr_val, 60 * 60)
    return attr_val

def get_gst_name_id(gst_name_or_id):
    # if cached result exists return it
    print "in gst_name_or_id"
    slug = slugify(gst_name_or_id)
    cache_key = 'gst_name_id' + str(slug)
    cache_result = cache.get(cache_key)

    if cache_result:
        return (cache_result[0], ObjectId(cache_result[1]))
    # ---------------------------------

    # gst_id = ObjectId(gst_name_or_id) if ObjectId.is_valid(gst_name_or_id) else None
    
    # gst_obj = node_collection.one({
    #                                 "_type": {"$in": ["GSystemType", "MetaType"]},
    #                                 "$or":[
    #                                     {"_id": gst_id},
    #                                     {"name": unicode(gst_name_or_id)}
    #                                 ]
    #                             })
    if isinstance(gst_name_or_id,ObjectId):
        q2 = Q('match',id=gst_name_or_id)
    else:
        q2 = Q('match',name=gst_name_or_id)

    q = eval("Q('bool',must =[Q('terms', type = ['GSystemType','MetaType']),q2])")

    # q = Q('match',name=dict(query='File',type='phrase'))
    s1 = Search(using=es, index='triples',doc_type="node").query(q)
    s2 = s1.execute()
    print "s2",s2
    gst_obj = s2[0]
    print "Object:",gst_obj
    if gst_obj:
        gst_name = gst_obj.name
        gst_id = gst_obj.id

        # setting cache with ObjectId
        cache_key = u'gst_name_id' + str(slugify(gst_id))
        cache.set(cache_key, (gst_name, gst_id), 60 * 60)

        # setting cache with gst_name
        cache_key = u'gst_name_id' + str(slugify(gst_name))
        cache.set(cache_key, (gst_name, gst_id), 60 * 60)

        return gst_name, gst_id

    return None, None