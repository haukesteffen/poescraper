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

var trackedAccounts = []string{
	"kjfdgkjldkjfkjlkf",
}

var db *sql.DB

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

func initDB(c *Config) {
	var err error
	connStr := fmt.Sprintf("host=%s port=%s user=%s "+
		"password=%s dbname=%s sslmode=disable",
		c.dbHost, c.dbPort, c.dbUser, c.dbPass, c.dbName)
	db, err = sql.Open("postgres", connStr)
	if err != nil {
		panic(err)
	}
}

func stashToDB(singlestash PoeStash) {
	var id int
	insertDynStmt := `INSERT INTO "stash"("stashid","accountname","stash","league") values($1, $2, $3, $4) RETURNING id`
	row := db.QueryRow(insertDynStmt, singlestash.ID, singlestash.AccountName, singlestash.Stash, singlestash.League)
	if err := row.Scan(&id); err != nil {
		panic(err)
	}
	singleStashTraverser(singlestash, id)
}

func itemToDB(item PoeItem, instashid string, insertid int) {
	insertDynStmt := `INSERT INTO "items"("instashid", "itemid", "itemclass", "basetype", "rarity", "ilvl", "implicitmods", "explicitmods", "fracturedmods",
		"corrupted", "price", "stash_id") values($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)`
	rows, err := db.Query(insertDynStmt, instashid, item.ID, item.Extended.Subcategories[0], item.BaseType, item.FrameType, item.Ilvl, pq.Array(item.ImplicitMods),
		pq.Array(item.ExplicitMods), pq.Array(item.FracturedMods), item.Corrupted, item.Note, insertid)
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

func accountIsTracked(lookup string) bool {
	for _, val := range trackedAccounts {
		if val == lookup {
			return true
		}
	}
	return false
}

func stashFilter(stash *PoeStash) bool {
	if stash.League == "Hardcore Sentinel" || accountIsTracked(stash.AccountName) {
		return true
	}
	return false
}

func itemFilter(item *PoeItem, fromStash *PoeStash) bool {
	var subcat []string
	// look at normal, magic and rare items
	if item.FrameType > 0 && item.FrameType < 3 && item.Identified {
		subcat = item.Extended.Subcategories
		if len(subcat) > 0 {
			return true
		}
	}
	return false
}

func singleStashTraverser(stash PoeStash, insertid int) {
	if stashFilter(&stash) {
		for _, item := range stash.Items {
			if itemFilter(&item, &stash) {
				if todb {
					itemToDB(item, stash.ID, insertid)
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

type Config struct {
	poeEmail  string
	dbHost    string
	dbPort    string
	dbName    string
	dbUser    string
	dbPass    string
	change_id string
}

func newConfig() *Config {
	c := &Config{}
	poeemail, poeemailOk := os.LookupEnv("POEEMAIL")
	if !poeemailOk {
		fmt.Fprintln(os.Stderr, "Set Email (POEEMAIL)")
		os.Exit(1)
	}
	c.poeEmail = poeemail
	change_id, change_idOk := os.LookupEnv("CHANGEID")
	if change_idOk {
		c.change_id = change_id
	} else {
		c.change_id = ""
	}
	if todb {
		dbhost, dbhostOk := os.LookupEnv("DBHOST")
		if !dbhostOk {
			fmt.Fprintln(os.Stderr, "Set database host (DBHOST)")
			os.Exit(1)
		}
		c.dbHost = dbhost
		dbport, dbportOk := os.LookupEnv("DBPORT")
		if !dbportOk {
			fmt.Fprintln(os.Stderr, "Set database port (DBPORT)")
			os.Exit(1)
		}
		c.dbPort = dbport
		dbname, dbnameOk := os.LookupEnv("DBDBNAME")
		if !dbnameOk {
			fmt.Fprintln(os.Stderr, "Set database name (DBDBNAME)")
			os.Exit(1)
		}
		c.dbName = dbname
		dbuser, dbuserOk := os.LookupEnv("DBUSER")
		if !dbuserOk {
			fmt.Fprintln(os.Stderr, "Set database user (DBUSER)")
			os.Exit(1)
		}
		c.dbUser = dbuser
		dbpass, dbpassOk := os.LookupEnv("DBPASSWORD")
		if !dbpassOk {
			fmt.Fprintln(os.Stderr, "Set database password (DBPASS)")
			os.Exit(1)
		}
		c.dbPass = dbpass
	}
	fmt.Println("Env OK")
	return c
}

func main() {
	var file *os.File
	var change_id string
	var size float64
	var err error
	metadata_folder := "/data/"
	last_change_id_file := metadata_folder + "last_change_id"
	snooze := 2
	totalSize := 0.0
	fmt.Println(GitCommit, BuildTime)
	if os.Getenv("TODB") != "" {
		todb = false
		fmt.Println("Not writing to db")
	}
	c := newConfig()
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
	// use default if no change_id found in file...
	if change_id == "" {
		change_id = "1539440501-1543581122-1492205064-1658298895-1603627767"
	}
	// ... but always use given change_id, if it was set via env variable (CHANGEID)
	if c.change_id != "" {
		change_id = c.change_id
	}
	if todb {
		initDB(c)
	}
	client := resty.New()
	fmt.Println("Starting at", change_id)
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
