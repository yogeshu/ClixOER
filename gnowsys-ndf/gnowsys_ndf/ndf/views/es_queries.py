
import datetime
import time
import subprocess
import re
import ast
import string
import json
import locale

from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response  # , render
from django.template.loader import render_to_string

from django.template import RequestContext
from django.template.defaultfilters import slugify
from gnowsys_ndf.ndf.gstudio_es.paginator import Paginator ,EmptyPage, PageNotAnInteger

from django.core.cache import cache
from bson import ObjectId
from gnowsys_ndf.ndf.gstudio_es.es import *
from gnowsys_ndf.settings import LANGUAGES,OTHER_COMMON_LANGUAGES,EMAIL_HOST_USER
from django.shortcuts import render_to_response
from django.template import RequestContext
from gnowsys_ndf.ndf.models import GSystemType, Group, Node, GSystem, Buddy, Counter  #, Triple
from gnowsys_ndf.ndf.models import node_collection

from gnowsys_ndf.ndf.models import GSystemType

gfs = HashFS('/data/media/', depth=3, width=1, algorithm='sha256')

def help(request,group_id):
    template = 'ndf/help.html'
    return render_to_response(template, {'group_id':group_id},
                                context_instance=RequestContext(request))
 
def help_videos(request,group_id):
    node_id = request.POST.get('node_id')
    print 'inside help_videos',node_id
    with open('/home/docker/code/clixoer/gnowsys-ndf/gnowsys_ndf/ndf/static/ndf/module.json','r') as fd:
        json_data = json.load(fd)
    nd = get_node_by_id(node_id)
    videos = json_data[nd.name]
    print "videos:",videos
    template = 'ndf/thehelpmodal.html'
    return render_to_response(template, {'group_id':group_id , 'videos':videos})
   

def get_file(md5_or_relurl=None):

    file_blob = None
    
    try:
        if md5_or_relurl:
            file_blob = gfs.open(md5_or_relurl)
    except Exception as e:
        print "File '", md5_or_relurl, "' not found: ", e
            
    return file_blob

def readDoc(request, id, group_id, file_name=""):
    '''Return Files
    '''
    try:
        group_id = ObjectId(group_id)
    except:
        group_name, group_id = get_group_name_id(group_id)


    file_node = get_node_by_id(id)


    if file_node is not None:

        if file_node.if_file.original.relurl:
            # print "md5_or_relurl : ", file_node.if_file.original
            return HttpResponse(get_file(file_node.if_file.original.relurl),
                                content_type=file_node.if_file.mime_type)
    else:
        return HttpResponse("")


def about(request,group_id):
    template = 'ndf/about.html'
    return render_to_response(template, {'group_id':group_id},
                                context_instance=RequestContext(request)   )


def send_message(request,group_id):
    #template = 'ndf/about.html'
    #return render_to_response(template, {'group_id':group_id})
    from django.core.mail import send_mail, EmailMultiAlternatives
    from django.contrib import messages
    print "send message"
    print request
    print request.POST
    subject = 'Feedback message'
    domain = request.POST.get('domain','')
    if domain == '':
        domain = 'About'
    message = 'feedback received for'+domain
    c = {'email': request.POST['email'],
                 'first_name': request.POST['first_name'],'last_name':request.POST['last_name'],'domain':request.POST['domain'],'message':request.POST['message']}
    email_from = EMAIL_HOST_USER
    recipient_list = ['satej_shende@tiss.edu']
    html_content = render_to_string('ndf/html_message.html', c)
    msg = EmailMultiAlternatives(subject, message,email_from, recipient_list)

    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)
    messages.success(request, 'Your feedback sent successfully!')
    if domain != 'About':
        return HttpResponseRedirect( reverse('domain_page', kwargs={"group_id": group_id,"domain_name":request.POST['domain']}) )
    else:
        return HttpResponseRedirect( reverse('about', kwargs={"group_id": group_id}) )


def domain_help(request,group_id,domain_name):
    print "inside domain help",domain_name
    if domain_name == 'English':
        template = 'ndf/theEDhelp.html'

    if domain_name == 'Mathematics':
        template = 'ndf/theMDhelp.html'

    if domain_name == 'Science':
        template = 'ndf/theSDhelp.html'

    return render_to_response(template, {'group_id':group_id,'domain_name':domain_name},
                                context_instance=RequestContext(request)   )


def loadDesignDevelopment(request,group_id,domain_name):
    print "inside Design Development:",domain_name
    if domain_name == 'English':
        template = 'ndf/ED.html'
       
    if domain_name == 'Mathematics':
        template = 'ndf/MD.html'
       
    if domain_name == 'Science':
        template = 'ndf/SD.html'
    
    return render_to_response(template, {'group_id':group_id,'domain_name':domain_name},
                                context_instance=RequestContext(request)   )


def uploadDoc(request, group_id):
    print "inside"
    
    group_name, group_id = get_group_name_id(group_id)

    print "inside upload doc",group_name,group_id
    
    if request.method == "GET":
        template = "ndf/cmspage.html"

    variable = RequestContext(request, {'groupid':group_id,'group_id':group_id})
    return render_to_response(template, variable)


def upload_using_save_file(request,group_id):
    from gnowsys_ndf.ndf.views.file import save_file
    try:
        group_id = ObjectId(group_id)
    except:
        group_name, group_id = get_group_name_id(group_id)

    group_obj = node_collection.one({'_id': ObjectId(group_id)})
    title = request.POST.get('context_name','')
    sel_topic = request.POST.get('topic_list','')
    
    usrid = request.user.id
    name  = request.POST.get('name')

    from gnowsys_ndf.ndf.views.filehive import write_files
    is_user_gstaff = check_is_gstaff(group_obj._id, request.user)
    content_org = request.POST.get('content_org', '')
    uploaded_files = request.FILES.getlist('filehive', [])
    # gs_obj_list = write_files(request, group_id)
    # fileobj_list = write_files(request, group_id)
    # fileobj_id = fileobj_list[0]['_id']
    fileobj_list = write_files(request, group_id,unique_gs_per_file=False)
    # fileobj_list = write_files(request, group_id)
    fileobj_id = fileobj_list[0]['_id']
    file_node = node_collection.one({'_id': ObjectId(fileobj_id) })

    discussion_enable_at = node_collection.one({"_type": "AttributeType", "name": "discussion_enable"})
    for each_gs_file in fileobj_list:
        #set interaction-settings
        each_gs_file.status = u"PUBLISHED"
        if usrid not in each_gs_file.contributors:
            each_gs_file.contributors.append(usrid)

        if title == "raw material" or (title == "gallery" and is_user_gstaff):
            if u'raw@material' not in each_gs_file.tags:
                each_gs_file.tags.append(u'raw@material')

        group_object = node_collection.one({'_id': ObjectId(group_id)})
        if (group_object.edit_policy == "EDITABLE_MODERATED") and (group_object.moderation_level > 0):
            from gnowsys_ndf.ndf.views.moderation import get_moderator_group_set
            # print "\n\n\n\ninside editable moderated block"
            each_gs_file.group_set = get_moderator_group_set(each_gs_file.group_set, group_object._id)
            # print "\n\n\npage_node._id",page_node._id
            each_gs_file.status = u'MODERATION'
            # print "\n\n\n page_node.status",page_node.status
        each_gs_file.save()
        create_gattribute(each_gs_file._id, discussion_enable_at, True)
        return_status = create_thread_for_node(request,group_obj._id, each_gs_file)

    if title == "gallery" and not is_user_gstaff:
        return HttpResponseRedirect(reverse('course_gallery', kwargs={'group_id': group_id}))
    elif title == "raw material" or (title == "gallery" and is_user_gstaff):
        return HttpResponseRedirect(reverse('course_raw_material', kwargs={'group_id': group_id}))
    else:
        return HttpResponseRedirect( reverse('file_detail', kwargs={"group_id": group_id,'_id':fileobj_id}))
    # return HttpResponseRedirect(url_name)

def write_files(request, group_id, make_collection=False, unique_gs_per_file=True, **kwargs):

    user_id = request.user.id
    try:
        user_id = Author.extract_userid(request, **kwargs)
    except Exception as e:
        pass
    # print "user_id: ", user_id

    # author_obj = node_collection.one({'_type': u'Author', 'created_by': int(user_id)})
    author_obj = Author.get_author_obj_from_name_or_id(user_id)
    author_obj_id = author_obj._id
    kwargs['created_by'] = user_id

    group_name, group_id = get_group_name_id(group_id)

    first_obj      = None
    collection_set = []
    uploaded_files = request.FILES.getlist('filehive', [])
    name           = request.POST.get('name')

    gs_obj_list    = []
    for each_file in uploaded_files:

        gs_obj = node_collection.collection.GSystem()

        language = request.POST.get('language', GSTUDIO_SITE_DEFAULT_LANGUAGE)
        language = get_language_tuple(language)

        group_set = [ObjectId(group_id), ObjectId(author_obj_id)]

        if name and not first_obj and (name != 'untitled'):
            file_name = name
        else:
            file_name = each_file.name if hasattr(each_file, 'name') else name

        existing_file_gs = gs_obj.fill_gstystem_values(request=request,
                                    name=file_name,
                                    group_set=group_set,
                                    language=language,
                                    uploaded_file=each_file,
                                    unique_gs_per_file=unique_gs_per_file,
                                    **kwargs)
        # print "existing_file_gs",existing_file_gs
        if (gs_obj.get('_id', None) or existing_file_gs.get('_id', None)) and \
           (existing_file_gs.get('_id', None) == gs_obj.get('_id', None)):
            if gst_file_id not in gs_obj.member_of:
                gs_obj.member_of.append(gst_file_id)

            gs_obj.save(groupid=group_id,validate=False)

            if 'video' in gs_obj.if_file.mime_type:
                convertVideo.delay(user_id, str(gs_obj._id), file_name)
            if not first_obj:
                first_obj = gs_obj
            else:
                collection_set.append(gs_obj._id)

            gs_obj_list.append(gs_obj)
        elif existing_file_gs:
                gs_obj_list.append(existing_file_gs)

    if make_collection and collection_set:
        first_obj.collection_set = collection_set
        first_obj.save()

    return gs_obj_list

    # return render_to_response('ndf/filehive.html', {
    #   'group_id': group_id, 'groupid': group_id,
    #   }, context_instance=RequestContext(request))


def domain_page(request,group_id,domain_name):
    import json
    print "es_queries domain page:",domain_name,request.session.session_key
    domain_id = get_name_id_from_type(domain_name,'Group')[1]
    print "domain id:",domain_id
    domainnd = get_node_by_id(domain_id)
    print "domain nd:",domainnd
    
    files = get_nodes_by_ids_list(list(domainnd.collection_set))
    print request.META["CSRF_COOKIE"]
    #CSRF_COOKIE = request.META["CSRF_COOKIE"]
    import os
    print "re",files,os.getcwd()
    with open('/home/docker/code/clixoer/gnowsys-ndf/gnowsys_ndf/ndf/static/ndf/employees.json','r') as json_file:
        employeedata = json.load(json_file)
    with open('/home/docker/code/clixoer/gnowsys-ndf/gnowsys_ndf/ndf/static/ndf/testimonial.json','r') as json_file:
        testimonydata = json.load(json_file)
    return render_to_response(
            "ndf/domain.html",
            {"employee":employeedata,"testimony":testimonydata,"files":files,"first_arg":domain_name,"group_id":group_id},context_instance=RequestContext(request)) 
    
def get_module_previewdata(request,group_id):

    '''
    ARGS: module_obj
    Result will be of following form:
    {
        name: 'Module1',
        grade : [],
        subject : science,
        unit_details: [
            {
                name: 'Unit 1',
                lessn: 'Lessn 1',
                activities: 10
            },
            {
                name: 'Unit 1',
                type: 'Lessn 2',
                activities: 10
            }
        ]
    }
    '''
    node_id = request.POST.get("node_id")

    print "in es-queries: get_module_previewdata",node_id,request.session.session_key
    node_obj = get_node_by_id(node_id)


    units = list(get_attribute_value(node_id,'items_sort_list'))
    print "unitnds:",units
    if len(units) == 0 :
        units = get_nodes_by_ids_list(node_obj.collection_set)

    #imgsrc = get_attribute_value(node_id,'has_banner_pic')
    # unitnds = get_nodes_by_ids_list(list(node_obj.collection_set))
    module_dict = {}

    module_dict['name'] = node_obj.altnames
    module_dict['grade'] = get_attribute_value(node_id,'educationallevel')
    module_dict['subject'] = get_attribute_value(node_id,'educationalsubject')
    module_dict['image'] = get_relation_value(node_id,'has_banner_pic')
    module_dict['content'] = node_obj.content
    module_dict['unitdetails'] = []
    module_dict['id'] = node_obj.id
    module_dict['grade'] = [str(each) for each in module_dict['grade']]
    q= eval("Q('bool', must=[Q('match', type = 'GSystemType'), Q('match',name='File')])")
    GST_FILE = (Search(using=es,index = 'nodes',doc_type='node').query(q)).execute()
    
    q= eval("Q('bool', must=[Q('match', type = 'GSystemType'), Q('match',name='Page')])")
    GST_PAGE = (Search(using=es,index = 'nodes',doc_type='node').query(q)).execute()
    
    q= eval("Q('bool', must=[Q('match', type = 'GSystemType'), Q('match',name='Jsmol')])")
    GST_JSMOL = (Search(using=es,index = 'nodes',doc_type='node').query(q)).execute()

    q = Q('bool',must=[Q('terms',member_of=[GST_FILE[0].id,GST_JSMOL[0].id,GST_PAGE[0].id]),Q('match',access_policy='PUBLIC'),Q('match_phrase',tags = 'Handbook'),Q('match_phrase',tags = module_dict['name'].split()[0]),Q('match_phrase',tags = 'Student')])

    alldocs1 = (Search(using=es,index = 'nodes',doc_type='node').query(q)).sort({"last_update" : {"order" : "desc"}})
    
    alldocs2 = alldocs1.execute()

    print "document count:",alldocs1.count()
    student_docs = {}
    if alldocs1.count() > 0 :
        for each in alldocs2:
            student_docs[str(each.language[1])]='/media/'+str(each.if_file.original.relurl)
    print "docs:",student_docs
    
    q = Q('bool',must=[Q('terms',member_of=[GST_FILE[0].id,GST_JSMOL[0].id,GST_PAGE[0].id]),Q('match',access_policy='PUBLIC'),Q('match_phrase',tags = 'Handbook'),Q('match_phrase',tags = module_dict['name'].split()[0]),Q('match_phrase',tags = 'Teacher')])

    alldocs1 = (Search(using=es,index = 'nodes',doc_type='node').query(q)).sort({"last_update" : {"order" : "desc"}})
    alldocs2 = alldocs1.execute()
    
    teacher_docs = {}
    
    if alldocs1.count() > 0 :
        for each in alldocs2:
            teacher_docs[str(each.language[1])]='/media/'+str(each.if_file.original.relurl)
    print "docs:",teacher_docs
    q1 = []
    for each in str(module_dict['name']).split():
        q1.append(Q('match_phrase', tags = each))

    q = Q('bool',must=[Q('terms',member_of=[GST_FILE[0].id,GST_JSMOL[0].id,GST_PAGE[0].id]),Q('match',access_policy='PUBLIC'),Q('terms',language = ['english']  ),Q('match_phrase',tags = 'Tool')],should = q1,minimum_should_match=1)
                
    allinteractives1 = (Search(using=es,index = 'nodes',doc_type='node').query(q)).sort({"last_update" : {"order" : "desc"}})

    allinteractives2 = allinteractives1.execute()

    with open('/home/docker/code/clixoer/gnowsys-ndf/gnowsys_ndf/ndf/static/ndf/theInteractive.json','r') as json_file:
        tooldata = json.load(json_file)
    interactives_data ={}
    for each in allinteractives1:
        interactives_data[str(each.name)] = tooldata[str(each.name)]['Interactive_href']

    print q,allinteractives1.count(),interactives_data

    for each in units:
        lessnnds = get_nodes_by_ids_list(list(each.collection_set))
        lessnnds = sorted(lessnnds, key=lambda nd: nd.last_update)
        print "lessnnds:",lessnnds
        for lessn in lessnnds:
            unitdict = {}
            unitdict['name'] = each.altnames
            # print "lessnnds:",each.collection_set
            print "lessn name:",str(lessn.name).encode('utf-8')
            unitdict['lessname'] = str(lessn.name).encode('utf-8')
            unitdict['totalactivities'] = len(list(lessn.collection_set))
            module_dict['unitdetails'].append(unitdict) 
    print "module details:",module_dict

    return render_to_response('ndf/Emodule_preview.html',
            {
                'group_id': group_id, 'groupid': group_id,
                'moduledetails':module_dict, 'student_docs':student_docs,'teacher_docs':teacher_docs, 'interactivestotal':allinteractives1.count(), 'toolsdata':interactives_data
            },
            context_instance=RequestContext(request))

def get_node_by_id(node_id):
    '''
        Takes ObjectId or objectId as string as arg
            and return object
    '''
    print "node id:",node_id
    if node_id:
        q = eval("Q('match', id = str(node_id))")

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute()
        print "get_node_by_id s2",s2,q
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
        node_id_list = [str(each) for each in node_id_list]
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
        q = eval("Q('match', id = group_name_or_id)")

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
            q = eval("Q('bool',must =[Q('match', type = 'GAttribute'), Q('match', subject = str(node_id)), Q('match',attribute_type = str(gattr.id))])")

            # q = Q('match',name=dict(query='File',type='phrase'))
            s1 = Search(using=es, index='triples',doc_type="triple").query(q)
            s2 = s1.execute()
            print "s2:",s2,q
            if s1.count() > 0:
                node_attr = s2[0]
                attr_val = node_attr.object_value
                print "\n here: ", attr_name, " : ", type(attr_val), " : ", attr_val
                print "node attr:",node_attr
    if get_data_type:
        return {'value': attr_val, 'data_type': data_type}
    cache.set(cache_key, attr_val, 60 * 60)
    return attr_val

def get_gst_name_id(gst_name_or_id):
    # if cached result exists return it
    print "in gst_name_or_id",gst_name_or_id
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
        q2 = Q('match',id=str(gst_name_or_id))
    else:
        q2 = Q('match',name=gst_name_or_id)

    q = eval("Q('bool',must =[Q('terms', type = ['GSystemType','MetaType']),q2])")

    # q = Q('match',name=dict(query='File',type='phrase'))
    s1 = Search(using=es, index='nodes',doc_type="node").query(q)
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

def save_node_to_es(django_document):
    try:
        print "called to save_to_es method of es_queries"
        # node_types = ['GSystemType','MetaType','AttributeType','RelationType','GSystem']
        with open("/home/docker/code/gstudio/gnowsys-ndf/gnowsys_ndf/gstudio_configs/req_body.json") as req_body:
            request_body = json.load(req_body)
        
        doc = json.dumps(django_document,cls=NodeJSONEncoder)
        print "00000000000000000000000000000000000000000000000"
        print doc
        print "00000000000000000000000000000000000000000000000"
        django_document = json.loads(doc)
        print "================================================="
        print django_document
        print "================================================="

        django_document["id"] = django_document.pop("_id")
        django_document["type"] = django_document.pop("_type")

        index = None

        for k in GSTUDIO_ELASTIC_SEARCH_INDEX:
            for v in GSTUDIO_ELASTIC_SEARCH_INDEX[k]:
                if django_document["type"] in v:
                    if GSTUDIO_SITE_NAME == "CLIx":            
                        doc = json.dumps(django_document,cls=NodeJSONEncoder)
                        index = k
                    else:
                        index = GSTUDIO_SITE_NAME+"_"+k
                    index = index.lower()
                    break

        print django_document["type"]
        # if django_document["type"] == "GSystem" and GSTUDIO_SITE_NAME == "CLIx":
        #     print django_document["id"]
        #     print "-------------------------------------------------------------"
        #     es.index(index=index, doc_type="gsystem", id=django_document["id"], body=django_document)
        #     file_name.write(document["id"] + '\n')
        #     if django_document["type"]=="GSystem":
        #         if('if_file' in django_document.keys()):
        #             if(django_document["if_file"]["mime_type"] is not None):
        #                 data = django_document["if_file"]["mime_type"].split("/")
        #                 doc_type = data[0]
        #             else:
        #                 doc_type = "notmedia"
        #         else:
        #             doc_type = "notmedia"

        #     else:
        #         doc_type = "dontcare"

        #     if (not es.indices.exists("gsystem")):
        #         res = es.indices.create(index="gsystem", body=request_body)
        #     es.index(index="gsystem", doc_type=doc_type, id=django_document["id"], body=django_document)

        # else:
        #     print django_document["id"]
        #     if (not es.indices.exists("benchmarks")):
        #         res = es.indices.create(index="benchmarks", body=benchmarks_body)

        es.index(index='nodes', doc_type='node', id=django_document["id"], body=django_document)

    except Exception as e:
        print "Error while saving data to ES: "+str(e)


def save_triple_to_es(django_document):
    try:
        print "called to save_to_es method of es_queries"
        # node_types = ['GSystemType','MetaType','AttributeType','RelationType','GSystem']
        with open("/home/docker/code/gstudio/gnowsys-ndf/gnowsys_ndf/gstudio_configs/triple.json") as req_body:
            request_body = json.load(req_body)
        
        doc = json.dumps(django_document,cls=NodeJSONEncoder)
        print "00000000000000000000000000000000000000000000000"
        print doc
        print "00000000000000000000000000000000000000000000000"
        django_document = json.loads(doc)
        print "================================================="
        print django_document
        print "================================================="

        django_document["id"] = django_document.pop("_id")
        django_document["type"] = django_document.pop("_type")

        index = None

        for k in GSTUDIO_ELASTIC_SEARCH_INDEX:
            for v in GSTUDIO_ELASTIC_SEARCH_INDEX[k]:
                if django_document["type"] in v:
                    if GSTUDIO_SITE_NAME == "CLIx":            
                        doc = json.dumps(django_document,cls=NodeJSONEncoder)
                        index = k
                    else:
                        index = GSTUDIO_SITE_NAME+"_"+k
                    index = index.lower()
                    break

        print django_document["type"]
        # if django_document["type"] == "GSystem" and GSTUDIO_SITE_NAME == "CLIx":
        #     print django_document["id"]
        #     print "-------------------------------------------------------------"
        #     es.index(index=index, doc_type="gsystem", id=django_document["id"], body=django_document)
        #     file_name.write(document["id"] + '\n')
        #     if django_document["type"]=="GSystem":
        #         if('if_file' in django_document.keys()):
        #             if(django_document["if_file"]["mime_type"] is not None):
        #                 data = django_document["if_file"]["mime_type"].split("/")
        #                 doc_type = data[0]
        #             else:
        #                 doc_type = "notmedia"
        #         else:
        #             doc_type = "notmedia"

        #     else:
        #         doc_type = "dontcare"

        #     if (not es.indices.exists("gsystem")):
        #         res = es.indices.create(index="gsystem", body=request_body)
        #     es.index(index="gsystem", doc_type=doc_type, id=django_document["id"], body=django_document)

        # else:
        #     print django_document["id"]
        #     if (not es.indices.exists("benchmarks")):
        #         res = es.indices.create(index="benchmarks", body=benchmarks_body)

        es.index(index='triples', doc_type='triple', id=django_document["id"], body=django_document)

    except Exception as e:
        print "Error while saving data to ES: "+str(e)

def save_course_page(request, group_id):
    group_obj = get_group_name_id(group_id, get_obj=True)
    group_id = group_obj.id
    group_name = group_obj.name
    print "es_queries in save page",group_id,group_name
    tags = request.POST.get("tags",[])
    if tags:
        tags = json.loads(tags)
    else:
        tags = []    
    #template = 'ndf/gevent_base.html'
    template = 'ndf/lms.html'
    if not True:
        testimony_gst_name, testimony_gst_id = GSystemType.get_gst_name_id("testimony")
        testimony_obj = None
        activity_lang =  request.POST.get("lan", '')
        if request.method == "POST":
            name = request.POST.get("name", "")
            alt_name = request.POST.get("alt_name", "")
            content = request.POST.get("content_org", None)
            node_id = request.POST.get("node_id", "")
            if node_id:
                testimony_obj = node_collection.one({'_id': ObjectId(node_id)})
                if testimony_obj.altnames != alt_name:
                    testimony_obj.altnames = unicode(alt_name)
            else:
                # is_info_testimony = request.POST.get("testimony_type", "")
                testimony_obj = node_collection.collection.GSystem()
                testimony_obj.fill_gstystem_values(request=request)
                testimony_obj.member_of = [testimony_gst_id]
                testimony_obj.altnames = unicode(alt_name)
                # if is_info_testimony == "Info":
                #     info_testimony_gst_name, info_testimony_gst_id = GSystemType.get_gst_name_id('Info testimony')
                #     testimony_obj.type_of = [info_testimony_gst_id]
            
            if activity_lang:
                language = get_language_tuple(activity_lang)
                testimony_obj.language = language
            # if 'admin_info_page' in request.POST:
            #     admin_info_page = request.POST['admin_info_page']
            #     if admin_info_page:
            #         admin_info_page = json.loads(admin_info_page)
            #     if "None" not in admin_info_page:
            #         has_admin_rt = node_collection.one({'_type': "RelationType", 'name': "has_admin_page"})
            #         admin_info_page = map(ObjectId, admin_info_page)
            #         create_grelation(page_obj._id, has_admin_rt,admin_info_page)
            #         page_obj.reload()
            #     return HttpResponseRedirect(reverse("view_course_page",
            #      kwargs={'group_id': group_id, 'page_id': page_obj._id}))

            # if 'help_info_page' in request.POST:
            #     help_info_page = request.POST['help_info_page']
            #     if help_info_page:
            #         help_info_page = json.loads(help_info_page)
            #     if "None" not in help_info_page:
            #         has_help_rt = node_collection.one({'_type': "RelationType", 'name': "has_help"})
            #         help_info_page = map(ObjectId, help_info_page)
            #         create_grelation(page_obj._id, has_help_rt,help_info_page)
            #         page_obj.reload()
            #     return HttpResponseRedirect(reverse("view_course_page",
            #      kwargs={'group_id': group_id, 'page_id': page_obj._id}))
            testimony_obj.fill_gstystem_values(tags=tags)
            testimony_obj.name = unicode(name)
            testimony_obj.content = unicode(content)
            testimony_obj.created_by = request.user.id
            testimony_obj.save(groupid=group_id)
            return HttpResponseRedirect(reverse("view_course_page",
             kwargs={'group_id': group_id, 'page_id': testimony_obj.id}))
    else:
        page_gst_name, page_gst_id = get_gst_name_id("Page")
        page_obj = None
        activity_lang =  request.POST.get("lan", '')
        if request.method == "POST":
            name = request.POST.get("name", "")
            alt_name = request.POST.get("alt_name", "")
            content = request.POST.get("content_org", None)
            node_id = request.POST.get("node_id", "")
            if node_id:
                page_obj = node_collection.one({'_id': ObjectId(node_id)})
                q = eval("Q('match', id = str(node_id))")

                # q = Q('match',name=dict(query='File',type='phrase'))
                s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                s2 = s1.execute()
                if page_obj.altnames != alt_name:
                    page_obj.altnames = unicode(alt_name)
            else:
                is_info_page = request.POST.get("page_type", "")
                page_obj = node_collection.collection.GSystem()
                page_obj.fill_gstystem_values(request=request)
                page_obj.member_of = [page_gst_id]
                page_obj.altnames = unicode(alt_name)
                
            
            if activity_lang:
                language = get_language_tuple(activity_lang)
                page_obj.language = language
            
            page_obj.fill_gstystem_values(tags=tags)
            page_obj.name = unicode(name)
            page_obj.content = unicode(content)
            page_obj.created_by = request.user.id
            page_obj.save(groupid=group_id)
            print "page_object saved:",page_obj
            save_node_to_es(page_obj)
            return HttpResponseRedirect(reverse("view_course_page",
             kwargs={'group_id': group_id, 'page_id': page_obj.id}))


def module_detail(request, group_id, node_id,title=""):
    '''
    detail of of selected module
    '''
    group_name, group_id = Group.get_group_name_id(group_id)
    print "in module_detail and group id, title",group_id,title
    print "node_id",node_id          
    module_obj = Node.get_node_by_id(ObjectId(node_id))
    context_variable = {
                        'group_id': group_id, 'groupid': group_id,
                        'node': module_obj, 'title': title,
                        'card': 'ndf/event_card.html', 'card_url_name': 'groupchange'
                    }

    gstaff_access = check_is_gstaff(group_id,request.user)
    primary_lang_tuple = get_language_tuple(GSTUDIO_PRIMARY_COURSE_LANGUAGE)
    if title == "courses":

        module_detail_query = Q('bool',must = [Q('match',status = 'PUBLISHED'),Q('terms',module_obj.collection_set)],\
            should=[Q('match',group_admin =request.user.id),Q('match',created_by =request.user.id),Q('match',author_set =request.user.id),Q('match',member_of =gst_ce_id),Q('match',member_of =gst_announced_unit_id),\
            Q('match',group_type ='PUBLIC'),Q('match',language=primary_lang_tuple),Q('match',member_of=gst_ce_id)],minimum_should_match=1)
    
    if title == "drafts":
        module_detail_query.update({'$or': [
        {'$and': [
            {'member_of': gst_base_unit_id},
            {'$or': [
              {'created_by': request.user.id},
              {'group_admin': request.user.id},
              {'author_set': request.user.id},
            ]}
        ]},
      ]}) 

    # units_under_module = Node.get_nodes_by_ids_list(module_obj.collection_set)
    '''
    gstaff_access = check_is_gstaff(group_id, request.user)

    if gstaff_access:
        module_detail_query.update({'member_of': {'$in': [gst_announced_unit_id, gst_base_unit_id]}})
    else:
        module_detail_query.update({'member_of': gst_announced_unit_id})
    '''
    units_under_module = node_collection.find(module_detail_query).sort('last_update', -1)
    context_variable.update({'units_under_module': units_under_module})

    units_sort_list = get_attribute_value(node_id, 'items_sort_list')
    from django.core.cache import cache
    test = cache.get('5945db6e2c4796014abd1784attribute_valueitems_sort_list')
    print "test:",test 
    if units_sort_list:
        #print "from attribute:",units_sort_list
        context_variable.update({'units_sort_list': units_sort_list})
    else:
        print "no items_sort_list"
        context_variable.update({'units_sort_list': list(units_under_module)})

    template = 'ndf/module_detail.html'
    print "units of selected module", units_sort_list
    return render_to_response(
        template,
        context_variable,
        context_instance=RequestContext(request))

def member_of_names_list(group_obj):
        """Returns a list having names of each member (GSystemType, i.e Page,
        File, etc.), built from 'member_of' field (list of ObjectIds)

        """
        # from gsystem_type import GSystemType
        return [get_gst_name_id(ObjectId(gst_id))[0] for gst_id in group_obj.member_of]

def _get_current_and_old_display_pics(group_obj):

    # has_banner_pic_rt = node_collection.one({'_type': 'RelationType', 'name': unicode('has_banner_pic') })

    q = Q('bool',must=[Q('match', type = 'RelationType'),Q('match',name = 'has_banner_pic')])

    # q = Q('match',name=dict(query='File',type='phrase'))
    s1 = Search(using=es, index='nodes',doc_type="node").query(q)
    s2 = s1.execute()
    has_banner_pic_rt = s2[0]

    banner_pic_obj = None
    old_profile_pics = []
    for each in group_obj.relation_set:
        if "has_banner_pic" in each:
            # banner_pic_obj = node_collection.one(
            #     {'_type': {'$in':     activity_gst_name, activity_gst_id = get_gst_name_id("activity")
            #       ["GSystem", "File"]}, '_id': each["has_banner_pic"]}
            # )
            q = Q('bool',must=[Q('match', id = str(each["has_banner_pic"])),Q('terms',type = ["GSystem", "File"])])

            # q = Q('match',name=dict(query='File',type='phrase'))
            s1 = Search(using=es, index='nodes',doc_type="node").query(q)
            s2 = s1.execute()
            banner_pic_obj = s2[0]
            break

    # all_old_prof_pics = triple_collection.find({'_type': "GRelation", "subject": group_obj._id, 'relation_type': has_banner_pic_rt._id, 'status': u"DELETED"})
    
    q = Q('bool',must=[Q('match', type = 'GRelation'), Q('match', subject = str(group_obj.id)), Q('match', relation_type = str(has_banner_pic_rt.id))])
    s1 = Search(using=es, index='triples',doc_type="triple").query(q)

    # print "s1:",s1,q
    all_old_prof_pics = s1.execute()

    if all_old_prof_pics:
        for each_grel in all_old_prof_pics:
            if each_grel.status == 'DELETED':
                # n = node_collection.one({'_id': ObjectId(each_grel.right_subject)})
                q = Q('bool',must=[Q('match', id = each_grel.right_subject)])

                # q = Q('match',name=dict(query='File',type='phrase'))
                s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                s2 = s1.execute()
                n = s2[0]
                if n not in old_profile_pics:
                    old_profile_pics.append(n)

    return banner_pic_obj, old_profile_pics


def course_content(request, group_id):
    print "es_queries : In course_content",group_id, request.LANGUAGE_CODE
    group_obj   = get_group_name_id(group_id, get_obj=True)
    list_of_memberof_name = member_of_names_list(group_obj)
    group_id    = group_obj.id
    group_name  = group_obj.name
    allow_to_join = get_group_join_status(group_obj)
    template = 'ndf/gcourse_event_group.html'
    unit_structure =  get_course_content_hierarchy(group_obj,request.LANGUAGE_CODE)
    print "unit_structure:",unit_structure
    visited_nodes = []
    if 'BaseCourseGroup' in list_of_memberof_name:
        template = 'ndf/basecourse_group.html'
    if 'base_unit' in list_of_memberof_name:
        template = 'ndf/lms.html'
    if 'announced_unit' in list_of_memberof_name or 'Group' in list_of_memberof_name or 'Author' in list_of_memberof_name and 'base_unit' not in list_of_memberof_name:
        template = 'ndf/lms.html'
    banner_pic_obj,old_profile_pics = _get_current_and_old_display_pics(group_obj)
    # if request.user.is_authenticated():
    #     counter_obj = Counter.get_counter_obj(request.user.id, ObjectId(group_id))
    #     if counter_obj:
    #         # visited_nodes = map(str,counter_obj['visited_nodes'].keys())
    #         #print counter_obj
    #         visited_nodes = counter_obj['visited_nodes']
    print "banner_pic_obj:",banner_pic_obj
    context_variables = RequestContext(request, {
            'group_id': group_id, 'groupid': group_id, 'group_name':group_name,
            'group_obj': group_obj,'node': group_obj, 'title': 'course content',
            'allow_to_join': allow_to_join,
            'old_profile_pics':old_profile_pics, "prof_pic_obj": banner_pic_obj,
            'unit_structure': json.dumps(unit_structure,cls=NodeJSONEncoder),
            'visited_nodes': json.dumps(visited_nodes)
            })
    print "Before rendering template",template
    return render_to_response(template, context_variables)

def get_name_id_from_type(node_name_or_id, node_type, get_obj=False):
    '''
    e.g:
        Node.get_name_id_from_type('pink-bunny', 'Author')
    '''
    if not get_obj:
        # if cached result exists return it

        slug = slugify(node_name_or_id)
        cache_key = node_type + '_name_id' + str(slug)
        cache_result = cache.get(cache_key)

        if cache_result:
            # todo:  return OID after casting
            return (cache_result[0], ObjectId(cache_result[1]))
        # ---------------------------------

    node_id = ObjectId(node_name_or_id) if ObjectId.is_valid(node_name_or_id) else None
    # node_obj = node_collection.one({
    #                                 "_type": {"$in": [
    #                                         # "GSystemType",
    #                                         # "MetaType",
    #                                         # "RelationType",
    #                                         # "AttributeType",
    #                                         # "Group",
    #                                         # "Author",
    #                                         node_type
    #                                     ]},
    #                                 "$or":[
    #                                     {"_id": node_id},
    #                                     {"name": unicode(node_name_or_id)}
    #                                 ]
    #                             })

    if ObjectId.is_valid(node_name_or_id):

        q = Q('bool',must=[Q('match', type = node_type),Q('match',id=str(node_name_or_id))])
    else:
        q = Q('bool',must=[Q('match', type = node_type),Q('match',name=node_name_or_id)])

    # q = Q('match',name=dict(query='File',type='phrase'))
    s1 = Search(using=es, index='nodes',doc_type="node").query(q)
    s2 = s1.execute()
    node_obj =s2[0]


    if node_obj:
        node_name = node_obj.name
        node_id = node_obj.id

        # setting cache with ObjectId
        cache_key = node_type + '_name_id' + str(slugify(node_id))
        cache.set(cache_key, (node_name, node_id), 60 * 60)

        # setting cache with node_name
        cache_key = node_type + '_name_id' + str(slugify(node_name))
        cache.set(cache_key, (node_name, node_id), 60 * 60)

        if get_obj:
            return node_obj
        else:
            return node_name, node_id

    if get_obj:
        return None
    else:
        return None, None


def course_pages(request, group_id, page_id=None,page_no=1):
    from gnowsys_ndf.settings import GSTUDIO_NO_OF_OBJS_PP
    group_obj = get_group_name_id(group_id, get_obj=True)
    page_gst_name, page_gst_id = get_gst_name_id("Page")
    group_id = group_obj.id
    group_name = group_obj.name
    #template = 'ndf/gevent_base.html'
    print "inside course_pages",group_id
    template = 'ndf/lms.html'
    context_variables = {
            'group_id': group_id, 'groupid': group_id, 'group_name':group_name,
            'group_obj': group_obj, 'title': 'course_pages',
            'editor_view': True, 'activity_node': None, 'all_pages': None}

    if page_id:
        q = Q('bool',must=[Q('match', id = str(page_id))])

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute()
        node_obj =s2[0]
        rt_translation_of = get_name_id_from_type('translation_of', 'RelationType', get_obj=True)
        # other_translations_grels = triple_collection.find({
        #                     '_type': u'GRelation',
        #                     'subject': ObjectId(page_id),
        #                     'relation_type': rt_translation_of._id,
        #                     'right_subject': {'$nin': [node_obj._id]}
        #                 })

        q = Q('bool',must=[Q('match', type='GRelation'),Q('match',subject=str(page_id)),Q('match',relation_type=rt_translation_of.id)],must_not = [Q('match', right_subject = str(node_obj.id))])

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='triples',doc_type="triple").query(q)
        other_translations_grels = s1.execute()
        # node_obj =s2[0]
        rgtsubjects_list = [r.right_subject for r in other_translations_grels]
        
        # other_translations = node_collection.find({'_id': {'$in': [r.right_subject for r in other_translations_grels]} })
        q = Q('terms',id = rgtsubjects_list)

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='triples',doc_type="triple").query(q)
        other_translations = s1.execute()
        


        context_variables.update({'activity_node': node_obj, 'hide_breadcrumbs': True,'other_translations':other_translations})
        context_variables.update({'editor_view': False})


    else:
        activity_gst_name, activity_gst_id = get_gst_name_id("activity")
        # all_pages = node_collection.find({'member_of':
        #             {'$in': [page_gst_id, activity_gst_id] }, 'group_set': group_id,
        #             'type_of': {'$ne': [blog_page_gst_id]}
        #             # 'content': {'$regex': 'clix-activity-styles.css', '$options': 'i'}
        #             }).sort('last_update',-1)
        
        q = Q('bool',must = [Q('terms',member_of = [str(page_gst_id), str(activity_gst_id)]),Q('match',group_set = group_id)])

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q).sort('-last_update')
        all_pages = s1.execute()



        course_pages_info = Paginator(all_pages, page_no, GSTUDIO_NO_OF_OBJS_PP)
        context_variables.update({'editor_view': False, 'all_pages': all_pages,'course_pages_info':course_pages_info})
    return render_to_response(template,
                                context_variables,
                                context_instance = RequestContext(request)
    )

def create_edit_course_page(request, group_id, page_id=None,page_type=None):
    print "es_queries inside create_edit_activity",group_id
    group_obj = get_group_name_id(group_id, get_obj=True)
    group_id = group_obj.id
    group_name = group_obj.name
    #template = 'ndf/gevent_base.html'
    template = 'ndf/lms.html'
    # templates_gst = node_collection.one({"_type":"GSystemType","name":"Template"})
    # if templates_gst._id:
    #   # templates_cur = node_collection.find({"member_of":ObjectId(GST_PAGE._id),"type_of":ObjectId(templates_gst._id)})
    #   templates_cur = node_collection.find({"type_of":ObjectId(templates_gst._id)})

    context_variables = {
            'group_id': group_id, 'groupid': group_id, 'group_name':group_name,'page_type':page_type,
            'group_obj': group_obj, 'title': 'create_course_pages',
            'activity_node': None, #'templates_cur': templates_cur,
            'cancel_activity_url': reverse('course_pages',
                                        kwargs={
                                        'group_id': group_id
                                        })}

    if page_id:
        # node_obj = node_collection.one({'_id': ObjectId(page_id)})

        q = Q('bool',must=[Q('match', id = page_id)])

        # q = Q('match',name=dict(query='File',type='phrase'))
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        s2 = s1.execute()
        node_obj =s2[0]

        context_variables.update({'activity_node': node_obj, 'hide_breadcrumbs': True,
            'cancel_activity_url': reverse('view_course_page',
                                        kwargs={
                                        'group_id': group_id,
                                        'page_id': node_obj.id
                                        })})


    return render_to_response(template,
                                context_variables,
                                context_instance = RequestContext(request)
    )

def get_group_join_status(group_obj):
    # from gnowsys_ndf.ndf.templatetags.ndf_tags import get_attribute_value
    allow_to_join = None
    start_enrollment_date = get_attribute_value(group_obj.id,"start_enroll")
    last_enrollment_date = get_attribute_value(group_obj.id,"end_enroll")
    curr_date_time = datetime.datetime.now().date()
    print "start_enroll:",start_enrollment_date
    print "end_enroll:",last_enrollment_date
    if start_enrollment_date and last_enrollment_date:
      start_enrollment_date = datetime.datetime.strptime(start_enrollment_date, '%d/%m/%Y %H:%M:%S:%f')
      last_enrollment_date = datetime.datetime.strptime(last_enrollment_date, '%d/%m/%Y %H:%M:%S:%f')
      start_enrollment_date = start_enrollment_date.date()
      last_enrollment_date = last_enrollment_date.date()
      if start_enrollment_date <= curr_date_time and last_enrollment_date >= curr_date_time:
          allow_to_join = "Open"
      else:
          allow_to_join = "Closed"
    return allow_to_join

def get_course_content_hierarchy(unit_group_obj,lang="en"):
    '''
    ARGS: unit_group_obj
    Result will be of following form:
    {
        name: 'Lesson1',
        type: 'lesson',
        id: 'l1',
        activities: [
            {
                name: 'Activity 1',
                type: 'activity',
                id: 'a1'
            },
            {
                name: 'Activity 1',
                type: 'activity',
                id: 'a2'
            }
        ]
    }, {
        name: 'Lesson2',
        type: 'lesson',
        id: 'l2',
        activities: [
            {
                name: 'Activity 1',
                type: 'activity',
                id: 'a1'
            }
        ]
    }
    '''

    unit_structure = []
    for each in unit_group_obj.collection_set:
        lesson_dict ={}
        lesson = get_node_by_id(each)
        if lesson:
            trans_lesson = get_lang_node(lesson.id,lang)
            if trans_lesson:
                lesson_dict['label'] = trans_lesson.name
            else:
                lesson_dict['label'] = lesson.name
            lesson_dict['id'] = lesson.id
            lesson_dict['type'] = 'unit-name'
            lesson_dict['children'] = []
            if lesson.collection_set:
                for each_act in lesson.collection_set:
                    activity_dict ={}
                    activity = get_node_by_id(each_act)
                    if activity:
                        trans_act_name = get_lang_node(each_act,lang)
                        # activity_dict['label'] = trans_act_name.name or activity.name  
                        if trans_act_name:
                            activity_dict['label'] = trans_act_name.altnames or trans_act_name.name
                            print "in side activity loop", trans_act_name.id, "in language", lang
                            # activity_dict['label'] = trans_act_name.name
                        else:
                            # activity_dict['label'] = activity.name
                            activity_dict['label'] = activity.altnames or activity.name
                        activity_dict['type'] = 'activity-group'
                        activity_dict['id'] = str(activity.id)
                        lesson_dict['children'].append(activity_dict)
            unit_structure.append(lesson_dict)
    return unit_structure

def get_lang_node(node_id,lang):
    rel_value = get_relation_value(node_id,"translation_of")
    print "rel_value node:",rel_value
    for each in rel_value['grel_node']:
        if each.language[0] ==  get_language_tuple(lang)[0]:
            trans_node = each
            print "in get_lang_node", trans_node.id, "in language", each.language[0]
            return trans_node


def get_language_tuple(lang):
    """
    from input argument of language code of language name
    get the std matching tuple from settings.

    Returns:
        tuple: (<language code>, <language name>)

    Args:
        lang (str or unicode): it is the one of item from tuple.
        It may either language-code or language-name.
    """
    if not lang:
        return ('en', 'English')

    all_languages = list(LANGUAGES) + OTHER_COMMON_LANGUAGES

    # check if lang argument itself is a complete, valid tuple that exists in all_languages.
    if (lang in all_languages) or (tuple(lang) in all_languages):
        return lang

    all_languages_concanated = reduce(lambda x, y: x+y, all_languages)

    # iterating over each document in the cursor:
    # - Secondly, replacing invalid language values to valid tuple from settings
    if lang in all_languages_concanated:
        for each_lang in all_languages:
            if lang in each_lang:
                return each_lang

    # as a default return: ('en', 'English')
    return ('en', 'English')

def get_relation_value(node_id, grel, return_single_right_subject=False):

    # import ipdb; ipdb.set_trace()
    try:
        result_dict = {}
        if node_id:
            # node = node_collection.one({'_id': ObjectId(node_id) })
            
            node = get_node_by_id(node_id)

            # relation_type_node = node_collection.one({'_type': 'RelationType', 'name': unicode(grel) })
            
            q = eval("Q('bool',must=[Q('match', type = 'RelationType'), Q('match', name = grel)])")

            # q = Q('match',name=dict(query='File',type='phrase'))
            s1 = Search(using=es, index='nodes',doc_type="node").query(q)
            s2 = s1.execute()
            relation_type_node = s2[0]
            print "relation_type_node.object_cardinality:",relation_type_node.id
            if node and relation_type_node:
                if relation_type_node.object_cardinality > 1:
                    # node_grel = triple_collection.find({'_type': "GRelation", "subject": node._id, 'relation_type': relation_type_node._id,'status':"PUBLISHED"})
                    
                    q = Q('bool',must=[Q('match', type = 'GRelation'), Q('match', subject = str(node.id)), Q('match', relation_type = str(relation_type_node.id))])
                    s1 = Search(using=es, index='triples',doc_type="triple").query(q)

                    # print "s1:",s1,q
                    s2 = s1.execute()

                    # print "tripl nds:",s2

                    node_grel = s2

                    if node_grel:
                        grel_val = []
                        grel_id = []
                        for each_node in node_grel:
                            grel_val.append(each_node.right_subject)
                            grel_id.append(each_node.id)
                        # grel_val_node_cur = node_collection.find({'_id':{'$in' : grel_val}})

                        q = Q('terms', id = grel_val)

                        # q = Q('match',name=dict(query='File',type='phrase'))
                        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                        grel_val_node_cur = s1.execute()

                        result_dict.update({"cursor": True})
                        if return_single_right_subject:
                            # grel_val_node_cur = node_collection.find_one({'_id':{'$in' : grel_val}})
                            q = Q('match', id = grel_val)

                            # q = Q('match',name=dict(query='File',type='phrase'))
                            s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                            s2 = s1.execute()
                            grel_val_node_cur = s2[0]                            
                            result_dict.update({"cursor": False})
                        # nodes = [grel_node_val for grel_node_val in grel_val_node_cur]
                        # print "\n\n grel_val_node, grel_id == ",grel_val_node, grel_id
                        result_dict.update({"grel_id": grel_id, "grel_node": grel_val_node_cur})
                else:
                    print "else:",grel
                    # node_grel = triple_collection.one({'_type': "GRelation", "subject": node._id, 'relation_type': relation_type_node._id,'status':"PUBLISHED"})
                    q = Q('bool',must=[Q('match', type = 'GRelation'), Q('match', subject = node_id), Q('match', relation_type = relation_type_node.id)])
                    s1 = Search(using=es, index='triples',doc_type="triple").query(q)
                    s2 = s1.execute()
                    for each in s1[0:s1.count()]:
                        if each.status == 'PUBLISHED':
                            node_grel = each
                            break
                
                    if node_grel:
                        grel_val = list()
                        grel_val = node_grel.right_subject
                        grel_val = grel_val if isinstance(grel_val, list) else grel_val
                        grel_id = node_grel.id
                        # grel_val_node = node_collection.one({'_id':ObjectId(grel_val)})
                        # grel_val_node = node_collection.find_one({'_id':{'$in': grel_val}})

                        q = Q('match', id = grel_val)

                        # q = Q('match',name=dict(query='File',type='phrase'))
                        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
                        s2 = s1.execute()
                        grel_val_node = s2[0]
                        
                        # returns right_subject of grelation and GRelation _id
                        result_dict.update({"grel_id": grel_id, "grel_node": grel_val_node, "cursor": False})
        print "\n\nresult_dict === ",result_dict
        return result_dict
    except Exception as e:
        print e
        return {}

def get_unit_hierarchy(unit_group_obj,lang="en"):
    '''
    ARGS: unit_group_obj
    Result will be of following form:
    {
        name: 'Lesson1',
        type: 'lesson',
        id: 'l1',
        activities: [
            {
                name: 'Activity 1',
                type: 'activity',
                id: 'a1'
            },
            {
                name: 'Activity 1',
                type: 'activity',
                id: 'a2'
            }
        ]
    }, {
        name: 'Lesson2',
        type: 'lesson',
        id: 'l2',
        activities: [
            {
                name: 'Activity 1',
                type: 'activity',
                id: 'a1'
            }
        ]
    }
    '''
    unit_structure = []
    print "unit object and collection_set:",unit_group_obj.name,unit_group_obj.collection_set
    for each in unit_group_obj.collection_set:
        lesson_dict ={}
        lesson = get_node_by_id(str(each))
        if lesson:
            if lang != 'en':
                trans_lesson = get_lang_node(lesson.id,lang)
                lesson_dict['name'] = trans_lesson.name
            else:
                lesson_dict['name'] = lesson.name
            lesson_dict['type'] = 'lesson'
            lesson_dict['id'] = str(lesson.id)
            lesson_dict['language'] = lesson.language[0]
            lesson_dict['activities'] = []
            if lesson.collection_set:
                for each_act in lesson.collection_set:
                    activity_dict ={}
                    activity = Node.get_node_by_id(each_act)
                    if activity:
                        trans_act = get_lang_node(activity.id,lang)
                        if trans_act:
                            # activity_dict['name'] = trans_act.name
                            activity_dict['name'] = trans_act.altnames or trans_act.name
                        else:
                            # activity_dict['name'] = activity.name
                            activity_dict['name'] = activity.altnames or activity.name
                        activity_dict['type'] = 'activity'
                        activity_dict['id'] = str(activity.id)
                        lesson_dict['activities'].append(activity_dict)
            unit_structure.append(lesson_dict)

    return unit_structure

def unit_detail(request, group_id):
    '''
    detail of of selected units
    '''
    # parent_group_name, parent_group_id = Group.get_group_name_id(group_id)
    print "es_queries : In unit-detail ",group_id

    unit_group_obj = get_group_name_id(group_id, get_obj=True)

    unit_structure = get_unit_hierarchy(unit_group_obj, request.LANGUAGE_CODE)
    # template = "ndf/unit_structure.html"
    # template = 'ndf/gevent_base.html'
    template = 'ndf/lms.html'

    # print unit_structure
    req_context = RequestContext(request, {
                                'title': 'unit_authoring',
                                'hide_bannerpic': True,
                                'group_id': unit_group_obj.id,
                                'groupid': unit_group_obj.id,
                                'group_name': unit_group_obj.name,
                                'unit_obj': unit_group_obj,
                                'group_obj': unit_group_obj,
                                'unit_structure': json.dumps(unit_structure)
                            })
    return render_to_response(template, req_context)

def lesson_create_edit(request, group_id, unit_group_id=None):
    '''
    creation as well as edit of lessons
    returns following:
    {
        'success': <BOOL: 0 or 1>,
        'unit_hierarchy': <unit hierarchy json>,
        'msg': <error msg or objectid of newly created obj>
    }
    '''
    # parent_group_name, parent_group_id = Group.get_group_name_id(group_id)

    # parent unit id

    gst_lesson_name, gst_lesson_id = get_gst_name_id('lesson')
    gst_activity_name, gst_activity_id = get_gst_name_id('activity')
    gst_module_name, gst_module_id = get_gst_name_id('Module')
    rt_translation_of = get_name_id_from_type('translation_of', 'RelationType', get_obj=True)


    lesson_id = request.POST.get('lesson_id', None)
    lesson_language = request.POST.get('sel_lesson_lang','')
    unit_id_post = request.POST.get('unit_id', '')
    lesson_content = request.POST.get('lesson_desc', '')
    # print "lesson_id: ", lesson_id
    # print "lesson_language: ", lesson_language
    # print "unit_id_post: ", unit_id_post
    unit_group_id = unit_id_post if unit_id_post else unit_group_id
    # getting parent unit object
    unit_group_obj = Group.get_group_name_id(unit_group_id, get_obj=True)
    result_dict = {'success': 0, 'unit_hierarchy': [], 'msg': ''}
    if request.method == "POST":
        # lesson name
        lesson_name = request.POST.get('name', '').strip()
        if not lesson_name:
            msg = 'Name can not be empty.'
            result_dict = {'success': 0, 'unit_hierarchy': [], 'msg': msg}
            # return HttpResponse(0)

        # check for uniqueness of name
        # unit_cs: unit collection_set
        unit_cs_list = [str(each) for each in unit_group_obj.collection_set]
        print "unit list:",unit_cs_list
        unit_cs_objs_cur = get_nodes_by_ids_list(unit_cs_list)
        if unit_cs_objs_cur:
            unit_cs_names_list = [u.name for u in unit_cs_objs_cur]

        if not lesson_id and unit_cs_objs_cur  and  lesson_name in unit_cs_names_list:  # same name activity
            # currently following logic was only for "en" nodes.
            # commented and expecting following in future:
            # check for uniqueness w.r.t language selected within all sibling lessons's translated nodes

            # lesson_obj = Node.get_node_by_id(lesson_id)
            # if lesson_language != lesson_obj.language[0]:
            #     if lesson_language:
            #         language = get_language_tuple(lesson_language)
            #         lesson_obj.language = language
            #         lesson_obj.save()
            msg = u'Activity with same name exists in lesson: ' + unit_group_obj.name
            result_dict = {'success': 0, 'unit_hierarchy': [], 'msg': msg}

        elif lesson_id and ObjectId.is_valid(lesson_id):  # Update
            # getting default, "en" node:
            if lesson_language != "en":
                node = translated_node_id = None
                # grel_node = triple_collection.one({
                #                         '_type': 'GRelation',
                #                         'subject': ObjectId(lesson_id),
                #                         'relation_type': rt_translation_of._id,
                #                         'language': get_language_tuple(lesson_language),
                #                         # 'status': 'PUBLISHED'
                #                     })

                q = Q('bool',must = [Q('match',type = 'GRelation'),Q('match',subject=str(lesson_id)),Q('match',relation_type = str(rt_translation_of.id)),Q('match',language=get_language_tuple(lesson_language))])
                s1 = Search(using=es, index='triples',doc_type="triple").query(q)
                s2 = s1.execute()
                grel_node = s2[0]
                if grel_node:
                    # grelation found.
                    # transalated node exists.
                    # edit of existing translated node.

                    # node = Node.get_node_by_id(grel_node.right_subject)
                    # translated_node_id = node._id
                    lesson_id = grel_node.right_subject
                else:
                    # grelation NOT found.
                    # create transalated node.
                    user_id = request.user.id
                    new_lesson_obj = node_collection.collection.GSystem()
                    new_lesson_obj.fill_gstystem_values(name=lesson_name,
                                                    content=lesson_content,
                                                    member_of=gst_lesson_id,
                                                    group_set=unit_group_obj.id,
                                                    created_by=user_id,
                                                    status=u'PUBLISHED')
                    # print new_lesson_obj
                    if lesson_language:
                        language = get_language_tuple(lesson_language)
                        new_lesson_obj.language = language
                    new_lesson_obj.save(groupid=group_id)
                    save_node_to_es(new_lesson_obj)
                    trans_grel_list = [new_lesson_obj.id]
                    # trans_grels = triple_collection.find({'_type': 'GRelation', \
                    #         'relation_type': rt_translation_of._id,'subject': ObjectId(lesson_id)},{'_id': 0, 'right_subject': 1})
                    q = Q('bool',must = [Q('match',type = 'GRelation'),Q('match',subject=str(lesson_id)),Q('match',relation_type = str(rt_translation_of.id))])
                    s1 = Search(using=es, index='triples',doc_type="triple").query(q)
                    trans_grels = s1.execute()
                    # grel_node = s2[0]

                    for each_rel in trans_grels:
                        trans_grel_list.append(each_rel['right_subject'])
                    # translate_grel = create_grelation(node_id, rt_translation_of, trans_grel_list, language=language)
                    create_grelation(lesson_id, rt_translation_of, trans_grel_list, language=language)

            lesson_obj = Node.get_node_by_id(lesson_id)
            if lesson_obj and (lesson_obj.name != lesson_name):
                trans_lesson = get_lang_node(lesson_obj.id,lesson_language)
                if trans_lesson:
                    trans_lesson.name = lesson_name
                else:
                    lesson_obj.name = lesson_name
                # if lesson_language:
                #     language = get_language_tuple(lesson_language)
                #     lesson_obj.language = language
                lesson_obj.save(group_id=group_id)
                save_node_to_es(lesson_obj)
                unit_structure = get_unit_hierarchy(unit_group_obj, request.LANGUAGE_CODE)
                msg = u'Lesson name updated.'
                result_dict = {'success': 1, 'unit_hierarchy': unit_structure, 'msg': str(lesson_obj.id)}
            else:
                unit_structure = get_unit_hierarchy(unit_group_obj, request.LANGUAGE_CODE)
                msg = u'Nothing to update.'
                result_dict = {'success': 1, 'unit_hierarchy': unit_structure, 'msg': msg}

        else: # creating a fresh lesson object
            user_id = request.user.id
            new_lesson_obj = node_collection.collection.GSystem()
            new_lesson_obj.fill_gstystem_values(name=lesson_name,
                                            content=lesson_content,
                                            member_of=gst_lesson_id,
                                            group_set=unit_group_obj._id,
                                            created_by=user_id,
                                            status=u'PUBLISHED')
            # print new_lesson_obj
            if lesson_language:
                language = get_language_tuple(lesson_language)
                new_lesson_obj.language = language
            new_lesson_obj.save(groupid=group_id)
            save_node_to_es(new_lesson_obj)
            unit_group_obj.collection_set.append(new_lesson_obj._id)
            unit_group_obj.save(groupid=group_id)
            save_node_to_es(unit_group_obj)
            unit_structure = get_unit_hierarchy(unit_group_obj, request.LANGUAGE_CODE)

            msg = u'Added lesson under lesson: ' + unit_group_obj.name
            result_dict = {'success': 1, 'unit_hierarchy': unit_structure, 'msg': str(new_lesson_obj._id)}
            # return HttpResponse(json.dumps(unit_structure))

    # return HttpResponse(1)
    return HttpResponse(json.dumps(result_dict))

def create_grelation(subject_id, relation_type_node, right_subject_id_or_list, **kwargs):
    """Creates single or multiple GRelation documents (instances) based on given
    RelationType's cardinality (one-to-one / one-to-many).

    Arguments:
    subject_id -- ObjectId of the subject-node
    relation_type_node -- Document of the RelationType node (Embedded document)
    right_subject_id_or_list --
      - When one to one relationship: Single ObjectId of the right_subject node
      - When one to many relationship: List of ObjectId(s) of the right_subject node(s)

    Returns:
    - When one to one relationship: Created/Updated/Existed document.
    - When one to many relationship: Created/Updated/Existed list of documents.

    kwargs -- can hold the scope value
    """
    gr_node = None
    multi_relations = False
    triple_scope_val = kwargs.get('triple_scope', None)
    language = get_language_tuple(kwargs.get('language', None))
    '''
    Example:
    triple_scope:
      {
        relation_type_scope : {'alt_format': 'mp4', 'alt_size': '720p', 'alt_language': 'hi'},
        object_scope : unicode,
        subject_scope : unicode
      }

    In next phase, validate the scope values by adding:
        GSTUDIO_FORMAT_SCOPE_VALUES
        GSTUDIO_SIZE_SCOPE_VALUES
        GSTUDIO_LANGUAGE_SCOPE_VALUES
        in settings.py
        - katkamrachana, 23-12-2016
    '''
    try:
        subject_id = ObjectId(subject_id)

        def _create_grelation_node(subject_id, relation_type_node, right_subject_id_or_list, relation_type_text, triple_scope_val=None):
            # Code for creating GRelation node
            gr_node = triple_collection.collection.GRelation()

            gr_node.subject = subject_id
            gr_node.relation_type = relation_type_node.id
            gr_node.right_subject = right_subject_id_or_list
            # gr_node.relation_type_scope = relation_type_scope
            gr_node.language = language
            gr_node.status = u"PUBLISHED"
            gr_node.save()
            save_triple_to_es(gr_node)
            # gr_node.save(triple_node=relation_type_node, triple_id=relation_type_node._id)

            gr_node_name = gr_node.name
            info_message = "%(relation_type_text)s: GRelation (%(gr_node_name)s) " % locals() \
                + "created successfully.\n"

            relation_type_node_name = relation_type_node.name
            relation_type_node_inverse_name = relation_type_node.inverse_name

            # left_subject = node_collection.one({
            #     "_id": subject_id,
            #     "relation_set." + relation_type_node_name: {"$exists": True}
            # })

            q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node_name)])
            s1 = Search(using=es, index='nodes',doc_type="node").query(q)
            s2 = s1.execute()
            left_subject = s2[0]
            if triple_scope_val:
                gr_node = update_scope_of_triple(gr_node,relation_type_node, triple_scope_val, is_grel=True)

            if left_subject:
                                # Update value of grelation in existing as key-value pair value in
                                # given node's "relation_set" field
                # node_collection.collection.update({
                #     "_id": subject_id,
                #     "relation_set." + relation_type_node_name: {'$exists': True}
                # }, {
                #     "$addToSet": {"relation_set.$." + relation_type_node_name: right_subject_id_or_list}
                # },
                #     upsert=False, multi=False
                # )
                q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node_name)])
                f1 = "relation_set." + relation_type_node_name
                s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':right_subject_id_or_list})
                s2 = s1.execute()
                # left_subject = s2[0]


            else:
                # Add grelation as new key-value pair value in given node's
                # relation_set field
                # node_collection.collection.update({
                #     "_id": subject_id
                # }, {
                #     "$addToSet": {"relation_set": {relation_type_node_name: [right_subject_id_or_list]}}
                # },
                #     upsert=False, multi=False
                # )

                q = Q('bool',must = [Q('match',id = subject_id)])
                f1 = "relation_set." + relation_type_node_name
                s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':right_subject_id_or_list})
                s2 = s1.execute()

            # right_subject = node_collection.one({
            #     '_id': right_subject_id_or_list,
            #     "relation_set." + relation_type_node_inverse_name: {"$exists": True}
            # }, {
            #     'relation_set': 1
            # })

            q = Q('bool',must = [Q('match',id = right_subject_id_or_list),Q('exists',field = "relation_set." + relation_type_node_inverse_name)])
            # f1 = "relation_set." + relation_type_node_name
            s1 = Search(using=es, index='nodes',doc_type="node").query(q)
            s2 = s1.execute()
            right_subject = s2[0]

            if right_subject:
                # Update value of grelation in existing as key-value pair value in
                # given node's "relation_set" field
                # node_collection.collection.update({
                #     "_id": right_subject_id_or_list, "relation_set." + relation_type_node_inverse_name: {'$exists': True}
                # }, {
                #     "$addToSet": {"relation_set.$." + relation_type_node_inverse_name: subject_id}
                # },
                #     upsert=False, multi=False
                # )

                q = Q('bool',must = [Q('match',id = right_subject_id_or_list),Q('exists',field = "relation_set." + relation_type_node_inverse_name)])
                f1 = "relation_set." + relation_type_node_inverse_name
                s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':subject_id})
                s2 = s1.execute()

            else:
                # Add grelation as new key-value pair value in given node's
                # relation_set field
                # node_collection.collection.update({
                #     "_id": right_subject_id_or_list
                # }, {
                #     "$addToSet": {"relation_set": {relation_type_node_inverse_name: [subject_id]}}
                # },
                #     upsert=False, multi=False
                # )

                q = Q('bool',must = [Q('match',id = right_subject_id_or_list)])
                f1 = "relation_set." + relation_type_node_inverse_name
                s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':subject_id})
                s2 = s1.execute()

            return gr_node

        def _update_deleted_to_published(gr_node, relation_type_node, relation_type_text, triple_scope_val=None):
            gr_node.status = u"PUBLISHED"
            # gr_node.language = language
            gr_node.save()
            # gr_node.save(triple_node=relation_type_node, triple_id=relation_type_node._id)
            save_triple_to_es(gr_node)
            gr_node_name = gr_node.name
            relation_type_node_name = relation_type_node.name
            relation_type_node_inverse_name = relation_type_node.inverse_name

            subject_id = gr_node.subject
            right_subject = gr_node.right_subject

            info_message = " %(relation_type_text)s: GRelation (%(gr_node_name)s) " % locals() \
                + \
                "status updated from 'DELETED' to 'PUBLISHED' successfully.\n"

            # node_collection.collection.update({
            #     "_id": subject_id, "relation_set." + relation_type_node_name: {'$exists': True}
            # }, {
            #     "$addToSet": {"relation_set.$." + relation_type_node_name: right_subject}
            # },
            #     upsert=False, multi=False
            # )

            q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node_name)])
            f1 = "relation_set." + relation_type_node_name
            s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':right_subject})
            s2 = s1.execute()


            # node_collection.collection.update({
            #     "_id": right_subject, "relation_set." + relation_type_node_inverse_name: {'$exists': True}
            # }, {
            #     "$addToSet": {'relation_set.$.' + relation_type_node_inverse_name: subject_id}
            # },
            #     upsert=False, multi=False
            # )


            q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node_inverse_name)])
            f1 = "relation_set." + relation_type_node_inverse_name
            s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':subject_id})
            s2 = s1.execute()

            return gr_node


        if relation_type_node["object_cardinality"]:
            # If object_cardinality value exists and greater than 1 (or eaqual to 100)
            # Then it signifies it's a one to many type of relationship
            # assign multi_relations = True
            type_of_relationship = relation_type_node.member_of_names_list
            if relation_type_node["object_cardinality"] > 1:
                multi_relations = True

                if META_TYPE[3] in type_of_relationship:
                    # If Binary relationship found

                    # Check whether right_subject_id_or_list is list or not
                    # If not convert it to list
                    if not isinstance(right_subject_id_or_list, list):
                        right_subject_id_or_list = [right_subject_id_or_list]

                    # Check whether all values of a list are of ObjectId data-type or not
                    # If not convert them to ObjectId
                    for i, each in enumerate(right_subject_id_or_list):
                        right_subject_id_or_list[i] = ObjectId(each)

                else:
                    # Relationship Other than Binary one found; e.g, Triadic
                    if right_subject_id_or_list:
                        if not isinstance(right_subject_id_or_list[0], list):
                            right_subject_id_or_list = [
                                right_subject_id_or_list]

                        # right_subject_id_or_list: [[id, id, ...], [id, id,
                        # ...], ...]
                        for i, each_list in enumerate(right_subject_id_or_list):
                            # each_list: [id, id, ...]
                            for j, each in enumerate(each_list):
                                right_subject_id_or_list[i][j] = ObjectId(each)

            else:
                if META_TYPE[3] in type_of_relationship:
                    # If Binary relationship found
                    if isinstance(right_subject_id_or_list, list):
                        right_subject_id_or_list = ObjectId(
                            right_subject_id_or_list[0])

                    else:
                        right_subject_id_or_list = ObjectId(
                            right_subject_id_or_list)
                else:
                    # Relationship Other than Binary one found; e.g, Triadic
                    # right_subject_id_or_list: [[id, id, ...], [id, id, ...],
                    # ...]
                    if isinstance(right_subject_id_or_list, ObjectId):
                        right_subject_id_or_list = [right_subject_id_or_list]
                    if right_subject_id_or_list:
                        if isinstance(right_subject_id_or_list[0], list):
                            # Reduce it to [id, id, id, ...]
                            right_subject_id_or_list = right_subject_id_or_list[
                                0]

                        for i, each_id in enumerate(right_subject_id_or_list):
                            right_subject_id_or_list[i] = ObjectId(each_id)

        if multi_relations:
            # For dealing with multiple relations (one to many)

            # # Iterate and find all relationships (including DELETED ones' also)
            # nodes = triple_collection.find({
            #     '_type': "GRelation", 'subject': subject_id,
            #     'relation_type': relation_type_node._id
            # })

            q = Q('bool',must = [Q('match',type = 'GRelation'),Q('match',subject=subject_id),Q('match', relation_type = relation_type_node.id )])
            # f1 = "relation_set." + relation_type_node_inverse_name
            s1 = Search(using=es, index='triples',doc_type="triple").query(q)
            nodes = s1.execute()

            gr_node_list = []

            for n in nodes:
                if n.right_subject in right_subject_id_or_list:
                    if n.status != u"DELETED":
                        # If match found with existing one's, then only remove that ObjectId from the given list of ObjectIds
                        # Just to remove already existing entries (whose status
                        # is PUBLISHED)
                        right_subject_id_or_list.remove(n.right_subject)
                        gr_node_list.append(n)
                        # if triple_scope_val:
                        #     n = update_scope_of_triple(n, relation_type_node, triple_scope_val, is_grel=True)

                        # node_collection.collection.update(
                        #     {'_id': subject_id, 'relation_set.' +
                        #         relation_type_node.name: {'$exists': True}},
                        #     {'$addToSet': {
                        #         'relation_set.$.' + relation_type_node.name: n.right_subject}},
                        #     upsert=False, multi=False
                        # )

                        q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node.name)])
                        f1 = "relation_set." + relation_type_node.name
                        s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':n.right_subject})
                        s2 = s1.execute()

                        # node_collection.collection.update(
                        #     {'_id': n.right_subject, 'relation_set.' +
                        #         relation_type_node.inverse_name: {'$exists': True}},
                        #     {'$addToSet': {
                        #         'relation_set.$.' + relation_type_node.inverse_name: subject_id}},
                        #     upsert=False, multi=False
                        # )

                        q = Q('bool',must = [Q('match',id = n.right_subject),Q('exists',field = "relation_set." + relation_type_node.inverse_name)])
                        f1 = "relation_set." + relation_type_node.inverse_name
                        s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':subject_id})
                        s2 = s1.execute()

                        n.reload()

                else:
                    # Case: When already existing entry doesn't exists in newly come list of right_subject(s)
                    # So change their status from PUBLISHED to DELETED
                    n.status = u"DELETED"
                    n.save()
                    save_node_to_es(n)
                    # n.save(triple_node=relation_type_node, triple_id=relation_type_node._id)

                    info_message = " MultipleGRelation: GRelation (" + n.name + \
                        ") status updated from 'PUBLISHED' to 'DELETED' successfully.\n"

                    # node_collection.collection.update({
                    #     '_id': subject_id, 'relation_set.' + relation_type_node.name: {'$exists': True}
                    # }, {
                    #     '$pull': {'relation_set.$.' + relation_type_node.name: n.right_subject}
                    # },
                    #     upsert=False, multi=False
                    # )

                    q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node.name)])
                    f1 = "relation_set." + relation_type_node.name
                    s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.remove(params.val)", lang="painless",params={'val':n.right_subject})
                    s2 = s1.execute()

                    # res = node_collection.collection.update({
                    #     '_id': n.right_subject, 'relation_set.' + relation_type_node.inverse_name: {'$exists': True}
                    # }, {
                    #     '$pull': {'relation_set.$.' + relation_type_node.inverse_name: subject_id}
                    # },
                    #     upsert=False, multi=False
                    # )

                    q = Q('bool',must = [Q('match',id = n.right_subject),Q('exists',field = "relation_set." + relation_type_node.inverse_name)])
                    f1 = "relation_set." + relation_type_node.inverse_name
                    s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.remove(params.val)", lang="painless",params={'val':subject_id})
                    s2 = s1.execute()

            if right_subject_id_or_list:
                # If still ObjectId list persists, it means either they are new ones'
                # or from deleted ones'
                # For deleted one's, find them and modify their status to PUBLISHED
                # For newer one's, create them as new document
                for nid in right_subject_id_or_list:
                    # gr_node = triple_collection.one({
                    #     '_type': "GRelation", 'subject': subject_id,
                    #     'relation_type': relation_type_node._id, 'right_subject': nid
                    # })

                    q = Q('bool',must = [Q('match',type = 'GRelation'),Q('match',subject = subject_id),Q('match', relation_type = relation_type_node.id),Q('match', right_subject = nid)])
                    # f1 = "relation_set." + relation_type_node_name
                    s1 = Search(using=es, index='triples',doc_type="triple").query(q)
                    s2 = s1.execute()
                    gr_node = s2[0]

                    if gr_node is None:
                        # New one found so create it
                        # check for relation_type_scope variable in kwargs and pass
                        gr_node = _create_grelation_node(
                            subject_id, relation_type_node, nid, "MultipleGRelation", triple_scope_val)
                        gr_node_list.append(gr_node)

                    else:
                        # Deleted one found so change it's status back to
                        # Published
                        if gr_node.status == u'DELETED':
                            gr_node = _update_deleted_to_published(
                                gr_node, relation_type_node, "MultipleGRelation")
                            gr_node_list.append(gr_node)

                        else:
                            error_message = " MultipleGRelation: Corrupt value found - GRelation (" + \
                                gr_node.name + ")!!!\n"
                            # raise Exception(error_message)

            return gr_node_list

        else:
            # For dealing with single relation (one to one)
            gr_node = None

            relation_type_node_id = relation_type_node._id
            relation_type_node_name = relation_type_node.name
            relation_type_node_inverse_name = relation_type_node.inverse_name

            # gr_node_cur = triple_collection.find({
            #     "_type": "GRelation", "subject": subject_id,
            #     "relation_type": relation_type_node_id
            # })

            q = Q('bool',must = [Q('match',type = 'GRelation'),Q('match',subject = subject_id),Q('match', right_subject = relation_type_node_id)])
            # f1 = "relation_set." + relation_type_node_name
            s1 = Search(using=es, index='triples',doc_type="triple").query(q)
            gr_node_cur = s1.execute()

            for node in gr_node_cur:
                node_name = node.name
                node_status = node.status
                node_right_subject = node.right_subject

                if node_right_subject == right_subject_id_or_list:
                    # If match found, it means it could be either DELETED one
                    # or PUBLISHED one

                    if node_status == u"DELETED":
                        # If deleted, change it's status back to Published from
                        # Deleted
                        node = _update_deleted_to_published(
                            node, relation_type_node, "SingleGRelation", triple_scope_val)

                    elif node_status == u"PUBLISHED":
                        if triple_scope_val:
                            node = update_scope_of_triple(node, relation_type_node, triple_scope_val, is_grel=True)

                        node_collection.collection.update({
                            "_id": subject_id, "relation_set." + relation_type_node_name: {'$exists': True}
                        }, {
                            "$addToSet": {"relation_set.$." + relation_type_node_name: node_right_subject}
                        },
                            upsert=False, multi=False
                        )

                        q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node_name)])
                        f1 = "relation_set." + relation_type_node_name
                        s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':node_right_subject})
                        s2 = s1.execute()

                        # node_collection.collection.update({
                        #     "_id": node_right_subject, "relation_set." + relation_type_node_inverse_name: {'$exists': True}
                        # }, {
                        #     "$addToSet": {"relation_set.$." + relation_type_node_inverse_name: subject_id}
                        # },
                        #     upsert=False, multi=False
                        # )

                        q = Q('bool',must = [Q('match',id = node_right_subject),Q('exists',field = "relation_set." + relation_type_node_inverse_name)])
                        f1 = "relation_set." + relation_type_node_inverse_name
                        s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':subject_id})
                        s2 = s1.execute()


                        info_message = " SingleGRelation: GRelation (%(node_name)s) already exists !\n" % locals(
                        )

                    # Set gr_node value as matched value, so that no need to
                    # create new one
                    node.reload()
                    gr_node = node

                else:
                    # If match not found and if it's PUBLISHED one, modify it
                    # to DELETED
                    if node.status == u'PUBLISHED':
                        node.status = u"DELETED"
                        node.save()
                        save_triple_to_es(node)
                        # node.save(triple_node=relation_type_node, triple_id=relation_type_node._id)

                        node_collection.collection.update({
                            '_id': subject_id, 'relation_set.' + relation_type_node_name: {'$exists': True}
                        }, {
                            '$pull': {'relation_set.$.' + relation_type_node_name: node_right_subject}
                        },
                            upsert=False, multi=False
                        )

                        q = Q('bool',must = [Q('match',id = subject_id),Q('exists',field = "relation_set." + relation_type_node_name)])
                        f1 = "relation_set." + relation_type_node_name
                        s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.remove(params.val)", lang="painless",params={'val':node_right_subject})
                        s2 = s1.execute()


                        # node_collection.collection.update({
                        #     '_id': node_right_subject, 'relation_set.' + relation_type_node_inverse_name: {'$exists': True}
                        # }, {
                        #     '$pull': {'relation_set.$.' + relation_type_node_inverse_name: subject_id}
                        # },
                        #     upsert=False, multi=False
                        # )

                        q = Q('bool',must = [Q('match',id = node_right_subject),Q('exists',field = "relation_set." + relation_type_node_inverse_name)])
                        f1 = "relation_set." + relation_type_node_inverse_name
                        s1 = UpdateByQuery(using=es, index='nodes',doc_type="node").query(q).script(source="ctx._source.f1.add(params.val)", lang="painless",params={'val':subject_id})
                        s2 = s1.execute()


                        info_message = " SingleGRelation: GRelation (%(node_name)s) status " % locals() \
                            + \
                            "updated from 'PUBLISHED' to 'DELETED' successfully.\n"

            if gr_node is None:
                # Code for creation
                gr_node = _create_grelation_node(
                    subject_id, relation_type_node, right_subject_id_or_list, "SingleGRelation", triple_scope_val)

            return gr_node

    except Exception as e:
        error_message = "\n GRelationError (line #" + \
            str(exc_info()[-1].tb_lineno) + "): " + str(e) + "\n"
        raise Exception(error_message)


def get_group_resources(request, group_id, res_type="Page"):
    print "in es_queries get_group_resources"
    except_collection_set = []
    res_cur = None
    template = "ndf/group_pages.html"
    card_class = 'activity-page'

    try:
        # res_query = {'_type': 'GSystem', 'group_set': ObjectId(group_id)}
        # q1 = Q('bool',must = [])
        except_collection_set_of_id = request.GET.get('except_collection_set_of_id', None)
        print "except_collection_set_of_id:",except_collection_set_of_id
        except_collection_set_of_obj = get_node_by_id(except_collection_set_of_id)
        print "except_collection_set_of_obj:",except_collection_set_of_obj.collection_set
        if except_collection_set_of_obj:
            except_collection_set = except_collection_set_of_obj.collection_set
        #     if except_collection_set:
        #         # res_query.update({'_id': {'$nin': except_collection_set}})
        #         q2 = Q('match',id = str(except_collection_set))
        if res_type.lower() == "page":
            gst_page_name, gst_page_id = get_gst_name_id('Page')
            gst_blog_type_name, gst_blog_type_id = get_gst_name_id("Blog page")
            gst_info_type_name, gst_info_type_id = get_gst_name_id("Info page")
            # res_query.update({'type_of': {'$nin': [gst_blog_type_id, gst_info_type_id]}})
            # res_query.update({'member_of': gst_page_id})

        q = Q('bool',must = [Q('match',type = 'GSystem'),Q('match',group_set = str(group_id)),Q('match',member_of = str(gst_page_id))],must_not= [Q('terms',type_of = [str(gst_blog_type_id), str(gst_info_type_id)])])
        print "get_group_resources:",q
        s1 = Search(using=es, index='nodes',doc_type="node").query(q)
        res_cur = s1.execute()
        print "res_cur:",res_cur
        # right_subject = s2[0]
        # res_cur = node_collection.find(res_query).sort('last_update', -1)

    except Exception as get_group_resources_err:
      print "\n Error occurred. Error: {0}".format(str(get_group_resources_err))
      pass

    variable = RequestContext(request, {'cursor': res_cur, 'groupid': group_id, 'group_id': group_id, 'card_class': card_class })
    return render_to_response(template, variable)
