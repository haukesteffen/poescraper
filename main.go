package main

import (
	"fmt"
	"os"
	"time"

	"github.com/go-resty/resty/v2"
	//	"github.com/haukesteffen/poescraper/api"
)

type Tmp struct {
	NextChangeID string `json:"next_change_id"`
}

var url = "https://www.pathofexile.com/api/public-stash-tabs?id="

func main() {
	var change_id string
	if len(os.Args) > 1 {
		change_id = os.Args[1]
	} else {
		change_id = "1472289994-1475770471-1427149043-1588198401-1534034954"
	}
	if os.Getenv("POEEMAIL") == "" {
		fmt.Println("No Email (env: POEEMAIL) set.")
		os.Exit(1)
	}
	client := resty.New()
	for {
		change_id = fetchapi(client, change_id)
		time.Sleep(time.Duration(5) * time.Second)
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

func fetchapi(client *resty.Client, change_id string) string {
	//var dump api.Poe
	var dump Tmp
	resp, err := client.R().
		SetResult(&dump).
		SetHeader("User-Agent", fmt.Sprintf("OAuth poescraper/0.1 (contact: %s) StrictMode", os.Getenv("POEEMAIL"))).
		Get(url + change_id)
	if err != nil {
		panic(err)
	}
	if resp.StatusCode() == 200 {
		//fmt.Println("Time:", resp.Time())
		fmt.Println("Next change ID:", dump.NextChangeID)
		return dump.NextChangeID
	} else if resp.StatusCode() == 429 {
		fmt.Println("Too many requests. Sleeping 60s")
		time.Sleep(time.Duration(60) * time.Second)
		return change_id
	} else {
		fmt.Println("Other Error")
		fmt.Println(resp.StatusCode())
		fmt.Println(resp)
		return change_id
	}
}
