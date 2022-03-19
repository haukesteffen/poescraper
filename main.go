package main

import (
	"fmt"
	"os"
	"time"

	"github.com/go-resty/resty/v2"
	"github.com/haukesteffen/poescraper/api"
)

/*
{"verified":false,"w":1,"h":1,"icon":"https:\/\/web.poecdn.com\/gen\/image\/WzI1LDE0LHsiZiI6IjJESXRlbXMvUmluZ3MvVGh1bmRlckxvb3AiLCJ3IjoxLCJoIjoxLCJzY2FsZSI6MX1d\/1322cee671\/ThunderLoop.png","league":"Archnemesis",
"id":"376f84ae8f7d47805e9e0bbb71ce8d94f25a032d67e2a0981d7f65a9882aecb8","name":"Storm Secret","typeLine":"Topaz Ring","baseType":"Topaz Ring","identified":true,"ilvl":76,"note":"~price 7 chaos","corrupted":true,
"properties":[{"name":"Quality (Attribute Modifiers)","values":[["+20%",1]],"displayMode":0,"type":6}],"requirements":[{"name":"Level","values":[["56",0]],"displayMode":0}],"implicitMods":["+30% to Lightning Resistance"],
"explicitMods":["+27 to Intelligence","20% increased Lightning Damage","14% chance to Shock","Herald of Thunder also creates a storm when you Shock an Enemy","Herald of Thunder's Storms Hit Enemies with 37% increased Frequency",
"Take 250 Lightning Damage when Herald of Thunder Hits an Enemy"],
"flavourText":["Lightning lives in an endless circle."],"frameType":3,
"extended":{"category":"accessories","subcategories":["ring"]},"x":12,"y":7,"inventoryId":"Stash4"},

frameType:
	0 normal
	1 magic
	2 rare
	3 unique
	4 gem

print struct with keys:
	fmt.Printf("%+v\n", item)
*/

type Tmp struct {
	NextChangeID string `json:"next_change_id"`
}

var rarity = map[int]string{
	0: "Normal",
	1: "Magic",
	2: "Rare",
}

var url = "https://www.pathofexile.com/api/public-stash-tabs?id="

func main() {
	var change_id string
	var size float64
	snooze := 0.5
	totalSize := 0.0
	if len(os.Args) > 1 {
		change_id = os.Args[1]
	} else {
		change_id = "1472339778-1475818681-1427199351-1588249104-1534088717"
	}
	if os.Getenv("POEEMAIL") == "" {
		fmt.Println("No Email (env: POEEMAIL) set.")
		os.Exit(1)
	}
	client := resty.New()
	for {
		change_id, size = fetchapi(client, change_id)
		totalSize += size
		//fmt.Printf("Total download size start: %.2f MB\n", totalSize)
		time.Sleep(time.Duration(snooze) * time.Second)
	}
	//fmt.Println("Response Info:")
	//fmt.Println("  Error      :", err)
	//fmt.Println("  Status Code:", resp.StatusCode())
	//fmt.Println("  Status     :", resp.Status())
	//fmt.Println("  Proto      :", resp.Proto())
	//fmt.Println("  Time       :", resp.Time())
	//fmt.Println("  Received At:", resp.ReceivedAt())
	//fmt.Println("  Body       :\n", resp)
	//fmt.Println()

}

func fetchapi(client *resty.Client, change_id string) (string, float64) {
	var dump api.Poe
	//var dump Tmp
	resp, err := client.R().
		SetResult(&dump).
		SetHeader("User-Agent", fmt.Sprintf("OAuth poescraper/0.1 (contact: %s) StrictMode", os.Getenv("POEEMAIL"))).
		Get(url + change_id)
	if err != nil {
		panic(err)
	}
	if resp.StatusCode() == 200 {
		//fmt.Println("Time:", resp.Time())
		//fmt.Println("Next change ID:", dump.NextChangeID)
		go stashParser(dump)
		return dump.NextChangeID, float64(resp.Size()) / (1 << 20)
	} else if resp.StatusCode() == 429 {
		fmt.Println("Too many requests. Sleeping 60s")
		fmt.Println(resp.StatusCode())
		fmt.Println(resp)

		os.Exit(1)

		time.Sleep(time.Duration(60) * time.Second)
		return change_id, 0
	} else {
		fmt.Println("Other Error")
		fmt.Println(resp.StatusCode())
		fmt.Println(resp)

		os.Exit(1)

		return change_id, 0
	}
}

func stashParser(stashes api.Poe) {
	var subcat []string
	for _, v := range stashes.Stashes {
		if v.League == "Hardcore Archnemesis" {
			for _, item := range v.Items {
				// look at normal, magic and rare items
				if item.FrameType > 0 && item.FrameType < 3 && item.Identified && item.Note != "" {
					subcat = item.Extended.Subcategories
					if len(subcat) > 0 && subcat[0] == "ring" {
						//fmt.Printf("%+v", item)
						fmt.Printf("%v\nRarity: %v\niLvl: %v\n", item.BaseType, rarity[item.FrameType], item.Ilvl)
						for _, aff := range item.ExplicitMods {
							fmt.Println(aff)
						}
						fmt.Printf("Price: %v\n", item.Note)
						fmt.Println()
					}
				}
			}
		}
	}
}
