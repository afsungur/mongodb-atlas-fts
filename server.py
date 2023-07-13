from flask import Flask, render_template, request, jsonify
import os
import pymongo
import ssl
from bson import json_util
from config import mongo_uri
import ast
import json

app = Flask(__name__,             
            static_url_path='', 
            static_folder='templates/static',)
conn = pymongo.MongoClient(mongo_uri)
collection = conn['sample_mflix']['movies']
collection_airbnb = conn['sample_airbnb']['listingsAndReviews']
# endpoint``
@app.route('/search', methods=['GET'])
def search():
    with open("queries/query01.json", "r", encoding = 'utf-8') as query_file:
      agg_query=query_file.read()
    
    # Get the parameters from HTTP GET request
    queryParameters = request.args.get('query', default=None, type=str)

    # Replace the placeholder in query json file with the query parameters from HTTP
    agg_query=agg_query.replace("!!queryParameter!!", queryParameters)

    print(agg_query)

    # Generate pipeline
    agg_pipeline = ast.literal_eval(agg_query)

    # Execute the pipeline
    docs = list(collection.aggregate(agg_pipeline))

    # Return the results unders the docs array field
    json_result = json_util.dumps({'docs': docs}, json_options=json_util.RELAXED_JSON_OPTIONS)
    
    return jsonify(json_result)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', default=None, type=str)
    agg_pipeline =  [
        { 
            "$search": {
                "index" : "title_autocomplete",
                "autocomplete": {
                    "path": "title",
                    "query": query,
                    "fuzzy": {
                        "maxEdits": 1,
                        "maxExpansions": 100,
                    }
                }
            }
        },
        { 
            "$project": { 
                "title": 1, 
                "_id": 0, 
                "year": 1, 
                "fullplot": 1 
            }
        }, 
        {
            "$limit": 15
        }
    ]

    docs = list(collection.aggregate(agg_pipeline))
    return jsonify(docs)


@app.route('/searchCompound', methods=['GET'])
def search_compound():
    with open("queries/query12.json", "r", encoding = 'utf-8') as query_file:
      agg_query=query_file.read()
    
    # Get the parameters from HTTP GET request
    queryParametersAll = request.args.get('queryAll', default=None, type=str)
    queryParametersTitle = request.args.get('queryTitle', default=None, type=str)
    queryParametersFullplot = request.args.get('queryFullplot', default=None, type=str)
    queryParametersPlot = request.args.get('queryPlot', default=None, type=str)
    queryParametersCast = request.args.get('queryCast', default=None, type=str)

    # Replace the placeholder in query json file with the query parameters from HTTP
    agg_query=agg_query.replace("!!queryParameterAllTheFields!!", queryParametersAll)
    agg_query=agg_query.replace("!!queryParameterTitle!!", queryParametersTitle)
    agg_query=agg_query.replace("!!queryParameterFullplot!!", queryParametersFullplot)
    agg_query=agg_query.replace("!!queryParameterPlot!!", queryParametersPlot)
    agg_query=agg_query.replace("!!queryParameterCast!!", queryParametersCast)

    print(agg_query)

    # Generate pipeline
    agg_pipeline = ast.literal_eval(agg_query)

    # Execute the pipeline
    docs = list(collection.aggregate(agg_pipeline))

    # Return the results unders the docs array field
    json_result = json_util.dumps({'docs': docs}, json_options=json_util.RELAXED_JSON_OPTIONS)
    print(json_result)
    return jsonify(json_result)


@app.route('/geoWithin', methods=['GET'])
def geo_within():
    json_result = ""

    query_parameter_shape = request.args.get('shape', default=None, type=str)
    if ( query_parameter_shape == "circle" ):
        query_parameter_radius = request.args.get('radius', default=None, type=str)
        query_parameter_lat = request.args.get('latitude', default=None, type=str)
        query_parameter_lng = request.args.get('longtitude', default=None, type=str)
        with open("queries/query30.json", "r", encoding = 'utf-8') as query_file:
            agg_query=query_file.read()
            json_agg_query=json.loads(agg_query)
            json_agg_query[0]['$search']['geoWithin']['circle']['radius'] = int (query_parameter_radius)
            coord_array = []
            coord_array.append(float(query_parameter_lng))
            coord_array.append(float(query_parameter_lat))
            json_agg_query[0]['$search']['geoWithin']['circle']['center']['coordinates'] = coord_array
            print(json_agg_query)
            docs = list(collection_airbnb.aggregate(json_agg_query))
            json_result = json_util.dumps({'docs': docs}, json_options=json_util.RELAXED_JSON_OPTIONS)
    elif  ( query_parameter_shape == "box" ):
        query_parameter_lat0 = request.args.get('latitude0', default=None, type=float)
        query_parameter_lng0 = request.args.get('longtitude0', default=None, type=float)
        query_parameter_lat1 = request.args.get('latitude1', default=None, type=float)
        query_parameter_lng1 = request.args.get('longtitude1', default=None, type=float)
        with open("queries/query31.json", "r", encoding = 'utf-8') as query_file:
            agg_query=query_file.read()
            json_agg_query=json.loads(agg_query)

            bottom_left_coord_array = []
            bottom_left_coord_array.append(query_parameter_lng0)
            bottom_left_coord_array.append(query_parameter_lat0)

            top_right_coord_array = []
            top_right_coord_array.append(query_parameter_lng1)
            top_right_coord_array.append(query_parameter_lat1)

            json_agg_query[0]['$search']['geoWithin']['box']['bottomLeft']['coordinates'] = bottom_left_coord_array
            json_agg_query[0]['$search']['geoWithin']['box']['topRight']['coordinates'] = top_right_coord_array

            print(json_agg_query)
            docs = list(collection_airbnb.aggregate(json_agg_query))
            json_result = json_util.dumps({'docs': docs}, json_options=json_util.RELAXED_JSON_OPTIONS)

    elif  ( query_parameter_shape in ["polygon","multipolygon"] ):
        queryParameterCoordinateString01 = request.args.get('coordinatesPolygon01', default=None, type=str)
        multi_polygons_array = []
        coord_array = queryParameterCoordinateString01.split("|")
        polygon = []
        coord_array_atlasfts = []
        for coord in coord_array:
            tmp_coord_array_str = coord.split(",")
            print(tmp_coord_array_str)
            tmp_coord_array_float = []
            tmp_coord_array_float.append(float(tmp_coord_array_str[0]))
            tmp_coord_array_float.append(float(tmp_coord_array_str[1]))
            coord_array_atlasfts.append(tmp_coord_array_float)
        coord_array_atlasfts.append(coord_array_atlasfts[0])
        polygon.append(coord_array_atlasfts)
        multi_polygons_array.append(polygon)
        
        queryParameterCoordinateString02 = request.args.get('coordinatesPolygon02', default=None, type=str)
        if (queryParameterCoordinateString02 != None and queryParameterCoordinateString02 != ""):
            polygon = []
            coord_array = queryParameterCoordinateString02.split("|")
            coord_array_atlasfts_2 = []
            for coord in coord_array:
                tmp_coord_array_str = coord.split(",")
                print(tmp_coord_array_str)
                tmp_coord_array_float = []
                tmp_coord_array_float.append(float(tmp_coord_array_str[0]))
                tmp_coord_array_float.append(float(tmp_coord_array_str[1]))
                coord_array_atlasfts_2.append(tmp_coord_array_float)
            coord_array_atlasfts_2.append(coord_array_atlasfts_2[0])
            polygon.append(coord_array_atlasfts_2)
            multi_polygons_array.append(polygon)
        
        
        with open("queries/query32.json", "r", encoding = 'utf-8') as query_file:
            agg_query=query_file.read()
            json_agg_query=json.loads(agg_query)
            if ( len(multi_polygons_array) == 2):
                json_agg_query[0]['$search']['geoWithin']['geometry']['type'] = 'MultiPolygon'
                json_agg_query[0]['$search']['geoWithin']['geometry']['coordinates'] = multi_polygons_array
            else:
                json_agg_query[0]['$search']['geoWithin']['geometry']['type'] = 'Polygon'
                json_agg_query[0]['$search']['geoWithin']['geometry']['coordinates'] = polygon
            
            print(json_agg_query)
            docs = list(collection_airbnb.aggregate(json_agg_query))
            json_result = json_util.dumps({'docs': docs}, json_options=json_util.RELAXED_JSON_OPTIONS)

    return jsonify(json_result)


@app.route('/geoNear', methods=['GET'])
def geo_near():
    query_parameter_pivot = request.args.get('pivot', default=None, type=int)
    query_parameter_lat = request.args.get('latitude', default=None, type=str)
    query_parameter_lng = request.args.get('longtitude', default=None, type=str)
    query_parameter_property_type = request.args.get('property_type', default=None, type=str)
    query_parameter_description = request.args.get('keyword', default=None, type=str)
    with open("queries/query34.json", "r", encoding = 'utf-8') as query_file:
        agg_query=query_file.read()
        json_agg_query=json.loads(agg_query)
        coord_array = []
        coord_array.append(float(query_parameter_lng))
        coord_array.append(float(query_parameter_lat))
        json_agg_query[0]['$search']['compound']['should'][0]['near']['pivot'] = query_parameter_pivot
        json_agg_query[0]['$search']['compound']['should'][0]['near']['origin']['coordinates'] = coord_array
        json_agg_query[0]['$search']['compound']['must']['text']['query'] = query_parameter_property_type
        json_agg_query[0]['$search']['compound']['should'][1]['text']['query'] = query_parameter_description
        print(json_agg_query)
        docs = list(collection_airbnb.aggregate(json_agg_query))
        json_result = json_util.dumps({'docs': docs}, json_options=json_util.RELAXED_JSON_OPTIONS)
    return jsonify(json_result)

# page
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/autocomplete_test')
def index_autocomplete_page():
    return render_template("autocomplete_test.html")

@app.route('/highlight_title_test')
def index_highlight_title_test():
    return render_template("highlight_title_test.html")

@app.route('/highlight_fullplot_test')
def index_highlight_fullplot_test():
    return render_template("highlight_fullplot_test.html")

@app.route('/compound')
def index_compound():
    return render_template("compound.html")

@app.route('/geo')
def index_geo():
    return render_template("geo.html")

@app.route('/geonear')
def index_geo_near():
    return render_template("geonear.html")

if __name__ == '__main__':
    app.run(host="localhost", port=5010, debug=True)
