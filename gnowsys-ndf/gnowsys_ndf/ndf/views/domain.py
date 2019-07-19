from gnowsys_ndf.settings import GSTUDIO_ELASTICSEARCH
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search,connections,Q
import json
client = Elasticsearch('banta_i:9200')
''' -- imports from installed packages -- '''
from django.http import HttpResponseRedirect  # , HttpResponse uncomment when to use
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response  # , render  uncomment when to use
from django.template import RequestContext
from django.template import TemplateDoesNotExist


def domain_page(request,domain_name):
	#print "0000000000000000000000000000"
	print domain_name
	#user = request.get(domain_name)
	#print user
	#print "11111111111111111111111111111"
	q = Q("match", type="Group")&Q("match", name=domain_name)
	s = Search(index ='nodes').using(client).query(q)
	res = s.execute()
	re = []
	for hit in res:
		for git in hit.collection_set:
			q = Q("match", id=git)
			s = Search(index ='nodes').using(client).query(q)
			nis = s.execute()
			re.append(nis)
			#print nis
	print res
	return render_to_response(
		"ndf/domain.html",
		{"res":re,"first_arg":domain_name})