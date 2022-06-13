'''
常用的条码生成库，pyBarcode，ReportLab（可输出pdf文件），pyStrich
https://cloud.tencent.com/developer/article/1570283
'''
from fileinput import filename
import string
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code39, code128, code93
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing 
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF


def gen_pdf(filename:string):
    c=canvas.Canvas(filename)

    barcode39Std = code39.Standard39('123456ABCD', barHeight=50, barWidth = 1.2, stop=1)
    print(barcode39Std.height, barcode39Std.width)

    # code93 also has an Extended and MultiWidth version
    barcode93 = code93.Standard93('123456ABCD', barHeight=50, barWidth = 1.2)

    barcode128 = code128.Code128('123456ABCD', barHeight=50, barWidth = 1.2)

    codes = [barcode39Std, barcode93, barcode128]

    x = 60 * mm
    y = 260 * mm

    for code in codes:
        code.drawOn(c, x, y)
        y = y - 30 * mm

    # draw the eanbc8 code
    barcode_eanbc8 = eanbc.Ean8BarcodeWidget('1234567') # 定长，数据位7位，加一个校验位，长度不够前端补'0'
    d = Drawing(50, 10)
    d.scale(1.5, 1)
    d.add(barcode_eanbc8)
    renderPDF.draw(d, c, 170, 450)

    # draw the eanbc13 code
    barcode_eanbc13 = eanbc.Ean13BarcodeWidget('123456789012') 
    d = Drawing(50, 10)
    d.scale(1.5, 1)
    d.add(barcode_eanbc13)
    renderPDF.draw(d, c, 170, 320)

    # draw a QR code
    qr_code = qr.QrCodeWidget('1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    
    d = Drawing(200, 200, transform=[100/width,0,0,100/height,0,0])
    d.add(qr_code)
    renderPDF.draw(d, c, 50, 100)
    
    d = Drawing(200, 200, transform=[150/width,0,0,150/height,0,0])
    d.add(qr_code)
    renderPDF.draw(d, c, 180, 100)

    d = Drawing(200, 200, transform=[200/width,0,0,200/height,0,0])
    d.add(qr_code)
    renderPDF.draw(d, c, 350, 100)

    #showPage函数：保存当前页的canvas
    c.showPage()
    #save函数：保存文件并关闭canvas
    c.save()
    


if __name__ == '__main__':
    gen_pdf('barcode_sample1.pdf')
