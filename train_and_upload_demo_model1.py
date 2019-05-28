#!/usr/bin/env python

import sys
import json
import libsvm_formatter
import OperationFile
import GenerateQueryClass
import ExcuteSolrCommand

from optparse import OptionParser


def RunReRank(config, FileData):
    print("4 Create Query DataList")
    genqueries = GenerateQueryClass.GenerateQueries()
    print(FileData)
    reRankQueries = genqueries.generateQueriesExcelData(FileData, config["collection"], config["requestHandler"], config["solrFeatureStoreName"], config["efiParams"] )

    print("5 Running Solr queries to extract features")
    solrcmd = ExcuteSolrCommand.ExcuteSolr()
    fvGenerator = solrcmd.generateTrainingData(reRankQueries, config["host"], config["port"], config)
    formatter = libsvm_formatter.LibSvmFormatter()
    formatter.processQueryDocFeatureVector(fvGenerator, config["trainingFile"])
    print("6 Training model using '" + config["trainingLibraryLocation"] + " " + config["trainingLibraryOptions"] + "'")
    libsvm_formatter.trainLibSvm(config["trainingLibraryLocation"], config["trainingLibraryOptions"],
                                 config["trainingFile"], config["trainedModelFile"])
    print(
        "7 Converting trained model (" + config["trainedModelFile"] + ") to solr model (" + config["solrModelFile"] + ")")
    formatter.convertLibSvmModelToLtrModel(config["trainedModelFile"], config["solrModelFile"], config["solrModelName"],
                                           config["solrFeatureStoreName"])
    print("8 Uploading model (" + config["solrModelFile"] + ") to Solr")
    solrcmd.uploadModel(config["collection"], config["host"], config["port"], config["solrModelFile"], config["solrModelName"])
    print("------------------------END----------------------------")

def GetReRankQueries(config):
    # 批量读取文件夹内文件·
    print("3 Converting querier(" + config["userQueriesFilePath"] + " exchange file")
    openlistdir = OperationFile.OperationFiles

    #单个文件读取操作
    flist = openlistdir.GetFiles(openlistdir, config["userQueriesFilePath"])
    #print(flist)
    print("------------------------START----------------------------")
    for d in flist:
        print("Get Data by " + d)
        print("----------------------------------------------------")
        datalst = openlistdir.open_excel(openlistdir, d)
        RunReRank(config, datalst)

    #读取所有文件操作
    #filesdata = openlistdir.GetTranDataList(openlistdir, config["userQueriesFilePath"])
    #RunReRank(config, filesdata)

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
        print("1 Uploading features ("+config["solrFeaturesFile"]+") to Solr")
        solrcmd = ExcuteSolrCommand.ExcuteSolr()
        solrcmd.setupSolr(config["collection"], config["host"], config["port"], config["solrFeaturesFile"], config["solrFeatureStoreName"])

        print("2 Excute LTR Data")
        GetReRankQueries(config)


if __name__ == '__main__':
    sys.exit(main())
