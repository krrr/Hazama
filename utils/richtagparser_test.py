import richtagparser

html = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'SimSun'; font-size:10pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">t<span style=" font-style:italic;">es</span>t<span style=" background-color:#fffaa0;">t</span><span style=" text-decoration: line-through; background-color:#fffaa0;">es</span><span style=" background-color:#fffaa0;">t</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">t<span style=" text-decoration: underline;">es</span>t&gt;t<span style=" text-decoration: underline;">es</span>t</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">testtest</span></p></body></html>'''
plaintxt = richtagparser.strip.sub('', html.split('</head>')[1])
p = richtagparser.QtHtmlParser()
formats = p.feed(html)
for i in [(1,2,3), (4,1,2), (5,2,4), (5,2,2), (7,1,2), (10,2,5), (15,2,5),
    (19,8,1)]:
    assert i in formats
assert len(formats)==8
