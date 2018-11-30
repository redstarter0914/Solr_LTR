#!/usr/bin/env python

import sys
import json
import http.client
import urllib
import libsvm_formatter

from optparse import OptionParser

solrQueryUrl = ""


def setupSolr(collection, host, port, featuresFile, featureStoreName):
    '''Sets up solr with the proper features for the test'''

    conn = http.client.HTTPConnection(host, port)

    baseUrl = "/solr/" + collection
    featureUrl = baseUrl + "/schema/feature-store"

    conn.request("DELETE", featureUrl+"/"+featureStoreName)
    r = conn.getresponse()
   # print(r.status)
    msg = r.read()
    if (r.status != http.client.OK and
       r.status != http.client.CREATED and
       r.status != http.client.ACCEPTED and
       r.status != http.client.NOT_FOUND):
       raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))


    # Add features
    headers = {'Content-type': 'application/json'}
    featuresBody = open(featuresFile)

    conn.request("POST", featureUrl, featuresBody, headers)
   # print(featureUrl)
   # print(featuresBody)
    r = conn.getresponse()
    #print(r.status)
    msg = r.read()
    #print(msg)
    if (r.status != http.client.OK and
        r.status != http.client.ACCEPTED):
        #print(r.status)
        #print("")
        #print(r.reason)
        raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))

    conn.close()


def generateQueries(userQueriesFile, collection, requestHandler, solrFeatureStoreName, efiParams):

        with open(userQueriesFile, encoding="utf-8") as input:
            solrQueryUrls = [] #A list of tuples with solrQueryUrl,solrQuery,docId,scoreForPQ,source
            #print(userQueriesFile)
            for line in input:
                line = line.strip()
                searchText, docId, score, source = line.split("|")
              #  print(line)
                solrQuery = generateHttpRequest(collection, requestHandler, solrFeatureStoreName, efiParams, searchText, docId)
                solrQueryUrls.append((solrQuery, searchText, docId, score, source))

        return solrQueryUrls


def generateHttpRequest(collection, requestHandler, solrFeatureStoreName, efiParams, searchText, docId):
    global solrQueryUrl
    if len(solrQueryUrl) < 1:
        solrQueryUrl = "/".join(["", "solr", collection, requestHandler])
       # print(solrQueryUrl)
        solrQueryUrl += ("?fl=" + ",".join(["id", "score", "[features store="+solrFeatureStoreName+" "+efiParams+"]"]))
       # print(solrQueryUrl)
        solrQueryUrl += "&q="
        solrQueryUrl = solrQueryUrl.replace(" ", "+")
        #print(solrQueryUrl)
        solrQueryUrl += urllib.parse.quote_plus("id:")

        #print(solrQueryUrl)

    userQuery = urllib.parse.quote_plus(searchText.strip().replace("'", "\\'").replace("/", "\\\\/"))
    solrQuery = solrQueryUrl + '"' + urllib.parse.quote_plus(docId) + '"' #+ solrQueryUrlEnd
    solrQuery = solrQuery.replace("%24USERQUERY", userQuery).replace('$USERQUERY', urllib.parse.quote_plus("\\'" + userQuery +"\\'"))
    #print(solrQueryUrl)
    return solrQuery


def generateTrainingData(solrQueries, host, port):
    '''Given a list of solr queries, yields a tuple of query , docId , score , source , feature vector for each query.
    Feature Vector is a list of strings of form "key=value"'''
    conn = http.client.HTTPConnection(host, port)
    headers = {"Connection": " keep-alive"}

    #print(solrQueries)
    #print(host)
   #print(port)
    try:
        for queryUrl, query, docId, score, source in solrQueries:
            conn.request("GET", queryUrl, headers=headers)
            r = conn.getresponse()
           # print(queryUrl)
            msg = r.read()
            msgDict = json.loads(msg)

            #print("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))
            fv = ""
            docs = msgDict['response']['docs']
            if len(docs) > 0 and "[features]" in docs[0]:
                if not msgDict['response']['docs'][0]["[features]"] == None:
                    fv = msgDict['response']['docs'][0]["[features]"]
                   # print(fv)
                else:
                    print("ERROR NULL FV FOR: " + docId)
                    print(msg)
                    continue
            else:
                print("ERROR FOR: " + docId)
                print(msg)
                continue

            if r.status == http.client.OK:
               # print("http connection was ok for: " + queryUrl)

                yield(query, docId, score, source, fv.split(","))
            else:
                raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))
    except Exception as e:
        print(msg)
        print(e)

    conn.close()


def uploadModel(collection, host, port, modelFile, modelName):
    modelUrl = "/solr/" + collection + "/schema/model-store"
    headers = {'Content-type': 'application/json'}
    with open(modelFile) as modelBody:
        conn = http.client.HTTPConnection(host, port)

        conn.request("DELETE", modelUrl+"/"+modelName)
        r = conn.getresponse()
        msg = r.read()
       # print(modelUrl)
        if (r.status != http.client.OK and
            r.status != http.client.CREATED and
            r.status != http.client.ACCEPTED and
            r.status != http.client.NOT_FOUND):
            raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))

        conn.request("POST", modelUrl, modelBody, headers)
        r = conn.getresponse()
        msg = r.read()
        if (r.status != http.client.OK and
            r.status != http.client.CREATED and
            r.status != http.client.ACCEPTED):
                raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = OptionParser(usage="usage: %prog [options] ", version="%prog 1.0")
    parser.add_option('-c', '--config',
                      dest='configFile',
                      help='File of configuration for the test')

    (options, args) = parser.parse_args()

    if options.configFile == None:
        parser.print_help()
        return 1

    with open(options.configFile) as configFile:
        config = json.load(configFile)
        print("Uploading features ("+config["solrFeaturesFile"]+") to Solr")
        setupSolr(config["collection"], config["host"], config["port"], config["solrFeaturesFile"], config["solrFeatureStoreName"])

        print("Converting user queries ("+config["userQueriesFile"]+") into Solr queries for feature extraction")
        reRankQueries = generateQueries(config["userQueriesFile"], config["collection"], config["requestHandler"], config["solrFeatureStoreName"], config["efiParams"])
        #print(1)
        print("Running Solr queries to extract features")
        fvGenerator = generateTrainingData(reRankQueries, config["host"], config["port"])
        formatter = libsvm_formatter.LibSvmFormatter()
        formatter.processQueryDocFeatureVector(fvGenerator, config["trainingFile"])
        #print(2)
        print("Training model using '"+config["trainingLibraryLocation"]+" "+config["trainingLibraryOptions"]+"'")
        libsvm_formatter.trainLibSvm(config["trainingLibraryLocation"], config["trainingLibraryOptions"], config["trainingFile"], config["trainedModelFile"])
        #print(3)
        print("Converting trained model ("+config["trainedModelFile"]+") to solr model ("+config["solrModelFile"]+")")
        formatter.convertLibSvmModelToLtrModel(config["trainedModelFile"], config["solrModelFile"], config["solrModelName"], config["solrFeatureStoreName"])
        #print(4)
        print("Uploading model ("+config["solrModelFile"]+") to Solr")
        uploadModel(config["collection"], config["host"], config["port"], config["solrModelFile"], config["solrModelName"])


if __name__ == '__main__':
    sys.exit(main())
