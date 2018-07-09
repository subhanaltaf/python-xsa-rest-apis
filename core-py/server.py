import os
from flask import Flask
from cfenv import AppEnv
from hdbcli import dbapi
import logging
from cf_logging import flask_logging
from sap import xssec
from flask import abort
from flask import request

import json
from flask import make_response
from flask import jsonify

#create instance of flask app
app = Flask(__name__)
env = AppEnv()

#set up logging
flask_logging.init(app, logging.INFO)
logger = logging.getLogger('route.logger')

#assign port for flask app
app_port = int(os.environ.get('PORT', 3000))

#get env variables for bound services
hana = env.get_service(name='hdi-db')
uaa_service = env.get_service(name='myuaa').credentials

#used to establish connection with HANA DB
def connectDB(serviceName):
    service = env.get_service(name=serviceName)
    conn = dbapi.connect(address=service.credentials['host'],
                         port= int(service.credentials['port']),
                         user = service.credentials['user'],
                         password = service.credentials['password'],
                         CURRENTSCHEMA=service.credentials['schema'])
    return conn

#used to check if user is authorized
def checkAuth(header):
    if 'authorization' not in request.headers:
        return False
    
    access_token = header.get('authorization')[7:]
    security_context = xssec.create_security_context(access_token, uaa_service)
    isAuthorized = security_context.check_scope('openid') or security_context.check_scope('uaa.resource')
    if not isAuthorized:
        return False

    return True

#used to read incoming POST, PUT, DELETE request args
def getRequestParams(data):
    params = {}
    req = data.decode('utf-8')[1:-1].split(',')
    for param in req:
        temp = param.split(':')
        params[temp[0][1:-1]] = temp[1].strip()[1:-1]

    return params

@app.route('/')
def hello():
    #authorize user
    logger.info('Authorization successful') if checkAuth(request.headers) else abort(403)

    #establish db connection
    conn = connectDB('hdi-db')
    logger.info('Database connection successful: ' + str(conn.isconnected()))
                        
    cursor = conn.cursor()
    
    cursor.execute('SELECT CURRENT_USER FROM DUMMY')
    techUser = cursor.fetchone()['CURRENT_USER']
    cursor.execute('SELECT SESSION_CONTEXT(\'APPLICATIONUSER\') "APPLICATION_USER" FROM "DUMMY"')
    appUser = cursor.fetchone()['APPLICATION_USER']
    
    #html output
    output = '<h1>Welcome to SAP HANA!</h1><p>Technical User: %s</p><p>Application User: %s</p>' % (techUser, appUser)

    cursor.close()
    conn.close()
                
    return output

@app.route('/viewProduct', methods=['GET'])
def viewProduct():
    #authorize user
    logger.info('Authorization successful') if checkAuth(request.headers) else abort(403)

    #establish db connection
    conn = connectDB('hdi-db')
    logger.info('Database connection successful: ' + str(conn.isconnected()))

    cursor = conn.cursor()

    #check if the user has specified any parameters
    if (bool(request.args)):
        #check if user has provided number of results or category
        if 'category' in request.args:
            #if category is provided, query all products from category
            categories = request.args['category'].split(',')
            query = 'SELECT * FROM "Product.Products" WHERE '
            for item in categories:
                query += "CATEGORY='" + item + "' OR "
            query = query[:-3]
        #if number is provided, query that number of results
        elif 'number' in request.args:
            if (request.args['number'] == 'all'):
                query = 'SELECT * FROM "MDViews.ProductView"'
            else:
                query = 'SELECT * FROM "MDViews.ProductView" LIMIT ' + request.args['number']

        logger.info(query)      #log query for debugging
        cursor.execute(query)

        #format results in to a list of JSON objects
        results = []
        i = 0
        for row in cursor.fetchall():
            i = i + 1
            results.append(json.dumps({str(i): str(row)}))

        #send response
        return make_response(jsonify({"results" : results}), 200)

    #if no parameters specified
    else:
        return make_response(jsonify({"Error": "No category specified."}), 404)

@app.route('/addProduct', methods=['POST'])
def addProduct():
    #authorize user
    logger.info('Authorization successful') if checkAuth(request.headers) else abort(403)

    #establish db connection
    conn = connectDB('hdi-db')
    logger.info('Database connection successful: ' + str(conn.isconnected()))

    cursor = conn.cursor()

    params = getRequestParams(request.data)

    in_params = (params['productID'], params['category'], float(params['price']), None)
    output = cursor.callproc('"insert_product_data"', in_params)
    
    cursor.close()

    return str(output)

@app.route('/changePrice', methods=['PUT'])
def changePrice():
    #authorize user
    logger.info('Authorization successful') if checkAuth(request.headers) else abort(403)

    #establish db connection
    conn = connectDB('hdi-db')
    logger.info('Database connection successful: ' + str(conn.isconnected()))

    cursor = conn.cursor()
    params = getRequestParams(request.data)

    in_params = (params['productID'], float(params['newPrice']), None)
    output = cursor.callproc('"update_product_prices"', in_params)

    cursor.close()
    return str(output)

@app.route('/deleteProduct', methods=['DELETE'])
def deleteProduct():
    #authorize user
    logger.info('Authorization successful') if checkAuth(request.headers) else abort(403)

    #establish db connection
    conn = connectDB('hdi-db')
    logger.info('Database connection successful: ' + str(conn.isconnected()))

    cursor = conn.cursor()
    params = getRequestParams(request.data)
    sql_query = 'DELETE FROM "Product.Products" WHERE PRODUCTID = ' + params['productID'] + ';'
    
    logger.info(sql_query)
    cursor.execute(sql_query)
    
    return 'Product ' + params['productID'] + ' has been deleted.'

if __name__ == '__main__':
    app.run(port=app_port)
