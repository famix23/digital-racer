#!/usr/bin/env python3
"""Build Instagram draft content from DigitalRacer's real inventory. No publishing."""
import csv
import json
import argparse
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.digitalracer.store"
FIELDS = ["id","category","title","price_usd","image_url","product_url",
          "caption","publication_status","stock_verification","media_review"]
TAGS = {
 "Account":"#PUBGMobile #PUBGAccount #DigitalRacer",
 "Car Card":"#PUBGMobile #PUBGCarSkins #DigitalRacer",
 "UC Top-Up":"#PUBGMobile #PUBGUC #DigitalRacer",
 "In-Game Items":"#PUBGMobile #PUBGItems #DigitalRacer",
 "Popularity":"#PUBGMobile #PUBGPopularity #DigitalRacer",
 "Rank Boosting":"#PUBGMobile #PUBGRank #DigitalRacer"
}

def build(items,pages):
    if len(items) != len(pages):
        raise ValueError("Inventory count differs from URL index")
    seen=set()
    result=[]
    for item,page in zip(items,pages):
        if item["title"]!=page["title"] or str(item["price"])!=str(page["price"]):
            raise ValueError("Inventory and product URL index do not match")
        url=urljoin(BASE,page["url"])
        if url in seen:
            raise ValueError("Duplicate URL: "+url)
        seen.add(url)
        title=" ".join(item["title"].split())
        price=float(item["price"])
        cat=item["category"]
        caption=(title[:180]+("..." if len(title)>180 else "")+
          "\n\nListed price: $"+format(price,".2f")+
          " USD (subject to confirmation).\n\nFull details: digitalracer.store (link in bio). "
          "Please confirm stock, region, and delivery before ordering.\n\n"+
          TAGS.get(cat,"#PUBGMobile #DigitalRacer"))
        result.append(dict(
          id=page["url"].strip("/").split("/")[-1],
          category=cat,title=title,price_usd=format(price,".2f"),
          image_url=urljoin(BASE,item["thumbnail"]),
          product_url=url,caption=caption,publication_status="DRAFT_NOT_PUBLISHED",
          stock_verification="UNVERIFIED",media_review="REVIEW_REQUIRED"))
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,default=ROOT/"social/instagram/generated")
    args=ap.parse_args()
    items=json.loads((ROOT/"inventory.json").read_text(encoding="utf-8"))["items"]
    pages=json.loads((ROOT/"p/index.json").read_text(encoding="utf-8"))
    drafts=build(items,pages)
    args.output.mkdir(parents=True,exist_ok=True)
    for old in args.output.glob("catalog-draft-*.csv"):
        old.unlink()
    for start in range(0,len(drafts),65):
        path=args.output/("catalog-draft-"+str(start//65+1).zfill(2)+".csv")
        with path.open("w",encoding="utf-8-sig",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(drafts[start:start+65])
    (args.output/"manifest.json").write_text(json.dumps({
      "source":"inventory.json + p/index.json","drafts":len(drafts),
      "published":0,"stock_unverified":True,"media_review_required":True
    },indent=2),encoding="utf-8")
    print("Generated",len(drafts),"unpublished Instagram drafts")

if __name__=="__main__":
    main()
