import os
import xlrd

#读取文件夹下文件
class OperationFiles:
    def GetTranDataList(self, filepath):
        files = os.listdir(os.curdir + "/" + filepath)
        filedatalist = []
        for file in files:
            data = xlrd.open_workbook(filepath + "/" + file)
            table = data.sheet_by_name("ExportScoreData")
            nrows = table.nrows  # 行数
            for rownum in range(1, nrows):  # 遍历每一行的内容
                row = table.row_values(rownum)  # 根据行号获取行
                if row:  # 如果行存在
                    filedatalist.append(row)  # 装载数据
        return filedatalist

    def open_excel(self, userQueriesFile):
        data = xlrd.open_workbook(userQueriesFile)
        table = data.sheet_by_name("ExportScoreData")
        nrows = table.nrows  # 行数
        list = []  # 装读取结果的序列
        for rownum in range(1, nrows):  # 遍历每一行的内容
            row = table.row_values(rownum)  # 根据行号获取行
            if row:  # 如果行存在
                list.append(row)  # 装载数据
        return list

    def GetFiles(self, filepath):
        files = os.listdir(os.curdir + "/" + filepath)
        filelist = []
        for file in files:
            filelist.append(file)
        #print(filelist)
        return filelist
