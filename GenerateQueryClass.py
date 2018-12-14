import ExcuteSolrCommand

class GenerateQueries:
    def generateQueries(self, userQueriesFile, collection, requestHandler, solrFeatureStoreName, efiParams):
        with open(userQueriesFile, encoding="utf-8") as input:
            solrQueryUrls = []  # A list of tuples with solrQueryUrl,solrQuery,docId,scoreForPQ,source
            for line in input:
                line = line.strip()
                searchText, docId, score, source = line.split("|")
                #  print(line)
                solrQuery = generateHttpRequest(collection, requestHandler, solrFeatureStoreName, efiParams, searchText,
                                                docId)
                solrQueryUrls.append((solrQuery, searchText, docId, score, source))
        # print(solrQueryUrls)
        return solrQueryUrls


    def generateQueriesExcel(self, userQueriesFile, collection, requestHandler, solrFeatureStoreName, efiParams):
        solrQueryUrls = []  # A list of tuples with solrQueryUrl,solrQuery,docId,scoreForPQ,source
        datalst = open_excel(userQueriesFile)
        solrcmd= ExcuteSolrCommand.ExcuteSolr()
        for searchText, docId, score, source in datalst:
            solrQuery = solrcmd.generateHttpRequest(collection, requestHandler, solrFeatureStoreName, efiParams, searchText, docId)
            solrQueryUrls.append((solrQuery, searchText, docId, score, source))
        # print(solrQueryUrls)
        return solrQueryUrls


    def generateQueriesExcelData(self, UserQueriesFiles, collection, requestHandler, solrFeatureStoreName, efiParams):
        solrQueryUrls = []
        solrcmd = ExcuteSolrCommand.ExcuteSolr()
        #print(UserQueriesFiles)
        for searchText, docId, score, source in UserQueriesFiles:
            #print(searchText)
            solrQuery = solrcmd.generateHttpRequest(collection, requestHandler, solrFeatureStoreName, efiParams, searchText, docId)
            solrQueryUrls.append((solrQuery, searchText, docId, score, source))
        return solrQueryUrls
