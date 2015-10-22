from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.db import connection

def test_pg(request):
	if request.method != 'GET':
		return HttpResponse(status=400)



	cursor = connection.cursor()
	cursor.execute("CREATE TEMP VIEW temp2 AS (select * from test)")
	cursor.execute("select id from temp2")
	row = cursor.fetchone()
	print (row)
	return HttpResponse(row)
