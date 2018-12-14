import json
import http.client
import urllib

solrQueryUrl = ""


class ExcuteSolr:
    def setupSolr(self, collection, host, port, featuresFile, featureStoreName):
        '''Sets up solr with the proper features for the test'''
        conn = http.client.HTTPConnection(host, port)
        baseUrl = "/solr/" + collection
        featureUrl = baseUrl + "/schema/feature-store"
        # conn.request("DELETE", featureUrl+"/JapanDocFeatureStore")
        # r1 = conn.getresponse()

        conn.request("DELETE", featureUrl + "/" + featureStoreName)
        r = conn.getresponse()
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
        r = conn.getresponse()
        msg = r.read()
        if (r.status != http.client.OK and r.status != http.client.ACCEPTED):
            raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))
        conn.close()

    def generateHttpRequest(self, collection, requestHandler, solrFeatureStoreName, efiParams, searchText, docId):
        global solrQueryUrl
        if len(solrQueryUrl) < 1:
            solrQueryUrl = "/".join(["", "solr", collection, requestHandler])
            solrQueryUrl += ("?fl=" + ",".join(
                ["id", "score", "[features store=" + solrFeatureStoreName + " " + efiParams + "]"]))
            solrQueryUrl += "&q="
            solrQueryUrl = solrQueryUrl.replace(" ", "+")
            solrQueryUrl += urllib.parse.quote_plus("id:")
        userQuery = urllib.parse.quote_plus(searchText.strip().replace("'", "\\'").replace("/", "\\\\/"))
        solrQuery = solrQueryUrl + '"' + urllib.parse.quote_plus(docId) + '"'  # + solrQueryUrlEnd
        solrQuery = solrQuery.replace("%24USERQUERY", userQuery).replace('$USERQUERY', urllib.parse.quote_plus(
            "\\'" + userQuery + "\\'"))
        print(solrQuery)
        return solrQuery

    def generateTrainingData(self, solrQueries, host, port):
        '''Given a list of solr queries, yields a tuple of query , docId , score , source , feature vector for each query.
        Feature Vector is a list of strings of form "key=value"'''
        conn = http.client.HTTPConnection(host, port)
        headers = {"Connection": " keep-alive"}
        try:
            for queryUrl, query, docId, score, source in solrQueries:
                conn.request("GET", queryUrl, headers=headers)
                r = conn.getresponse()
                msg = r.read()
                msgDict = json.loads(msg)
                fv = ""
                docs = msgDict['response']['docs']
                if len(docs) > 0 and "[features]" in docs[0]:
                    if not msgDict['response']['docs'][0]["[features]"] == None:
                        fv = msgDict['response']['docs'][0]["[features]"]
                    else:
                        print("ERROR NULL FV FOR: " + docId)
                        print(msg)
                        continue
                else:
                    print("ERROR FOR: " + docId)
                    print(msg)
                    continue

                if r.status == http.client.OK:
                    yield (query, docId, score, source, fv.split(","))
                else:
                    raise Exception("Status: {0} {1}\nResponse: {2}".format(r.status, r.reason, msg))
        except Exception as e:
            print(msg)
            print(e)
        conn.close()

    def uploadModel(self, collection, host, port, modelFile, modelName):
        modelUrl = "/solr/" + collection + "/schema/model-store"
        headers = {'Content-type': 'application/json'}
        with open(modelFile) as modelBody:
            conn = http.client.HTTPConnection(host, port)
            conn.request("DELETE", modelUrl + "/" + modelName)
            r = conn.getresponse()
            msg = r.read()
            print(r.status)
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
