# -*- coding: utf-8 -*-
import xml.dom.minidom as m, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

doc = m.parse("installation_pv_synoptique.drawio")
fig, ax = plt.subplots(figsize=(17.5, 13))
geo_by_id = {}
for c in doc.getElementsByTagName("mxCell"):
    cid = c.getAttribute("id")
    style = c.getAttribute("style")
    val = c.getAttribute("value")
    g = c.getElementsByTagName("mxGeometry")
    if c.getAttribute("vertex") == "1" and g:
        gg = g[0]
        try:
            x=float(gg.getAttribute("x")); y=float(gg.getAttribute("y"))
            w=float(gg.getAttribute("width")); h=float(gg.getAttribute("height"))
        except: continue
        geo_by_id[cid]=(x+w/2, y+h/2)
        color="#dddddd"; ec="#666"
        if "image=" in style: color="#cfe8ff"; ec="#1B75BB"
        if "E60000" in style and "BUS" in val: color="#ff6666"
        if "1A1A1A" in style: color="#444"
        if "FFF3CD" in style: color="#fff3cd"
        ax.add_patch(mp.Rectangle((x,y), w, h, facecolor=color, edgecolor=ec, lw=0.8, alpha=0.85))
        short = val.replace("<b>","").replace("</b>","").split("<br/>")[0][:24]
        ax.text(x+3, y+12, f"{cid}", fontsize=5, color="#333")
        if short: ax.text(x+w/2, y+h/2, short, fontsize=5, ha="center", va="center")
# edges
for c in doc.getElementsByTagName("mxCell"):
    if c.getAttribute("edge")=="1":
        s=c.getAttribute("source"); t=c.getAttribute("target")
        if s in geo_by_id and t in geo_by_id:
            x1,y1=geo_by_id[s]; x2,y2=geo_by_id[t]
            col="#999"
            st=c.getAttribute("style")
            if "E60000" in st: col="red"
            elif "111111" in st: col="black"
            elif "8B4513" in st: col="brown"
            elif "1B75BB" in st: col="blue"
            elif "1E8449" in st: col="green"
            elif "B8860B" in st: col="goldenrod"
            elif "2E7D32" in st: col="green"
            ax.plot([x1,x2],[y1,y2], color=col, lw=0.8, alpha=0.6)
ax.set_xlim(0,1754); ax.set_ylim(1300,0)
ax.set_aspect("equal"); ax.axis("off")
plt.tight_layout()
plt.savefig("assets/components/_layout_preview.png", dpi=80)
print("preview saved")
