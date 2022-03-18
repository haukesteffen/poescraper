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
		fmt.Printf("Total download size start: %.2f MB\n", totalSize)
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
