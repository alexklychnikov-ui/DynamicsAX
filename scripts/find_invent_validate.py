import re
data=open("AOT_cus/PrivateProject_CUS_Layer_Export.xpo","rb").read()
pos=data.find(b"TABLE #InventTable")
sub=data[pos:pos+2000000]
for m in re.finditer(rb"SOURCE #validateFieldValue", sub):
    chunk=m.group(0)+sub[m.start():m.start()+20000]
    if chunk.count(b"NoYes::Yes")>=2:
        txt=chunk.decode("utf-8","replace")
        if "case fieldnum" in txt:
            lines=[l[1:] for l in txt.split("ENDSOURCE")[0].split("\n") if l.startswith("#")][:80]
            print("\n".join(lines))
            break
