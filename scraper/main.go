package main

import (
	"bufio"
	"database/sql"
	"fmt"
	"os"
	"strconv"
	"time"

	_ "github.com/doug-martin/goqu/v9/dialect/postgres"
	"github.com/go-resty/resty/v2"
	"github.com/lib/pq"
)

var GitCommit string = "undefined"
var BuildTime string = "No Time provided"

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

func dumpHeaders(resp *resty.Response) {
	fmt.Println("---------------")
	for name, values := range resp.Header() {
		for _, value := range values {
			fmt.Println(name, value)
		}
	}
	fmt.Println("---------------")
}

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

func stashToDB(singlestash PoeStash) {
	insertDynStmt := `INSERT INTO "stash"("stashid","accountname","stash","league") values($1, $2, $3, $4)`
	rows, err := db.Query(insertDynStmt, singlestash.ID, singlestash.AccountName, singlestash.Stash, singlestash.League)
	if err != nil {
		panic(err)
	}
	rows.Close()
	stashParser(singlestash)
}

func itemToDB(item PoeItem, instashid string) {
	insertDynStmt := `INSERT INTO "items"("instashid", "itemid", "itemclass", "basetype", "rarity", "ilvl", "implicitmods", "explicitmods", "fracturedmods",
		"corrupted", "price") values($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`
	rows, err := db.Query(insertDynStmt, instashid, item.ID, item.Extended.Subcategories[0], item.BaseType, item.FrameType, item.Ilvl, pq.Array(item.ImplicitMods),
		pq.Array(item.ExplicitMods), pq.Array(item.FracturedMods), item.Corrupted, item.Note)

	if err != nil {
		panic(err)
	}
	rows.Close()
}

func fetchapi(client *resty.Client, change_id string) (string, float64) {
	var dump Poe
	//var dump Tmp
	resp, err := client.R().
		SetResult(&dump).
		SetHeader("User-Agent", fmt.Sprintf("OAuth poescraper/0.1 (contact: %s) StrictMode", os.Getenv("POEEMAIL"))).
		Get(url + change_id)
	if err != nil {
		panic(err)
	}
	respCode := resp.StatusCode()
	if respCode == 200 {
		//go stashParser(dump)
		stashGetter(dump)
		return dump.NextChangeID, float64(resp.Size()) / (1 << 20)
	} else if respCode == 429 {
		fmt.Println("Status Code:", respCode, "at", resp.ReceivedAt())
		dumpHeaders(resp)
		fmt.Println(resp)
		header := resp.Header().Get("Retry-After")
		waiting_seconds, err := strconv.Atoi(header)
		if err != nil {
			fmt.Println("Couldn't cast to int:", header)
			fmt.Println("Sleeping 60s")
			waiting_seconds = 60
		}
		time.Sleep(time.Duration(waiting_seconds) * time.Second)
		return change_id, 0
	} else {
		fmt.Println("Other Error. Sleeping 60s")
		fmt.Println(resp.StatusCode(), "at", resp.ReceivedAt())
		fmt.Println(resp)
		time.Sleep(time.Duration(60) * time.Second)
		return change_id, 0
	}
}

func stashGetter(apiresp Poe) {
	for _, v := range apiresp.Stashes {
		lg := v.League
		if v.Public && lg != "Sentinel" && lg != "Standard" && lg != "Hardcore" {
			stashToDB(v)
		}
	}
}

func stashParser(stash PoeStash) {
	var subcat []string
	if stash.League == "Hardcore Sentinel" {
		for _, item := range stash.Items {
			// look at normal, magic and rare items
			if item.FrameType > 0 && item.FrameType < 3 && item.Identified {
				subcat = item.Extended.Subcategories
				if len(subcat) > 0 {
					if todb {
						itemToDB(item, stash.ID)
					} else {
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
	metadata_folder := "/data/"
	last_change_id_file := metadata_folder + "last_change_id"
	snooze := 0.5
	totalSize := 0.0
	fmt.Println(GitCommit, BuildTime)
	// todo
	if os.Getenv("TODB") != "" {
		todb = false
	}
	file, err = os.OpenFile(last_change_id_file, os.O_RDWR|os.O_CREATE, 0600)
	if err != nil {
		fmt.Println(last_change_id_file, "nicht gefunden und/oder konnte nicht erstellt werden.")
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
	// todo better checks
	if os.Getenv("DBHOST") != "" && todb {
		initDB()
	}
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
			fmt.Println("Could not write to file ", last_change_id_file)
			//panic(err)
		}
		file.Sync()
		//fmt.Printf("Total download size start: %.2f MB\n", totalSize)
		time.Sleep(time.Duration(snooze) * time.Second)
	}
}
