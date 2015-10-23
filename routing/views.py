from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.db import connection
import json

# Create your views here.

def index(request):
	return render(request, 'index.html')

def do_routing(request):
	if not request.method == 'GET':
		return HttpResponse(status=400)

	source = ['','']
	target = ['','']

	source[0] = request.GET.get('source_lat','')
	source[1] = request.GET.get('source_lon','')
	target[0] = request.GET.get('target_lat','')
	target[1] = request.GET.get('target_lon','')


	if source[0] == '' or source[1] == '' or target[0] == '' or target[1] == '':
		return HttpResponseForbidden('Parameter is forbitted of None value.')

	routing_source, np_source = __get_routing_id(source, target, "temp1")
	routing_target, np_target = __get_routing_id(target, source, "temp2")

	dijstra_path = __dijstra(routing_source, routing_target)


	# Follow GeoJson type,  Ref: http://leafletjs.com/examples/geojson.html
	response = dict()
	coordinates, length_total = __transfer_path_id_to_position(dijstra_path, np_source, np_target)

	geometry = dict()
	geometry['type'] = "LineString"
	geometry['coordinates'] = coordinates

	properties = dict()
	properties['length_total'] = length_total
	properties['source'] = source
	properties['target'] = target

	response['type'] =  "Feature"
	response['geometry'] = geometry
	response['properties'] = properties

	return HttpResponse(json.dumps(response), status=200, content_type='application/json')

def __transfer_path_id_to_position(path, np_source, np_target):
	cursor = connection.cursor()

	coordinates = list()
	coordinates.append([float(np_source[0]), float(np_source[1])])
	total_length = 0
	for tu in path:		# tu: id,node,edge,length
		cursor.execute("SELECT x1,y1 from ways where source={0}".format(tu[1]))
		row = cursor.fetchall()
		if not len(row)>0:
			cursor.execute("SELECT x2,y2 from ways where target={0}".format(tu[1]))
			row = cursor.fetchall()

		lonlat = row[0]
		coordinates.append([lonlat[0], lonlat[1]])
		total_length += tu[3]
	coordinates.append([float(np_target[0]), float(np_target[1])])
	return coordinates, total_length

def __dijstra(s, d):
	cursor = connection.cursor()

	cursor.execute("SELECT seq, id1 as node, id2 as edge, cost FROM pgr_dijkstra(' SELECT gid AS id, source::integer, target::integer, length::double precision AS cost FROM ways', {0}, {1}, false, false)".format(s,d))
	row = cursor.fetchall()
	return row

def __get_routing_id(source, target, view_name):
	point_id = ""
	
	cursor = connection.cursor()
	cursor.execute("CREATE TEMP VIEW {2} AS (\
		SELECT points.np as np, source, x1, y1, target, x2, y2 FROM\
		(SELECT ST_AsText(ST_Line_Interpolate_Point(the_geom, ST_Line_Locate_Point(the_geom, ST_GeomFromText('POINT( {0}\
		 {1})',4326)))) AS np , source, target, x1, y1, x2, y2\
		FROM ways WHERE the_geom && ST_Expand(ST_GeomFromText('POINT({0} {1})',4326), 10)) AS points \
		ORDER BY ST_Distance(ST_GeomFromText(points.np,4326),ST_GeomFromText('POINT({0} {1})',4326)) LIMIT 1)".\
		format(source[1], source[0], view_name))

	# Get nearest point (np)
	cursor.execute("SELECT np from {0}".format(view_name))
	row = cursor.fetchall()
	np = row[0][0]
	

	cursor.execute("SELECT ST_Distance(ST_GeomFromText(FORMAT('POINT(%s %s)',x1,y1),4326),ST_GeomFromText('POINT({0} {1})',4326)) > \
		ST_Distance(ST_GeomFromText(FORMAT('POINT(%s %s)',x2,y2), 4326),ST_GeomFromText('POINT({0} {1})',4326)) from {2}".\
		format(target[1], target[0], view_name))

	row = cursor.fetchall()

	if row[0][0] == True:
		# choose x2, y2
		cursor.execute("SELECT target FROM {0}".format(view_name))
		row = cursor.fetchone()
		point_id = row[0]
	else:
		cursor.execute("SELECT source FROM {0}".format(view_name))
		row = cursor.fetchone()
		point_id = row[0]

	np = np[:-1]
	np = np.split("(")[1]
	np = np.split(" ")

	return point_id, np
