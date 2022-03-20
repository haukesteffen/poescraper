package main

import (
	"bufio"
	"database/sql"
	"fmt"
	"os"
	"time"

	"github.com/go-resty/resty/v2"
	"github.com/haukesteffen/poescraper/api"
	"github.com/lib/pq"
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
 id            | integer
 basetype      | text
 rarity        | smallint
 ilvl          | smallint
 implicit      | text[]
 explicit      | text[]
 corrupted     | boolean
 fracturedmods | text[]
 price         | text
 itemid	       | text
*/

type Tmp struct {
	NextChangeID string `json:"next_change_id"`
}

var rarity = map[int]string{
	0: "Normal",
	1: "Magic",
	2: "Rare",
}

var db *sql.DB

// todo
var todb bool = true

var url = "https://www.pathofexile.com/api/public-stash-tabs?id="

func initDB() {
	var err error
	connStr := fmt.Sprintf("host=%s port=%s user=%s "+
		"password=%s dbname=%s sslmode=disable",
		os.Getenv("DBHOST"), os.Getenv("DBPORT"), os.Getenv("DBUSER"), os.Getenv("DBPASSWORD"), os.Getenv("DBDBNAME"))
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		panic(err)
	}
}

func itemToDB(item api.PoeItem) {
	insertDynStmt := `INSERT INTO "items"("basetype", "rarity", "ilvl", "implicit", "explicit", "corrupted", "fracturedmods", "price", "itemid") values($1, $2, $3, $4, $5, $6, $7, $8, $9)`
	_, err := db.Exec(insertDynStmt, item.BaseType, item.FrameType, item.Ilvl, pq.Array(item.ImplicitMods), pq.Array(item.ExplicitMods), item.Corrupted, pq.Array(item.FracturedMods), item.Note, item.ID)
	if err != nil {
		panic(err)
	}
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
				if item.FrameType > 0 && item.FrameType < 3 && item.Identified {
					subcat = item.Extended.Subcategories
					if len(subcat) > 0 && subcat[0] == "ring" {
						if todb {
							go itemToDB(item)
						}
						//fmt.Printf("%+v", item)
						fmt.Printf("%v\nRarity: %v\niLvl: %v\n", item.BaseType, rarity[item.FrameType], item.Ilvl)
						for _, imp := range item.ImplicitMods {
							fmt.Println(imp)
						}
						fmt.Println("-----------------")
						for _, aff := range item.ExplicitMods {
							fmt.Println(aff)
						}
						fmt.Println("-----------------")
						fmt.Printf("Price: %v\n", item.Note)
						fmt.Println()
					}
				}
			}
		}
	}
}

func main() {
	var file *os.File
	var change_id string
	var size float64
	var err error
	last_change_id_file := "/data/last_change_id"
	snooze := 0.5
	totalSize := 0.0
	// todo
	if os.Getenv("TODB") != "" {
		todb = false
	}

	file, err = os.OpenFile(last_change_id_file, os.O_RDWR|os.O_CREATE, 0755)
	if err != nil {
		panic(err)
	}
	scanner := bufio.NewScanner(file)
	scanner.Scan()
	change_id = scanner.Text()
	if err = scanner.Err(); err != nil {
		panic(err)
	}
	if change_id == "" {
		change_id = "1474588903-1478046118-1429398778-1590571140-1536383722"
	}
	if len(os.Args) > 1 {
		change_id = os.Args[1]
	}
	if os.Getenv("POEEMAIL") == "" {
		fmt.Println("No Email (env: POEEMAIL) set.")
		os.Exit(1)
	}
	if os.Getenv("DBHOST") == "" {
		fmt.Println("No DB vars")
		os.Exit(1)
	}
	initDB()
	client := resty.New()
	fmt.Println("Starting at", change_id)
	if !todb {
		fmt.Println("Not writing to db")
	}
	for {
		change_id, size = fetchapi(client, change_id)
		totalSize += size
		_, err := file.WriteAt([]byte(change_id), 0)
		if err != nil {
			panic(err)
		}
		file.Sync()
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
