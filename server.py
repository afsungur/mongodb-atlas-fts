from flask import Flask, render_template, request, jsonify
import os
import pymongo
import ssl
from bson import json_util
from config import mongo_uri
import ast


app = Flask(__name__)
conn = pymongo.MongoClient(mongo_uri, ssl_cert_reqs=ssl.CERT_NONE)
collection = conn['sample_mflix']['movies']

# endpoint
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


# page
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/compound')
def index_compound():
    return render_template("compound.html")

if __name__ == '__main__':
    app.run(host="localhost", port=5010, debug=True)
