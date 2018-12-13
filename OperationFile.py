import os
import xlrd

class OperationFiles:
    def GetTranDataList(self, filepath):
        files = os.listdir(os.curdir+"/"+filepath)
        filedatalist = []
        #print(files)
        for file in files:
            data = xlrd.open_workbook(filepath + "/" + file)
            table = data.sheet_by_name("ExportScoreData")
            nrows = table.nrows  # 行数
            for rownum in range(1, nrows):  # 遍历每一行的内容
                row = table.row_values(rownum)  # 根据行号获取行
                if row:  # 如果行存在
                    filedatalist.append(row)  # 装载数据
        return filedatalist